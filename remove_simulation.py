#!/usr/bin/env python3
"""
Remove a simulation from pendulum.star by index number.

Usage: python3 remove_simulation.py <simulation_number>
Example: python3 remove_simulation.py 26
"""

import re
import json
import sys

if len(sys.argv) != 2:
    print("Usage: python3 remove_simulation.py <simulation_number>")
    print("Example: python3 remove_simulation.py 26")
    sys.exit(1)

try:
    sim_number = int(sys.argv[1])
except ValueError:
    print(f"Error: '{sys.argv[1]}' is not a valid number")
    sys.exit(1)

# Read the file
with open('pendulum.star', 'r') as f:
    content = f.read()

# Find ALL_SIMULATIONS
match = re.search(r'ALL_SIMULATIONS = (\[\[.*?\]\])\s*\n', content, re.DOTALL)
if not match:
    print("Error: Could not find ALL_SIMULATIONS in pendulum.star")
    sys.exit(1)

array_text = match.group(1)
simulations = json.loads(array_text)

print(f"Current number of simulations: {len(simulations)}")

# Remove simulation by number (convert to 0-based index)
sim_index = sim_number - 1

if sim_index < 0 or sim_index >= len(simulations):
    print(f"Error: Simulation #{sim_number} does not exist (valid range: 1-{len(simulations)})")
    sys.exit(1)

del simulations[sim_index]
print(f"Removed simulation #{sim_number}")
print(f"New number of simulations: {len(simulations)}")

# Convert back to string
new_array_text = json.dumps(simulations)

# Replace in content
new_content = content.replace(match.group(1), new_array_text)

# Write back
with open('pendulum.star', 'w') as f:
    f.write(new_content)

print("Successfully updated pendulum.star")
