#!/usr/bin/env python3
"""Batch renderer for double pendulum generations.
Processes all JSON files in generations/ directory and outputs:
- Scaled PNG of the last frame
- Full WebP animation
- HTML gallery with hover-to-play

Usage:
    python3 batch_render.py [max_count]
    - max_count: Optional maximum number of generations to process (default: all)
"""

import os
import json
import subprocess
import glob
import base64
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple
import tempfile

# Parse command line arguments
parser = argparse.ArgumentParser(description="Batch render double pendulum generations")
parser.add_argument(
    "max_count",
    type=int,
    nargs="?",
    default=None,
    help="Maximum number of generations to process (default: all)",
)
args = parser.parse_args()

# Configuration
GENERATIONS_DIR = Path("generations")
OUTPUT_DIR = Path("output")
MAX_WORKERS = 4  # Parallel rendering
SCALE_FACTOR = 2  # Scale up factor for last frame (64x32 -> 128x64)

# Load dots.svg and encode as base64 for embedding
try:
    with open("dots.svg", "rb") as f:
        DOTS_SVG_BASE64 = base64.b64encode(f.read()).decode("ascii")
except FileNotFoundError:
    DOTS_SVG_BASE64 = ""


def get_generation_files() -> List[Path]:
    """Get generation JSON files sorted by ID, limited to max_count if specified."""
    files = list(GENERATIONS_DIR.glob("*.json"))
    # Sort by numeric ID
    files.sort(key=lambda p: int(p.stem))
    # Limit to max_count if specified
    if args.max_count is not None:
        files = files[: args.max_count]
    return files


# HTML template - uses f-string to embed base64 SVG
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Double Pendulum Gallery</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0a0a0a;
            color: #fff;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            font-weight: 300;
            letter-spacing: 2px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto 20px;
        }}
        .play-all-btn {{
            background: #333;
            border: 1px solid #555;
            color: #fff;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s ease;
        }}
        .play-all-btn:hover {{
            background: #444;
        }}
        .play-all-btn.active {{
            background: #4a9;
            border-color: #4a9;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .pendulum-card {{
            background: #000;
            border-radius: 4px;
            overflow: hidden;
            transition: transform 0.2s ease;
            min-height: 85px;
        }}
        .pendulum-card:hover {{
            transform: scale(1.05);
            z-index: 10;
        }}
        .pendulum-container {{
            position: relative;
            width: 100%;
            aspect-ratio: 2 / 1;
            background: #000;
            overflow: hidden;
        }}
        .pendulum-container img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
            image-rendering: pixelated;
            image-rendering: -moz-crisp-edges;
            image-rendering: crisp-edges;
            -webkit-mask-image: url('data:image/svg+xml;base64,___DOTS_SVG_BASE64___');
            -webkit-mask-repeat: no-repeat;
            -webkit-mask-size: contain;
            mask-image: url('data:image/svg+xml;base64,___DOTS_SVG_BASE64___');
            mask-repeat: no-repeat;
            mask-size: contain;
        }}
        .pendulum-container img.animation {{
            opacity: 0;
        }}
        .pendulum-container img.static-frame {{
            opacity: 1;
        }}
        .gallery.playing-all .pendulum-container img.animation,
        .pendulum-card:hover .pendulum-container img.animation {{
            opacity: 1;
        }}
        .gallery.playing-all .pendulum-container img.static-frame,
        .pendulum-card:hover .pendulum-container img.static-frame {{
            opacity: 0;
        }}
        .pendulum-info {{
            padding: 5px 8px;
            background: #000;
            opacity: 0;
            transition: opacity 0.2s ease;
        }}
        .pendulum-card:hover .pendulum-info {{
            opacity: 1;
        }}
        .pendulum-id {{
            font-size: 11px;
            color: #888;
        }}
        .stats {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Double Pendulum Gallery</h1>
        <button class="play-all-btn" id="playAllBtn">Play All</button>
    </div>
    <p style="text-align: center; color: #666; margin-bottom: 20px;">Hover to preview • Click to view in loop mode</p>
    <div class="gallery" id="gallery"></div>
    <div class="stats">
        <p>{total_count} generations</p>
    </div>

    <script>
        const gallery = document.getElementById('gallery');
        const playAllBtn = document.getElementById('playAllBtn');
        const totalGens = {total_count};
        const genIds = {gen_ids_js};
        let playingAll = false;

        genIds.forEach(i => {{
            const card = document.createElement('div');
            card.className = 'pendulum-card';
            card.onclick = () => window.location.href = 'viewer.html?gen=' + i + '&loop=1';

            const container = document.createElement('div');
            container.className = 'pendulum-container';

            const img = document.createElement('img');
            img.className = 'animation';
            img.dataset.src = i + '.webp';
            img.alt = 'Generation ' + i;

            const staticImg = document.createElement('img');
            staticImg.className = 'static-frame';
            staticImg.dataset.src = i + '_static.webp';
            staticImg.alt = 'Generation ' + i;

            const info = document.createElement('div');
            info.className = 'pendulum-info';
            info.innerHTML = '<span class="pendulum-id">Generation ' + i + '</span>';

            container.appendChild(img);
            container.appendChild(staticImg);
            card.appendChild(container);
            card.appendChild(info);
            gallery.appendChild(card);
        }});

        playAllBtn.addEventListener('click', () => {{
            playingAll = !playingAll;
            gallery.classList.toggle('playing-all', playingAll);
            playAllBtn.textContent = playingAll ? 'Stop All' : 'Play All';
            playAllBtn.classList.toggle('active', playingAll);
        }});

        const imageObserver = new IntersectionObserver((entries, observer) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }}
            }});
        }}, {{
            rootMargin: '100px'
        }});

        document.querySelectorAll('img[data-src]').forEach(img => {{
            imageObserver.observe(img);
        }});
    </script>
