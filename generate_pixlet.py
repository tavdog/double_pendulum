import json
import random
import math
from simulation import simulate
from pendulum import Pendulum, DoublePendulum

# Random arm lengths
LENGTH_1_MIN = 4.0
LENGTH_1_MAX = 6.0  # 50% longer than minimum

# Generate 50 different random pendulum simulations
print("Generating 50 random pendulum simulations...")
all_simulations = []
for i in range(50):
    print(f"  Simulation {i+1}/50...")

    # Retry until we get a stable simulation
    max_retries = 100
    for retry in range(max_retries):
        try:
            # Generate random arm lengths, angles and masses
            LENGTH_1 = round(random.uniform(LENGTH_1_MIN, LENGTH_1_MAX), 2)  # Random first arm length
            LENGTH_2 = round(random.uniform(2.0, 7.2), 2)  # Random second arm length
            theta1 = random.uniform(-math.pi, math.pi)  # Random angle for first pendulum
            theta2 = random.uniform(-math.pi, math.pi)  # Random angle for second pendulum
            m1 = round(random.uniform(1, 6), 2)
            m2 = round(random.uniform(1, 6), 2)

            # Calculate positions from angles (starting from rest, so velocities = 0)
            x1 = LENGTH_1 * math.sin(theta1)
            y1 = -LENGTH_1 * math.cos(theta1)
            x2 = x1 + LENGTH_2 * math.sin(theta2)
            y2 = y1 - LENGTH_2 * math.cos(theta2)

            # Create pendulum with fixed lengths but random angles and masses
            p1 = Pendulum(m=m1, x=x1, y=y1, u=0, v=0)
            p2 = Pendulum(m=m2, x=x2, y=y2, u=0, v=0)
            rand_ex = DoublePendulum(p1, p2)

            results = simulate(rand_ex, duration=33.3, step_size=1/45)

            # Extract frames
            frames = []
            is_valid = True
            for coords in results.ys:
                # Check if values are reasonable (not NaN or too large)
                if any(abs(c) > 1000 or c != c for c in coords):  # c != c checks for NaN
                    is_valid = False
                    break
                frames.append({
                    'x1': coords[0],
                    'y1': coords[2],
                    'x2': coords[1],
                    'y2': coords[3]
                })

            if is_valid:
                all_simulations.append(frames)
                print(f"    Length1={LENGTH_1}, Length2={LENGTH_2}, Masses=({m1}, {m2})")
                break
            else:
                if retry < max_retries - 1:
                    print(f"    Retry {retry+1}: unstable simulation, trying again...")
                else:
                    print(f"    Failed after {max_retries} retries")

        except (FloatingPointError, ValueError) as e:
            if retry < max_retries - 1:
                print(f"    Retry {retry+1}: simulation error, trying again...")
            else:
                print(f"    Failed after {max_retries} retries")
                raise

# Calculate bounds based on maximum pendulum extent
# Maximum extent is when both arms are fully stretched in the same direction
# LENGTH_1 varies from 4.0 to 6.0, LENGTH_2 varies from 2.0 to 7.2
max_extent = LENGTH_1_MAX + 7.2  # Maximum possible extent

min_x, max_x = -max_extent, max_extent
min_y, max_y = -max_extent, max_extent

# Position origin on screen: horizontally centered and 35% down from top
origin_screen_x = 32
origin_screen_y = int(32 * 0.35)  # 35% down from top edge (11 pixels)

# Calculate scale to fit the pendulum on screen
# Available space: left=32px, right=32px, up=11px, down=21px
# We need to fit max_extent in all directions
padding = 2
scale_x = (32 - padding) / max_extent  # Horizontal scale
scale_y = (21 - padding) / max_extent  # Vertical scale (pendulum mostly swings down)

# Use the smaller scale to ensure it fits
scale = min(scale_x, scale_y)

# Transform all simulations to screen coordinates
all_screen_frames = []
for frames in all_simulations:
    screen_frames = []
    for f in frames:
        # Transform and scale coordinates relative to origin (0, 0)
        # Y is flipped (negative Y in physics = down on screen)
        sx1 = int(f['x1'] * scale + origin_screen_x)
        sy1 = int(-f['y1'] * scale + origin_screen_y)
        sx2 = int(f['x2'] * scale + origin_screen_x)
        sy2 = int(-f['y2'] * scale + origin_screen_y)

        screen_frames.append([sx1, sy1, sx2, sy2])
    all_screen_frames.append(screen_frames)

