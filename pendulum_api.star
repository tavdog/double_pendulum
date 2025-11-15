load("render.star", "render")
load("encoding/base64.star", "base64")
load("encoding/json.star", "json")
load("http.star", "http")
load("random.star", "random")
load("schema.star", "schema")
load("time.star", "time")
load("cache.star", "cache")

# API endpoint for fetching simulations
API_URL = "https://wildc.net/dp/api.py"

# Cache TTL in seconds (1 hour)
CACHE_TTL = 15

# Display constants (matching generate_pixlet.py)
# Pendulum length constraints
LENGTH_1_MAX = 6.0
LENGTH_2_MAX = 7.2
MAX_EXTENT = LENGTH_1_MAX + LENGTH_2_MAX  # 13.2

# Screen positioning
ORIGIN_X = 32  # Horizontally centered
ORIGIN_Y = 11  # 35% down from top (32 * 0.35 ≈ 11)

# Calculate scale to fit pendulum on screen
# Available space: left=32px, right=32px, up=11px, down=21px
PADDING = 2
SCALE_X = (32.0 - PADDING) / MAX_EXTENT  # Horizontal scale ≈ 2.27
SCALE_Y = (21.0 - PADDING) / MAX_EXTENT  # Vertical scale ≈ 1.44
SCALE = int(SCALE_Y * 10) / 10.0  # Use smaller scale, round to 1 decimal ≈ 1.4

def fetch_simulation(seed):
    """Fetch a simulation from the API and transform coordinates to pixel space."""
    cache_key = "sim_" + str(seed)

    # Try to get from cache first
    cached = cache.get(cache_key)
    if cached != None:
        return json.decode(cached)

    # Build API URL with parameters
    # Request a simulation with specific seed for reproducibility
    url = API_URL + "?mode=random&duration=15&step_size=0.033&seed=" + str(seed)

    # Fetch from API
    response = http.get(url, ttl_seconds=CACHE_TTL)
    if response.status_code != 200:
        print("API request failed: " + str(response.status_code))
        return None

    # Parse JSON response
    data = response.json()
    trajectory = data.get("trajectory", [])

    # Transform coordinates from physics space to pixel space
    # trajectory contains [x1, y1, x2, y2] arrays
    pixel_frames = []
    for point in trajectory:
        if len(point) >= 4:
            # Map physics coordinates to pixels
            # Physics origin (0,0) maps to (ORIGIN_X, ORIGIN_Y)
            # Note: Y-axis is inverted (physics +y is up, screen +y is down)
            x1_pixel = ORIGIN_X + int(point[0] * SCALE)
            y1_pixel = ORIGIN_Y - int(point[1] * SCALE)
            x2_pixel = ORIGIN_X + int(point[2] * SCALE)
            y2_pixel = ORIGIN_Y - int(point[3] * SCALE)

            pixel_frames.append([x1_pixel, y1_pixel, x2_pixel, y2_pixel])

    # Cache the transformed data
    cache.set(cache_key, json.encode(pixel_frames), ttl_seconds=CACHE_TTL)

    return pixel_frames

def main(config):
    # Get animation seed from config
    seed_config = config.get("seed", "random")

    # Determine seed for simulation
    if seed_config == "random" or seed_config == "":
        # Use current time to pick a different simulation periodically
        seed = time.now().unix  # Changes every second
    else:
        # Use specified seed
        seed = int(seed_config)

    print("Fetching simulation with seed: " + str(seed))

    # Fetch simulation from API
    simulation = fetch_simulation(seed)

    # Handle fetch failure
    if simulation == None or len(simulation) == 0:
        return render.Root(
            child = render.Text("API Error", color="#FF0000")
        )

    # Get speed setting from config
    speed = config.get("speed", "fast")

    # Set delay based on speed (slow = 33ms, fast = 16ms)
    if speed == "fast":
        delay = 16  # Fast: twice as fast (~60fps)
    else:
        delay = 33  # Slow: normal speed (~30fps)

    # Render all frames from the selected simulation
    all_frames = []
    for frame_idx in range(len(simulation)):
        all_frames.append(render_frame(simulation, seed, frame_idx))

    return render.Root(
        delay = delay,
        show_full_animation = True,
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

def render_frame(simulation, seed, frame_idx):
    frame = simulation[frame_idx]
    x1, y1, x2, y2 = frame[0], frame[1], frame[2], frame[3]

    # Fixed origin (anchor point) - matches the physics origin (0,0)
    origin_x = ORIGIN_X
    origin_y = ORIGIN_Y

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

            # Display simulation seed in top left corner
            render.Padding(
                pad = (1, 1, 0, 0),
                child = render.Text(
                    content = "#" + str(seed),
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
                default = "slow",
                options = [
                    schema.Option(
                        display = "Fast (2x speed)",
                        value = "fast",
                    ),
                    schema.Option(
                        display = "Slow (normal)",
                        value = "slow",
                    ),
                ],
            ),
            schema.Dropdown(
                id = "seed",
                name = "Simulation",
                desc = "Select simulation seed (or random)",
                icon = "dice",
                default = "random",
                options = [
                    schema.Option(display = "Random (changes every second)", value = "random"),
                    schema.Option(display = "Seed #1", value = "1"),
                    schema.Option(display = "Seed #2", value = "2"),
                    schema.Option(display = "Seed #3", value = "3"),
                    schema.Option(display = "Seed #42", value = "42"),
                    schema.Option(display = "Seed #100", value = "100"),
                    schema.Option(display = "Seed #123", value = "123"),
                    schema.Option(display = "Seed #456", value = "456"),
                    schema.Option(display = "Seed #789", value = "789"),
                    schema.Option(display = "Seed #999", value = "999"),
                ],
            ),
        ],
    )