</body>
    </html>
 """


def render_generation(gen_file: Path) -> Tuple[str, str, str] | None:
    """
    Render a single generation file.
    Returns: (generation_id, static_filename, webp_filename)
    """
    gen_id = gen_file.stem
    webp_file = OUTPUT_DIR / f"{gen_id}.webp"
    static_file = OUTPUT_DIR / f"{gen_id}_static.webp"

    # Config for animation (full animation with 3s fade out, no freeze)
    anim_config = {
        "generation_id": gen_id,
        "animation": "api_random",
        "speed": "fast",
        "show_label": False,
        "line_style": "widget",
        "line_color": "#404040",
        "show_joints": True,
        "trail_fade": False,
        "show_full_animation": True,
        "last_frame_only": False,
        "freeze_duration": "0",
        "enable_fade_out": True,
        "transparent_bg": True,
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
        "transparent_bg": True,
    }

    # Write configs to temp files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(anim_config, f)
        anim_config_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(static_config, f)
        static_config_path = f.name

    try:
        # Render full WebP animation at native resolution (64x32)
        if not webp_file.exists():
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
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )
            if result.returncode != 0:
                print(f"Error rendering {gen_id}.webp: {result.stderr}")
                return None

        # Render last frame as static WebP at native resolution (64x32)
        if not static_file.exists():
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
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )
            if result.returncode != 0:
                print(f"Error rendering {gen_id}_static.webp: {result.stderr}")
                return None

        return (gen_id, f"{gen_id}_static.webp", f"{gen_id}.webp")

    finally:
        os.unlink(anim_config_path)
        os.unlink(static_config_path)


def generate_html(items: List[Tuple[str, str, str]]) -> str:
    """Generate the HTML gallery."""
    # Sort results by generation ID
    items.sort(key=lambda x: int(x[0]))

    # Create JavaScript array of successful generation IDs
    gen_ids = [item[0] for item in items]

    html = HTML_TEMPLATE.format(
        total_count=len(items), gen_ids_js="[" + ",".join(gen_ids) + "]"
    )
    # Replace SVG placeholder with actual base64 data
    html = html.replace("___DOTS_SVG_BASE64___", DOTS_SVG_BASE64)
    return html


def main():
    print("Double Pendulum Batch Renderer")
    print("=" * 40)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Get all generation files
    gen_files = get_generation_files()
    print(f"Found {len(gen_files)} generation files")

    if not gen_files:
        print("No generation files found in generations/ directory")
        return

    # Process all generations in parallel
    print(f"\nRendering with {MAX_WORKERS} workers...")
    results = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(render_generation, f): f for f in gen_files}

        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                if result:
                    results.append(result)
                    gen_id = result[0]
                    print(f"  [{i + 1}/{len(gen_files)}] Rendered generation {gen_id}")
            except Exception as e:
                gen_file = futures[future]
                print(f"  Error processing {gen_file}: {e}")

    # Sort results by generation ID
    results.sort(key=lambda x: int(x[0]))

    # Generate HTML
    print("\nGenerating HTML gallery...")
    html_content = generate_html(results)
    html_path = OUTPUT_DIR / "index.html"
    with open(html_path, "w") as f:
        f.write(html_content)

    print(f"\nComplete!")
    print(f"  Output directory: {OUTPUT_DIR.absolute()}")
    print(f"  HTML gallery: {html_path.absolute()}")
    print(f"  Total rendered: {len(results)}")


if __name__ == "__main__":
    main()
