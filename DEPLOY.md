# Deployment Instructions for Double Pendulum API

## Files to Upload

Upload these files to `~/wildc.net/dp/` on your server:

Required Python modules:
- `api.py` - Main API script
- `pendulum.py` - Double pendulum physics
- `simulation.py` - Simulation functions
- `methods.py` - Numerical methods (RK4, Euler, etc.)
- `RK_DAE_solver.py` - Differential equation solver
- `pyproject.toml` - Dependencies for uv

Optional:
- `test_api.py` - Test script
- `API_USAGE.md` - Usage documentation

## Server Setup Steps

### 1. Upload Files

```bash
# From your local machine
scp api.py pendulum.py simulation.py methods.py RK_DAE_solver.py pyproject.toml \
    taviz@wildc.net:~/wildc.net/dp/
```

### 2. SSH to Server and Setup venv

```bash
ssh taviz@wildc.net
cd ~/wildc.net/dp

# Create virtual environment with uv
uv venv

# Install dependencies
uv pip install -r pyproject.toml
# Or alternatively:
uv sync

# Make API executable
chmod +x api.py
```

### 3. Test Locally on Server

```bash
cd ~/wildc.net/dp

# Test random mode
QUERY_STRING="mode=random&duration=5&step_size=0.1&seed=42" \
REQUEST_METHOD="GET" \
./api.py

# Test custom mode
echo '{"mode":"custom","pendulum1":{"m":5,"x":1.5,"y":-2,"u":0,"v":0},"pendulum2":{"m":3,"x":3.0,"y":-4,"u":0,"v":0},"duration":3,"step_size":0.1}' | \
REQUEST_METHOD="POST" \
./api.py
```

### 4. Configure Web Server

#### For Apache (with CGI enabled)

Add to your Apache config or .htaccess:

```apache
<Directory "/home/taviz/wildc.net/dp">
    Options +ExecCGI
    AddHandler cgi-script .py
    Require all granted
</Directory>
```

#### For nginx (with fcgiwrap)

```nginx
location /dp/api.py {
    gzip off;
    fastcgi_pass unix:/var/run/fcgiwrap.socket;
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME /home/taviz/wildc.net/dp/api.py;
}
```

### 5. Access via Web

Once configured, access at:
- Random: `https://wildc.net/dp/api.py?mode=random&duration=30&step_size=0.001`
- Custom: POST JSON to `https://wildc.net/dp/api.py`

## Troubleshooting

### Check Shebang Path
Verify the venv path in api.py matches your setup:
```bash
head -1 api.py
# Should show: #!/home/taviz/wildc.net/dp/.venv/bin/python3
```

### Check Python Path
```bash
.venv/bin/python3 -c "import sys; print(sys.executable)"
```

### Check Dependencies
```bash
.venv/bin/python3 -c "import numpy; print(numpy.__version__)"
```

### Test Direct Execution
```bash
cd ~/wildc.net/dp
./api.py
# Should output JSON (might show error about missing params, but shouldn't show import errors)
```

## Notes

- The shebang in `api.py` is set to `/home/taviz/wildc.net/dp/.venv/bin/python3`
- If your username or path differs, update the shebang line
- The API includes CORS headers (`Access-Control-Allow-Origin: *`) for web access
- Larger simulations (long duration, small step_size) will take time to compute
