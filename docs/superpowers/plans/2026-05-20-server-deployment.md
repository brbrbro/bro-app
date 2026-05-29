# BRO APP 自有服务器部署计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Flask 后端部署到用户自有服务器，支持小程序 API 访问

**Architecture:** 使用 Gunicorn + Nginx + Systemd 部署 Flask 应用，SQLite 作为数据库

**Tech Stack:** Python 3.10 / Flask / Gunicorn / Nginx / Systemd / Ubuntu 22.04

---

## 文件结构

```
服务器部署相关文件：
├── backend/                      后端代码（已存在）
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── requirements.txt
│   ├── routes/
│   └── admin/
├── deployment/
│   ├── gunicorn.conf.py          Gunicorn 配置
│   ├── bro.service               Systemd 服务文件
│   └── nginx.conf                Nginx 站点配置
└── scripts/
    └── setup_server.sh           服务器初始化脚本
```

---

## 任务分解

### Task 1: 准备部署配置文件

**Files:**
- Create: `deployment/gunicorn.conf.py`
- Create: `deployment/bro.service`
- Create: `deployment/nginx.conf`
- Create: `scripts/setup_server.sh`

- [ ] **Step 1: 创建 Gunicorn 配置文件**

```python
# deployment/gunicorn.conf.py
bind = "0.0.0.0:5001"
workers = 2
worker_class = "gthread"
threads = 4
timeout = 30
keepalive = 2
errorlog = "/var/log/bro/error.log"
accesslog = "/var/log/bro/access.log"
capture_output = True
enable_stdio_inheritance = True
```

- [ ] **Step 2: 创建 Systemd 服务文件**

```ini
# deployment/bro.service
[Unit]
Description=BRO APP Backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/bro
Environment="PATH=/var/www/bro/venv/bin"
Environment="PYTHONPATH=/var/www/bro"
ExecStart=/var/www/bro/venv/bin/gunicorn -c /var/www/bro/deployment/gunicorn.conf.py app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: 创建 Nginx 配置文件**

```nginx
# deployment/nginx.conf
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或服务器IP

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/bro/backend/static;
        expires 30d;
    }
}
```

- [ ] **Step 4: 创建服务器初始化脚本**

```bash
#!/bin/bash
# scripts/setup_server.sh

set -e

echo "=== BRO APP 服务器部署脚本 ==="

# 更新系统
echo "[1/8] 更新系统..."
sudo apt update && sudo apt upgrade -y

# 安装必要软件
echo "[2/8] 安装必要软件..."
sudo apt install -y python3 python3-pip python3-venv nginx git

# 创建应用目录
echo "[3/8] 创建应用目录..."
sudo mkdir -p /var/www/bro
sudo chown $USER:$USER /var/www/bro

# 复制代码到服务器（假设代码已通过git或其他方式上传到服务器）
echo "[4/8] 请确保代码已上传到 /var/www/bro"
echo "    可以使用: scp -r backend/ user@server:/var/www/bro/"

# 创建虚拟环境
echo "[5/8] 创建 Python 虚拟环境..."
cd /var/www/bro
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "[6/8] 安装 Python 依赖..."
pip install -r backend/requirements.txt

# 创建日志目录
echo "[7/8] 创建日志目录..."
sudo mkdir -p /var/log/bro
sudo chown www-data:www-data /var/log/bro

# 初始化数据库
echo "[8/8] 初始化数据库..."
cd backend
python3 -c "from app import app; from models import db; app.app_context().push(); db.create_all()"

echo "=== 基础环境准备完成 ==="
echo "下一步: 配置 Systemd 和 Nginx"
```

---

### Task 2: 服务器环境配置

**Prerequisites:** 需要服务器 SSH 访问权限

- [ ] **Step 1: 配置 Systemd 服务**

```bash
# 在服务器上执行
sudo cp deployment/bro.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bro
```

- [ ] **Step 2: 配置 Nginx**

```bash
# 在服务器上执行
sudo cp deployment/nginx.conf /etc/nginx/sites-available/bro
sudo ln -s /etc/nginx/sites-available/bro /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

- [ ] **Step 3: 配置防火墙**

```bash
# 开放必要端口
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable
```

---

### Task 3: 启动服务并验证

- [ ] **Step 1: 启动后端服务**

```bash
sudo systemctl start bro
sudo systemctl status bro
```

**Expected output:** `Active: active (running)`

- [ ] **Step 2: 验证 API 可访问**

```bash
# 本地测试
curl http://localhost:5001/api/health

# 应该返回:
# {"db":"connected","service":"bro-backend","status":"ok","version":"1.0.0"}
```

- [ ] **Step 3: 验证 Nginx 代理**

```bash
# 通过 Nginx 访问
curl http://your-server-ip/api/health
```

---

### Task 4: 更新小程序配置

**Files:**
- Modify: `wechat-miniapp/app.js`

- [ ] **Step 1: 修改 API 地址**

```javascript
// wechat-miniapp/app.js
App({
  globalData: {
    userInfo: null,
    region: 'mainland',
    apiBase: 'https://your-domain.com/api'  // 替换为你的服务器地址
    // 如果没有域名，使用 http://your-server-ip/api
    // 注意：小程序要求 HTTPS，需要配置 SSL 证书
  }
});
```

---

### Task 5: SSL 证书配置（可选但推荐）

- [ ] **Step 1: 安装 Certbot**

```bash
sudo apt install -y certbot python3-certbot-nginx
```

- [ ] **Step 2: 申请证书**

```bash
sudo certbot --nginx -d your-domain.com
```

- [ ] **Step 3: 自动续期**

```bash
sudo systemctl status certbot.timer
```

---

## 自检清单

- [x] 所有配置文件包含完整代码
- [x] 无 TBD/TODO 占位符
- [x] 包含验证步骤和预期输出
- [x] 包含错误处理（systemd restart）
- [x] 包含 SSL 配置指引

---

**部署计划完成。** 保存至 `docs/superpowers/plans/2026-05-20-server-deployment.md`

**执行选项：**

1. **Subagent-Driven (推荐)** — 分任务执行，每步验证
2. **Inline Execution** — 批量执行

**注意：** 需要用户提供服务器信息（IP/域名、SSH 凭据）才能实际执行部署。