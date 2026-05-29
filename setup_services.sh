#!/bin/bash
# setup_services.sh - 配置 Gunicorn + Systemd + Nginx

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[1/4] 配置 Gunicorn...${NC}"
cat > /var/www/bro/gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:5001"
workers = 2
worker_class = "gthread"
threads = 4
timeout = 30
keepalive = 2
errorlog = "/var/log/bro/error.log"
accesslog = "/var/log/bro/access.log"
capture_output = True
enable_stdio_inheritance = True
EOF

echo -e "${YELLOW}[2/4] 配置 Systemd 服务...${NC}"
sudo tee /etc/systemd/system/bro.service > /dev/null << 'EOF'
[Unit]
Description=BRO APP Backend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/bro
Environment="PATH=/var/www/bro/venv/bin"
Environment="PYTHONPATH=/var/www/bro"
ExecStart=/var/www/bro/venv/bin/gunicorn -c /var/www/bro/gunicorn.conf.py app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bro

echo -e "${YELLOW}[3/4] 配置 Nginx...${NC}"
sudo tee /etc/nginx/sites-available/bro > /dev/null << 'EOF'
server {
    listen 80;
    server_name 43.132.168.188;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /static {
        alias /var/www/bro/static;
        expires 30d;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/bro /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

echo -e "${YELLOW}[4/4] 启动服务...${NC}"
sudo systemctl restart nginx
sudo systemctl start bro
sleep 2
sudo systemctl status bro --no-pager

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}服务配置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "测试命令:"
echo "  curl http://106.53.188.248/api/health"
echo ""
echo "管理命令:"
echo "  sudo systemctl start bro    # 启动"
echo "  sudo systemctl stop bro     # 停止"
echo "  sudo systemctl restart bro  # 重启"
echo "  sudo systemctl status bro   # 查看状态"
echo ""
echo "日志查看:"
echo "  sudo tail -f /var/log/bro/error.log"
echo "  sudo tail -f /var/log/bro/access.log"