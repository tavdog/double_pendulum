#!/usr/bin/env python3
"""Test render - first 5 generations with lazy loading"""

import subprocess
import json
import tempfile
import os
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Get first 5 generation files
gen_files = sorted(Path("generations").glob("*.json"), key=lambda p: int(p.stem))[:5]


def render_gen(gen_file):
    gen_id = gen_file.stem
    webp_file = OUTPUT_DIR / f"{gen_id}.webp"
    static_file = OUTPUT_DIR / f"{gen_id}_static.webp"

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

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(anim_config, f)
        anim_config_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(static_config, f)
        static_config_path = f.name

    try:
        if not webp_file.exists():
            subprocess.run(
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
                cwd=".",
            )

        if not static_file.exists():
            subprocess.run(
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
                cwd=".",
            )
    finally:
        os.unlink(anim_config_path)
        os.unlink(static_config_path)

    return gen_id


print("Rendering first 5 generations...")
for gen_file in gen_files:
    gen_id = render_gen(gen_file)
    print(f"  Done: {gen_id}")

# Generate simple test HTML
html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lazy Loading Test</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }
        h1 { text-align: center; margin-bottom: 30px; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1800px; margin: 0 auto; }
        .pendulum-card { background: #1a1a1a; border-radius: 12px; overflow: hidden; transition: transform 0.2s ease; cursor: pointer; min-height: 160px; }
        .pendulum-card:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.5); }
        .pendulum-container { position: relative; width: 100%; aspect-ratio: 2 / 1; background: #000; overflow: hidden; }
        .pendulum-container img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; transition: opacity 0.2s ease; }
        .static-frame { z-index: 1; }
        .animation { z-index: 0; opacity: 0; }
        .pendulum-card:hover .static-frame { opacity: 0; }
        .pendulum-card:hover .animation { opacity: 1; z-index: 2; }
        .pendulum-info { padding: 10px 15px; background: #000; }
        .pendulum-id { font-size: 14px; color: #888; }
        .loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #333; font-size: 12px; z-index: 0; }
    </style>
</head>
<body>
    <h1>Lazy Loading Test (5 items)</h1>
    <div class="gallery">
"""

for gen_file in gen_files:
    gen_id = gen_file.stem
    html_content += f"""
        <div class="pendulum-card">
            <div class="pendulum-container">
                <div class="loading">Loading...</div>
                <img class="static-frame" data-src="{gen_id}_static.webp" alt="Generation {gen_id}" loading="lazy">
                <img class="animation" data-src="{gen_id}.webp" alt="Generation {gen_id} Animation" loading="lazy">
            </div>
            <div class="pendulum-info">
                <div class="pendulum-id">Generation {gen_id}</div>
            </div>
        </div>
"""

html_content += """
    </div>
    <script>
        // Lazy load animations only when card is hovered
        document.querySelectorAll('.pendulum-card').forEach(card => {
            const staticImg = card.querySelector('.static-frame');
            const animImg = card.querySelector('.animation');
            let animLoaded = false;
            
            card.addEventListener('mouseenter', () => {
                if (!animLoaded && animImg.dataset.src) {
                    animImg.src = animImg.dataset.src;
                    animLoaded = true;
                }
            });
        });
        
        // Intersection Observer for static frames
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        document.querySelectorAll('.static-frame[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    </script>
</body>
</html>
"""

with open(OUTPUT_DIR / "index.html", "w") as f:
    f.write(html_content)

print("\nDone! Open output/index.html to test lazy loading.")
