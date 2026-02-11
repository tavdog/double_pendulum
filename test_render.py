#!/usr/bin/env python3
"""Test render - only generation 100"""

import subprocess
import json
import tempfile
import os
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

gen_id = "100"
webp_file = OUTPUT_DIR / f"{gen_id}.webp"
static_file = OUTPUT_DIR / f"{gen_id}_static.webp"

# Config for animation (full animation)
anim_config = {
    "generation_id": gen_id,
    "animation": "api_random",
    "speed": "fast",
    "show_label": False,
    "line_style": "widget",
    "line_color": "#FFFFFF",
    "show_joints": True,
    "trail_fade": False,
    "show_full_animation": True,
    "last_frame_only": False,
}

# Config for static image (last frame only, no legs)
static_config = {
    "generation_id": gen_id,
    "animation": "api_random",
    "speed": "fast",
    "show_label": False,
    "line_style": "none",
    "show_joints": False,
    "trail_fade": False,
    "show_full_animation": True,
    "last_frame_only": True,
}

# Write configs
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(anim_config, f)
    anim_config_path = f.name

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(static_config, f)
    static_config_path = f.name

try:
    # Render full WebP animation at 2x (128x64)
    print(f"Rendering {gen_id}.webp...")
    result = subprocess.run(
        [
            "pixlet",
            "render",
            "double_pendulum.star",
            "--config",
            anim_config_path,
            "--output",
            str(webp_file),
            "--width",
            "64",
            "--height",
            "32",
            "--2x",
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(f"  Created: {webp_file}")

    # Render static frame
    print(f"Rendering {gen_id}_static.webp...")
    result = subprocess.run(
        [
            "pixlet",
            "render",
            "double_pendulum.star",
            "--config",
            static_config_path,
            "--output",
            str(static_file),
            "--width",
            "64",
            "--height",
            "32",
            "--2x",
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(f"  Created: {static_file}")

finally:
    os.unlink(anim_config_path)
    os.unlink(static_config_path)

print("\nDone!")
