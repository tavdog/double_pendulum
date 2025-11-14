import csv
from simulation import create_random_example, simulate

# Create and simulate the double pendulum
# 15 seconds duration, 30 Hz sampling rate (1/30 = 0.0333... second step size)
rand_ex = create_random_example()
results = simulate(rand_ex, duration=15, step_size=1/30)

# Output coordinates to CSV
output_file = 'pendulum_coordinates.csv'
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Write header
    writer.writerow(['time', 'x1', 'y1', 'x2', 'y2'])

    # Write coordinate data
    # results.ys contains [x1, x2, y1, y2] for each time step
    for i, coords in enumerate(results.ys):
        time = i * results.h  # Calculate time from step index and step size
        x1, x2, y1, y2 = coords[0], coords[1], coords[2], coords[3]
        writer.writerow([time, x1, y1, x2, y2])

print(f"Wrote {len(results.ys)} coordinate pairs to {output_file}")
print(f"Time range: 0 to {(len(results.ys)-1) * results.h:.2f} seconds")
print(f"Step size: {results.h}")
