#!/home/taviz/wildc.net/dp/.venv/bin/python3
"""Simple CGI API for generating double pendulum simulation datasets.

Usage examples:
    # Random simulation
    ./api.py?mode=random&duration=30&step_size=0.001

    # Custom initial conditions
    ./api.py (with POST JSON body)

POST JSON format:
    {
        "mode": "custom",
        "pendulum1": {"m": 5, "x": 1.5, "y": -2, "u": 0, "v": 0},
        "pendulum2": {"m": 3, "x": 3.0, "y": -4, "u": 0, "v": 0},
        "duration": 30,
        "step_size": 0.001,
        "method": "RK4"
    }
"""

import json
import sys
import random
from urllib.parse import parse_qs
import os

from pendulum import Pendulum, DoublePendulum
from simulation import create_random_example, create_random_example_with_lengths, simulate
from methods import RK4, Euler, ExplicitMidpoint, DOPRI5

# Map of method names to method objects
METHODS = {
    'RK4': RK4,
    'Euler': Euler,
    'ExplicitMidpoint': ExplicitMidpoint,
    'DOPRI5': DOPRI5
}


def parse_request():
    """Parse CGI request parameters from GET query string or POST JSON body.

    Returns:
        dict: Request parameters
    """
    request_method = os.environ.get('REQUEST_METHOD', 'GET')

    if request_method == 'POST':
        # Parse JSON from POST body
        content_length = int(os.environ.get('CONTENT_LENGTH', 0))
        if content_length > 0:
            post_data = sys.stdin.read(content_length)
            return json.loads(post_data)
        return {}
    else:
        # Parse query string parameters
        query_string = os.environ.get('QUERY_STRING', '')
        params = parse_qs(query_string)
        # Convert single-item lists to values
        return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def generate_simulation(params):
    """Generate double pendulum simulation based on parameters.

    Args:
        params (dict): Request parameters

    Returns:
        dict: Simulation results with metadata
    """
    # Extract parameters with defaults
    mode = params.get('mode', 'random')
    duration = float(params.get('duration', 30))
    step_size = float(params.get('step_size', 0.001))
    method_name = params.get('method', 'RK4')
    seed = params.get('seed')

    # Length constraints (adjusted for better visual results)
    length1_min = float(params.get('length1_min', 4.5))
    length1_max = float(params.get('length1_max', 6.0))
    length2_min = float(params.get('length2_min', 3.5))
    length2_max = float(params.get('length2_max', 7.2))

    # Set random seed if provided
    if seed is not None:
        random.seed(int(seed))

    # Get numerical method
    method = METHODS.get(method_name, RK4)

    # Create double pendulum example
    if mode == 'random':
        # Use length-based random generation for better control
        example = create_random_example_with_lengths(
            length1_min=length1_min,
            length1_max=length1_max,
            length2_min=length2_min,
            length2_max=length2_max
        )
        mode_info = {
            'type': 'random',
            'pendulum1': {
                'm': float(example._b1.m),
                'x': float(example._b1.x),
                'y': float(example._b1.y),
                'u': float(example._b1.u),
                'v': float(example._b1.v)
            },
            'pendulum2': {
                'm': float(example._b2.m),
                'x': float(example._b2.x),
                'y': float(example._b2.y),
                'u': float(example._b2.u),
                'v': float(example._b2.v)
            }
        }
    else:  # custom mode
        p1_data = params.get('pendulum1', {})
        p2_data = params.get('pendulum2', {})

        p1 = Pendulum(
            m=float(p1_data.get('m', 5)),
            x=float(p1_data.get('x', 1.5)),
            y=float(p1_data.get('y', -2)),
            u=float(p1_data.get('u', 0)),
            v=float(p1_data.get('v', 0))
        )
        p2 = Pendulum(
            m=float(p2_data.get('m', 3)),
            x=float(p2_data.get('x', 3.0)),
            y=float(p2_data.get('y', -4)),
            u=float(p2_data.get('u', 0)),
            v=float(p2_data.get('v', 0))
        )

        example = DoublePendulum(p1, p2)
        mode_info = {
            'type': 'custom',
            'pendulum1': p1_data,
            'pendulum2': p2_data
        }

    # Run simulation
    result = simulate(example, method=method, duration=duration, step_size=step_size)

    # Extract trajectory data
    # ys contains [x1, x2, y1, y2, u1, u2, v1, v2] for each timestep
    # By default, return just position coordinates [x1, y1, x2, y2]
    full_data = params.get('full', 'false').lower() == 'true'

    trajectory = []
    for i, y in enumerate(result.ys):
        if full_data:
            # Full data with time and velocities
            trajectory.append({
                'time': float(i * step_size),
                'x1': float(y[0]),
                'x2': float(y[1]),
                'y1': float(y[2]),
                'y2': float(y[3]),
                'u1': float(y[4]),
                'u2': float(y[5]),
                'v1': float(y[6]),
                'v2': float(y[7])
            })
        else:
            # Just position coordinates like in starlark file
            trajectory.append([
                float(y[0]),  # x1
                float(y[2]),  # y1
                float(y[1]),  # x2
                float(y[3])   # y2
            ])

    return {
        'simulation': mode_info,
        'parameters': {
            'duration': duration,
            'step_size': step_size,
            'method': method_name,
            'num_points': len(trajectory)
        },
        'trajectory': trajectory
    }


def main():
    """Main CGI handler."""
    try:
        # Parse request
        params = parse_request()

        # Generate simulation
        result = generate_simulation(params)

        # Output JSON response
        print("Content-Type: application/json")
        print("Access-Control-Allow-Origin: *")  # Enable CORS
        print()
        print(json.dumps(result, indent=2))

    except Exception as e:
        # Error response
        print("Content-Type: application/json")
        print("Status: 400 Bad Request")
        print()
        print(json.dumps({
            'error': str(e),
            'type': type(e).__name__
        }, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
