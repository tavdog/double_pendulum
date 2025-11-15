#!/usr/bin/env python3
"""Test script for the double pendulum API."""

import json
import os
import sys
import subprocess

def test_random_mode():
    """Test API with random mode."""
    print("Testing random mode...")
    env = os.environ.copy()
    env['QUERY_STRING'] = 'mode=random&duration=3&step_size=0.1&seed=42'
    env['REQUEST_METHOD'] = 'GET'

    result = subprocess.run(
        ['python3', 'api.py'],
        env=env,
        capture_output=True,
        text=True
    )

    print("Status:", result.returncode)
    output_lines = result.stdout.split('\n')
    # Skip headers, find JSON
    json_start = None
    for i, line in enumerate(output_lines):
        if line.strip() == '':
            json_start = i + 1
            break

    if json_start:
        json_output = '\n'.join(output_lines[json_start:])
        data = json.loads(json_output)
        print(f"  Mode: {data['simulation']['type']}")
        print(f"  Points: {data['parameters']['num_points']}")
        print(f"  First point: x1={data['trajectory'][0]['x1']}, y1={data['trajectory'][0]['y1']}")
        print("  ✓ Random mode test passed\n")
        return data
    else:
        print("  ✗ Failed to parse response")
        print(result.stdout)
        return None


def test_custom_mode():
    """Test API with custom mode."""
    print("Testing custom mode...")
    json_data = {
        "mode": "custom",
        "pendulum1": {"m": 5, "x": 1.5, "y": -2, "u": 0, "v": 0},
        "pendulum2": {"m": 3, "x": 3.0, "y": -4, "u": 0, "v": 0},
        "duration": 3,
        "step_size": 0.1,
        "method": "RK4"
    }
    json_str = json.dumps(json_data)

    env = os.environ.copy()
    env['REQUEST_METHOD'] = 'POST'
    env['CONTENT_LENGTH'] = str(len(json_str))

    result = subprocess.run(
        ['python3', 'api.py'],
        input=json_str,
        env=env,
        capture_output=True,
        text=True
    )

    print("Status:", result.returncode)
    output_lines = result.stdout.split('\n')
    # Skip headers, find JSON
    json_start = None
    for i, line in enumerate(output_lines):
        if line.strip() == '':
            json_start = i + 1
            break

    if json_start:
        json_output = '\n'.join(output_lines[json_start:])
        data = json.loads(json_output)
        print(f"  Mode: {data['simulation']['type']}")
        print(f"  Points: {data['parameters']['num_points']}")
        print(f"  First point: x1={data['trajectory'][0]['x1']}, y1={data['trajectory'][0]['y1']}")
        print(f"  Pendulum 1 mass: {data['simulation']['pendulum1']['m']}")
        print("  ✓ Custom mode test passed\n")
        return data
    else:
        print("  ✗ Failed to parse response")
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return None


if __name__ == '__main__':
    print("=" * 60)
    print("Double Pendulum API Tests")
    print("=" * 60 + "\n")

    test_random_mode()
    test_custom_mode()

    print("All tests completed!")
