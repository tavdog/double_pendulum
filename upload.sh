#!/bin/bash
# Upload script for double pendulum API

SERVER="taviz@wildc.net"
REMOTE_DIR="~/wildc.net/dp"

echo "Uploading files to $SERVER:$REMOTE_DIR..."

# Create remote directory if it doesn't exist
ssh $SERVER "mkdir -p $REMOTE_DIR"

# Upload required files
scp api.py \
    pendulum.py \
    simulation.py \
    methods.py \
    RK_DAE_solver.py \
    pyproject.toml \
    $SERVER:$REMOTE_DIR/

# Upload optional documentation
scp API_USAGE.md \
    DEPLOY.md \
    test_api.py \
    $SERVER:$REMOTE_DIR/ 2>/dev/null || echo "Optional files not found, skipping..."

echo ""
echo "Upload complete!"
echo ""
echo "Next steps on server:"
echo "  ssh $SERVER"
echo "  cd $REMOTE_DIR"
echo "  uv venv"
echo "  uv pip install numpy"
echo "  chmod +x api.py"
echo "  # Test: QUERY_STRING=\"mode=random&duration=3&step_size=0.1\" REQUEST_METHOD=\"GET\" ./api.py"
