#!/usr/bin/env python3
"""Generate viewer.html with available generations"""

import os
import base64
from pathlib import Path

OUTPUT_DIR = Path("output")

# Load dots.svg and encode as base64 for embedding
try:
    with open("dots.svg", "rb") as f:
        DOTS_SVG_BASE64 = base64.b64encode(f.read()).decode("ascii")
except FileNotFoundError:
    DOTS_SVG_BASE64 = ""

# Get list of available generation files
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
            background: #000;
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
        .progress-bar {{
            position: absolute;
            bottom: 0;
            left: 0;
            height: 2px;
            background: #4a9;
            width: 0%;
            transition: width 0.1s linear;
        }}
        .controls {{
            margin-top: 20px;
            display: flex;
            gap: 10px;
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
        .count {{
            margin-top: 20px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h1>Double Pendulum Random Viewer</h1>
    <p class="subtitle">Mouse over to loop • Mouse out to auto-advance</p>
    
    <div class="viewer-container">
        <div class="pendulum-display" id="display">
            <div class="loading" id="loading">Loading...</div>
            <img id="animation" alt="Double Pendulum Animation">
            <div class="progress-bar" id="progress"></div>
        </div>
        <div class="info-bar">
            <div class="generation-info">
                Generation <span id="genId">-</span>
            </div>
            <div class="status" id="status">Auto-advancing...</div>
        </div>
    </div>
    
    <div class="controls">
        <button id="nextBtn">Next Random</button>
        <button id="toggleLoopBtn">Pause Auto-Advance</button>
    </div>
    
    <p class="count">{len(generations)} generations available</p>

    <script>
        const generations = [{gen_list}];
        
        let currentGen = null;
        let isLooping = false;
        let isPaused = false;
        let progressInterval = null;
        let autoAdvanceTimeout = null;
        
        const display = document.getElementById('display');
        const animationImg = document.getElementById('animation');
        const loading = document.getElementById('loading');
        const genId = document.getElementById('genId');
        const status = document.getElementById('status');
        const progress = document.getElementById('progress');
        const nextBtn = document.getElementById('nextBtn');
        const toggleLoopBtn = document.getElementById('toggleLoopBtn');
        
        function getRandomGeneration() {{
            const idx = Math.floor(Math.random() * generations.length);
            return generations[idx];
        }}
        
        function loadGeneration(gen) {{
            currentGen = gen;
            loading.style.display = 'block';
            animationImg.style.display = 'none';
            genId.textContent = gen;
            
            const img = new Image();
            img.onload = () => {{
                animationImg.src = img.src;
                loading.style.display = 'none';
                animationImg.style.display = 'block';
                
                if (!isPaused && !isLooping) {{
                    startAutoAdvance(15000);  // Animation (~10s) + fade (5s)
                }}
            }};
            img.src = `${{gen}}.webp`;
        }}
        
        function startAutoAdvance(duration) {{
            clearTimeout(autoAdvanceTimeout);
            clearInterval(progressInterval);
            
            let elapsed = 0;
            const interval = 100;
            
            progress.style.width = '0%';
            progress.style.opacity = '1';
            
            progressInterval = setInterval(() => {{
                elapsed += interval;
                const pct = (elapsed / duration) * 100;
                progress.style.width = `${{pct}}%`;
                
                if (elapsed >= duration) {{
                    clearInterval(progressInterval);
                }}
            }}, interval);
            
            autoAdvanceTimeout = setTimeout(() => {{
                if (!isLooping && !isPaused) {{
                    loadNext();
                }}
            }}, duration);
            
            updateStatus();
        }}
        
        function loadNext() {{
            let nextGen = getRandomGeneration();
            while (nextGen === currentGen && generations.length > 1) {{
                nextGen = getRandomGeneration();
            }}
            loadGeneration(nextGen);
        }}
        
        function updateStatus() {{
            if (isLooping) {{
                status.textContent = 'Looping (mouse over)';
                status.classList.add('looping');
                progress.style.opacity = '0';
            }} else if (isPaused) {{
                status.textContent = 'Paused';
                status.classList.remove('looping');
                progress.style.opacity = '0';
            }} else {{
                status.textContent = 'Auto-advancing...';
                status.classList.remove('looping');
            }}
        }}
        
        display.addEventListener('mouseenter', () => {{
            isLooping = true;
            clearTimeout(autoAdvanceTimeout);
            clearInterval(progressInterval);
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
            clearInterval(progressInterval);
            loadNext();
        }});
        
        toggleLoopBtn.addEventListener('click', () => {{
            isPaused = !isPaused;
            toggleLoopBtn.textContent = isPaused ? 'Resume Auto-Advance' : 'Pause Auto-Advance';
            
            if (isPaused) {{
                clearTimeout(autoAdvanceTimeout);
                clearInterval(progressInterval);
            }} else if (!isLooping) {{
                loadNext();
            }}
            updateStatus();
        }});
        
        loadNext();
    </script>
</body>
</html>
"""

output_path = OUTPUT_DIR / "viewer.html"
# Replace SVG placeholder with actual base64 data
html = html.replace("___DOTS_SVG_BASE64___", DOTS_SVG_BASE64)
with open(output_path, "w") as f:
    f.write(html)

print(f"Generated viewer.html with {len(generations)} generations")
