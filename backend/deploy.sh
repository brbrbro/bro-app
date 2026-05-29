#!/bin/bash
set -e

echo "=== BRO Backend Deployment Script ==="
echo "Date: $(date)"
echo ""

# Configuration
APP_DIR="/var/www/bro"
BACKUP_DIR="/var/www/backups"
SERVICE_NAME="bro"

echo "[1/7] Stopping service..."
sudo systemctl stop $SERVICE_NAME || true

echo ""
echo "[2/7] Creating backup..."
mkdir -p $BACKUP_DIR
if [ -d "$APP_DIR" ]; then
    BACKUP_FILE="$BACKUP_DIR/bro-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf $BACKUP_FILE -C $(dirname $APP_DIR) $(basename $APP_DIR)
    echo "Backup created: $BACKUP_FILE"
fi

echo ""
echo "[3/7] Checking files..."
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo "ERROR: requirements.txt not found in $APP_DIR"
    exit 1
fi

if [ ! -f "$APP_DIR/app.py" ]; then
    echo "ERROR: app.py not found in $APP_DIR"
    exit 1
fi

echo ""
echo "[4/7] Activating virtual environment..."
cd $APP_DIR
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

echo ""
echo "[5/7] Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "[6/7] Database initialization..."
python3 -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('Database tables created/verified')
"

echo ""
echo "[7/7] Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Checking service status..."
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "Testing API..."
curl -s http://localhost:5001/api/health | python3 -m json.tool || echo "API test failed"

echo ""
echo "Done!"
echo "Health check URL: http://106.53.188.248:5001/api/health"
echo "Questions API: http://106.53.188.248:5001/api/questions?region=mainland"