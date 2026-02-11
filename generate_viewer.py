#!/usr/bin/env python3
"""Generate viewer.html with available generations"""

import os
import base64
from pathlib import Path

OUTPUT_DIR = Path("output")

try:
    with open("dots.svg", "rb") as f:
        DOTS_SVG_BASE64 = base64.b64encode(f.read()).decode("ascii")
except FileNotFoundError:
    DOTS_SVG_BASE64 = ""

generations = []
for f in OUTPUT_DIR.glob("*.webp"):
    if "_static" not in f.name:
        try:
            gen_id = int(f.stem)
            generations.append(gen_id)
        except ValueError:
            pass

generations.sort()
gen_list = ", ".join(str(g) for g in generations)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Double Pendulum Random Viewer</title>
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
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        h1 {{
            font-weight: 300;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }}
        .viewer-container {{
            background: #1a1a1a;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            max-width: 800px;
            width: 100%;
        }}
        .pendulum-display {{
            position: relative;
            width: 100%;
            aspect-ratio: 2 / 1;
            background: #000;
            overflow: hidden;
            cursor: pointer;
        }}
        .pendulum-display img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            aspect-ratio: 2 / 1;
            background: transparent;
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
        .pendulum-display img.layer-1 {{
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
        }}
        .pendulum-display img.layer-2 {{
            position: absolute;
            top: 0;
            left: 0;
            z-index: 2;
            opacity: 1.0;
            mix-blend-mode: screen;
            filter: brightness(1.3);
        }}
        .info-bar {{
            padding: 15px 20px;
            background: #000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .generation-info {{
            font-size: 14px;
            color: #888;
        }}
        .generation-info span {{
            color: #fff;
            font-weight: 500;
        }}
        .status {{
            font-size: 12px;
            color: #666;
            font-style: italic;
        }}
        .status.looping {{
            color: #4a9;
        }}
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #333;
            font-size: 14px;
            z-index: 10;
        }}
        .controls {{
            margin-top: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        button {{
            padding: 10px 20px;
            background: #1a1a1a;
            border: 1px solid #333;
            color: #fff;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s ease;
        }}
        button:hover {{
            background: #333;
            border-color: #555;
        }}
        button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        button.active {{
            background: #4a9;
            border-color: #4a9;
        }}
        .count {{
            margin-top: 20px;
            color: #666;
            font-size: 12px;
        }}
        .theater-ui {{
            text-align: center;
            margin-bottom: 20px;
        }}
        body.theater-mode .theater-ui,
        body.theater-mode .info-bar {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="theater-ui">
        <h1>Double Pendulum Random Viewer</h1>
        <p class="subtitle">Mouse over to loop • Mouse out to auto-advance</p>

        <div class="controls">
            <button id="nextBtn">Next Random</button>
            <button id="toggleLoopBtn">Pause Auto-Advance</button>
            <button id="overlayBtn">Battle Mode: OFF</button>
            <button id="theaterBtn">Theater Mode: OFF</button>
        </div>

        <p class="count">{len(generations)} generations available</p>
    </div>

    <div class="viewer-container">
        <div class="pendulum-display" id="display">
            <div class="loading" id="loading">Loading...</div>
            <img id="layer1" class="layer-1" alt="Layer 1" style="display: none;">
            <img id="layer2" class="layer-2" alt="Layer 2" style="display: none;">
        </div>
        <div class="info-bar">
            <div class="generation-info">
                Generation <span id="genId">-</span>
            </div>
            <div class="status" id="status">Auto-advancing...</div>
        </div>
    </div>

    <script>
        const generations = [{gen_list}];

        let currentGen1 = null;
        let currentGen2 = null;
        let isLooping = false;
        let isPaused = false;
        let autoAdvanceTimeout = null;
        let overlayMode = false;
        let theaterMode = false;

        const display = document.getElementById('display');
        const layer1 = document.getElementById('layer1');
        const layer2 = document.getElementById('layer2');
        const loading = document.getElementById('loading');
        const genId = document.getElementById('genId');
        const status = document.getElementById('status');
        const nextBtn = document.getElementById('nextBtn');
        const toggleLoopBtn = document.getElementById('toggleLoopBtn');
        const overlayBtn = document.getElementById('overlayBtn');
        const theaterBtn = document.getElementById('theaterBtn');

        function getRandomGeneration() {{
            const idx = Math.floor(Math.random() * generations.length);
            return generations[idx];
        }}

        function loadGeneration(gen, layer) {{
            const img = layer === 1 ? layer1 : layer2;
            
            if (layer === 1) {{
                currentGen1 = gen;
                loading.style.display = 'block';
                layer1.style.display = 'none';
            }} else {{
                currentGen2 = gen;
                layer2.style.display = 'none';
            }}
            
            genId.textContent = overlayMode && currentGen2 ? `${{currentGen1}} vs ${{currentGen2}}` : currentGen1;
            
            const imgObj = new Image();
            imgObj.onload = () => {{
                img.src = imgObj.src;
                loading.style.display = 'none';
                
                if (layer === 1) {{
                    layer1.style.display = 'block';
                }} else {{
                    layer2.style.display = 'block';
                }}
                
                if (!isPaused && !isLooping) {{
                    startAutoAdvance(15000);
                }}
            }};
            imgObj.src = `${{gen}}.webp`;
        }}

        function startAutoAdvance(duration) {{
            clearTimeout(autoAdvanceTimeout);
            
            autoAdvanceTimeout = setTimeout(() => {{
                if (!isLooping && !isPaused) {{
                    loadNext();
                }}
            }}, duration);
            
            updateStatus();
        }}

        function loadNext() {{
            let nextGen = getRandomGeneration();
            while (nextGen === currentGen1 && generations.length > 1) {{
                nextGen = getRandomGeneration();
            }}
            
            if (overlayMode) {{
                let nextGen2 = getRandomGeneration();
                while (nextGen2 === currentGen2 && generations.length > 1) {{
                    nextGen2 = getRandomGeneration();
                }}
                loadGeneration(nextGen2, 2);
            }}
            
            loadGeneration(nextGen, 1);
        }}

        function updateStatus() {{
            if (isLooping) {{
                status.textContent = 'Looping (mouse over)';
                status.classList.add('looping');
            }} else if (isPaused) {{
                status.textContent = 'Paused';
                status.classList.remove('looping');
            }} else {{
                status.textContent = 'Auto-advancing...';
                status.classList.remove('looping');
            }}
        }}

        display.addEventListener('mouseenter', () => {{
            isLooping = true;
            clearTimeout(autoAdvanceTimeout);
            updateStatus();
        }});

        display.addEventListener('mouseleave', () => {{
            isLooping = false;
            if (!isPaused) {{
                startAutoAdvance(5000);
            }}
            updateStatus();
        }});

        nextBtn.addEventListener('click', () => {{
            clearTimeout(autoAdvanceTimeout);
            loadNext();
        }});

        toggleLoopBtn.addEventListener('click', () => {{
            isPaused = !isPaused;
            toggleLoopBtn.textContent = isPaused ? 'Resume Auto-Advance' : 'Pause Auto-Advance';
            
            if (isPaused) {{
                clearTimeout(autoAdvanceTimeout);
            }} else if (!isLooping) {{
                startAutoAdvance(5000);
            }}
            updateStatus();
        }});

        overlayBtn.addEventListener('click', () => {{
            overlayMode = !overlayMode;
            overlayBtn.textContent = overlayMode ? 'Battle Mode: ON' : 'Battle Mode: OFF';
            overlayBtn.classList.toggle('active', overlayMode);
            
            if (overlayMode) {{
                layer2.style.display = 'block';
                if (!currentGen2) {{
                    loadGeneration(getRandomGeneration(), 2);
                }}
            }} else {{
                layer2.style.display = 'none';
            }}
            
            genId.textContent = overlayMode ? `${{currentGen1}} vs ${{currentGen2}}` : currentGen1;
        }});

        theaterBtn.addEventListener('click', () => {{
            theaterMode = !theaterMode;
            document.body.classList.toggle('theater-mode', theaterMode);
            theaterBtn.textContent = theaterMode ? 'Theater Mode: ON' : 'Theater Mode: OFF';
            theaterBtn.classList.toggle('active', theaterMode);
        }});

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' && theaterMode) {{
                theaterMode = false;
                document.body.classList.remove('theater-mode');
                theaterBtn.textContent = 'Theater Mode: OFF';
                theaterBtn.classList.remove('active');
            }}
        }});

        loadNext();
    </script>
</body>
</html>
"""

output_path = OUTPUT_DIR / "viewer.html"
html = html.replace("___DOTS_SVG_BASE64___", DOTS_SVG_BASE64)
with open(output_path, "w") as f:
    f.write(html)

print(f"Generated viewer.html with {len(generations)} generations")
