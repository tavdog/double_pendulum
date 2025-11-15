# Double Pendulum API

A simple CGI-based API for generating double pendulum simulation datasets.

## Files

- `api.py` - Main API script
- `test_api.py` - Test script demonstrating usage

## Usage

### Random Mode (GET Request)

Generate a random double pendulum simulation:

```bash
QUERY_STRING="mode=random&duration=30&step_size=0.001&seed=42" \
REQUEST_METHOD="GET" \
python3 api.py
```

#### Query Parameters

- `mode=random` - Generate random initial conditions
- `duration` - Simulation duration in seconds (default: 30)
- `step_size` - Time step size (default: 0.001)
- `seed` - Random seed for reproducibility (optional)
- `method` - Numerical method: RK4, Euler, ExplicitMidpoint, DOPRI5 (default: RK4)

### Custom Mode (POST Request)

Specify custom initial conditions via JSON POST body:

```bash
echo '{
  "mode": "custom",
  "pendulum1": {"m": 5, "x": 1.5, "y": -2, "u": 0, "v": 0},
  "pendulum2": {"m": 3, "x": 3.0, "y": -4, "u": 0, "v": 0},
  "duration": 30,
  "step_size": 0.001,
  "method": "RK4"
}' | python3 api.py
```

#### Pendulum Parameters

Each pendulum has:
- `m` - Mass
- `x`, `y` - Initial position coordinates
- `u`, `v` - Initial velocities (usually 0 for stable start)

## Response Format

The API returns JSON with the following structure:

```json
{
  "simulation": {
    "type": "random" or "custom",
    "pendulum1": {
      "m": 5.0,
      "x": 1.5,
      "y": -2.0,
      "u": 0.0,
      "v": 0.0
    },
    "pendulum2": { ... }
  },
  "parameters": {
    "duration": 30.0,
    "step_size": 0.001,
    "method": "RK4",
    "num_points": 30001
  },
  "trajectory": [
    {
      "time": 0.0,
      "x1": 1.5,
      "x2": 3.0,
      "y1": -2.0,
      "y2": -4.0,
      "u1": 0.0,
      "u2": 0.0,
      "v1": 0.0,
      "v2": 0.0
    },
    ...
  ]
}
```

### Trajectory Data

Each point in the trajectory contains:
- `time` - Time in seconds
- `x1`, `y1` - Position of first pendulum bob
- `x2`, `y2` - Position of second pendulum bob
- `u1`, `v1` - Velocity of first pendulum bob
- `u2`, `v2` - Velocity of second pendulum bob

## Testing

Run the test script to verify the API works correctly:

```bash
python3 test_api.py
```

## Setting up as a CGI Script

To use as an actual web CGI script:

1. Place `api.py` in your web server's CGI directory (e.g., `/usr/lib/cgi-bin/`)
2. Ensure it's executable: `chmod +x api.py`
3. Update the shebang line if needed to point to your Python installation
4. Configure your web server to execute CGI scripts

Then access via HTTP:
- Random: `http://yourserver/cgi-bin/api.py?mode=random&duration=30`
- Custom: POST JSON to `http://yourserver/cgi-bin/api.py`

## Available Numerical Methods

- `RK4` - 4th order Runge-Kutta (recommended, default)
- `DOPRI5` - Dormand-Prince method (adaptive step size)
- `ExplicitMidpoint` - 2nd order method
- `Euler` - Simple Euler method (less accurate, for testing)