# Generate Starlark script
starlark_code = f'''load("render.star", "render")
load("encoding/base64.star", "base64")
load("time.star", "time")
load("schema.star", "schema")

# 50 different pendulum simulations
# Each has {len(all_screen_frames[0])} frames at 30 fps = {len(all_screen_frames[0])/30:.1f} seconds
ALL_SIMULATIONS = {json.dumps(all_screen_frames)}

def main(config):
    # Pick a random simulation based on current time
    now = time.now().unix
    sim_idx = now % len(ALL_SIMULATIONS)

    simulation = ALL_SIMULATIONS[sim_idx]

    # Get speed setting from config
    speed = config.get("speed", "fast")
    print("Speed mode:", speed)

    # Set delay based on speed (fast = 2ms, slow = 8ms)
    if speed == "fast":
        delay = 2  # Fast speed (~3 seconds)
    else:
        delay = 8  # Normal speed (~12 seconds)

    # Render all frames from the selected simulation
    all_frames = []
    for frame_idx in range(len(simulation)):
        all_frames.append(render_frame(sim_idx, frame_idx))

    return render.Root(
        delay = delay,
        child = render.Animation(
            children = all_frames,
        ),
    )

def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB color. H in [0,360], S and V in [0,1]"""
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    r = int((r + m) * 255)
    g = int((g + m) * 255)
    b = int((b + m) * 255)

    # Convert digits to hex chars
    def to_hex(val):
        digits = "0123456789ABCDEF"
        return digits[val // 16] + digits[val % 16]

    return "#" + to_hex(r) + to_hex(g) + to_hex(b)

def draw_line(x0, y0, x1, y1):
    """Draw a line using simple linear interpolation"""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    # If the line is just a point, return it
    if dx == 0 and dy == 0:
        if (x0 >= 0 and x0 < 64 and y0 >= 0 and y0 < 32):
            points.append((x0, y0))
        return points

    # Use simple linear interpolation for simplicity
    steps = max(dx, dy)
    for i in range(steps + 1):
        t = i / float(steps)
        x = int(x0 + t * (x1 - x0))
        y = int(y0 + t * (y1 - y0))
        if (x >= 0 and x < 64 and y >= 0 and y < 32):
            points.append((x, y))

    return points

def render_frame(sim_idx, frame_idx):
    simulation = ALL_SIMULATIONS[sim_idx]
    frame = simulation[frame_idx]
    x1, y1, x2, y2 = frame[0], frame[1], frame[2], frame[3]

    # Fixed origin (anchor point) - matches the physics origin (0,0)
    origin_x = {origin_screen_x}
    origin_y = {origin_screen_y}

    # Calculate color based on time progression within THIS simulation
    # Cycle through full rainbow over the course of one simulation
    hue = (frame_idx * 360.0 / len(simulation)) % 360
    bob2_color = hsv_to_rgb(hue, 1.0, 1.0)

    # Build list of plot points for trails (all previous frames in this simulation)
    trail_points = []
    for i in range(frame_idx):
        f = simulation[i]
        trail_hue = (i * 360.0 / len(simulation)) % 360
        trail_color = hsv_to_rgb(trail_hue, 1.0, 0.5)  # Dimmer for trail
        trail_points.append((f[2], f[3], trail_color))  # x2, y2, color

    return render.Stack(
        children = [
            # Black background
            render.Box(
                width = 64,
                height = 32,
                color = "#000",
            ),

            # Display simulation number in corner
            render.Padding(
                pad = (1, 1, 0, 0),
                child = render.Text(
                    content = "no." + str(sim_idx + 1),
                    color = "#888",
                    font = "tom-thumb",
                ),
            ),

            # Fixed origin point (white dot)
            render.Padding(
                pad = (origin_x - 1, origin_y - 1, 0, 0),
                child = render.Circle(
                    color = "#FFFFFF",
                    diameter = 2,
                ),
            ),

            # Trail dots for second bob (with color gradient)
            render.Stack(
                children = [
                    render.Padding(
                        pad = (pt[0], pt[1], 0, 0),
                        child = render.Box(width=1, height=1, color=pt[2]),
                    ) if (pt[0] >= 0 and pt[0] < 64 and pt[1] >= 0 and pt[1] < 32) else render.Box(width=0, height=0)
                    for pt in trail_points
                ],
            ),

            # Lines connecting origin -> bob1 -> bob2
            # Line from origin to first bob
            render.Stack(
                children = [
                    render.Padding(
                        pad = (pt[0], pt[1], 0, 0),
                        child = render.Box(width=1, height=1, color="#FFFFFF"),
                    )
                    for pt in draw_line(origin_x, origin_y, x1, y1)
                ],
            ),
            # Line from first bob to second bob
            render.Stack(
                children = [
                    render.Padding(
                        pad = (pt[0], pt[1], 0, 0),
                        child = render.Box(width=1, height=1, color="#FFFFFF"),
                    )
                    for pt in draw_line(x1, y1, x2, y2)
                ],
            ),

            # First bob (cyan)
            render.Padding(
                pad = (x1 - 1, y1 - 1, 0, 0),
                child = render.Circle(
                    color = "#00FFFF",
                    diameter = 2,
                ),
            ) if (x1 >= 0 and x1 < 64 and y1 >= 0 and y1 < 32) else render.Box(width=0, height=0),

            # Second bob (color changes over time)
            render.Padding(
                pad = (x2 - 1, y2 - 1, 0, 0),
                child = render.Circle(
                    color = bob2_color,
                    diameter = 3,
                ),
            ) if (x2 >= 0 and x2 < 64 and y2 >= 0 and y2 < 32) else render.Box(width=0, height=0),
        ],
    )

def get_schema():
    return schema.Schema(
        version = "1",
        fields = [
            schema.Dropdown(
                id = "speed",
                name = "Speed",
                desc = "Animation playback speed",
                icon = "gauge",
                default = "fast",
                options = [
                    schema.Option(
                        display = "Fast (~3 seconds)",
                        value = "fast",
                    ),
                    schema.Option(
                        display = "Slow (~12 seconds)",
                        value = "slow",
                    ),
                ],
            ),
        ],
    )
'''

# Write the Starlark file
with open('pendulum.star', 'w') as f:
    f.write(starlark_code)

print(f"\nGenerated pendulum.star with {len(all_screen_frames)} simulations")
print(f"Each simulation: {len(all_screen_frames[0])} frames")
print(f"Total animation: {len(all_screen_frames) * len(all_screen_frames[0])} frames = {len(all_screen_frames) * len(all_screen_frames[0]) / 30:.1f} seconds")
print(f"Coordinate bounds: X({min_x:.2f}, {max_x:.2f}), Y({min_y:.2f}, {max_y:.2f})")
print(f"Scale factor: {scale:.2f}")
print(f"Origin position on screen: ({origin_screen_x}, {origin_screen_y})")
