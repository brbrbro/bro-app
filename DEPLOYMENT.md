# BRO APP 服务器部署指南

**服务器:** 106.53.188.248
**用户:** ubuntu
**部署路径:** /var/www/bro
**端口:** 5001 (Gunicorn) -> 80 (Nginx)

---

## 快速部署步骤

### 1. 本地准备

确保你有以下文件：
```
bro-deploy/
├── deploy.sh              # 主部署脚本
├── setup_services.sh      # 服务配置脚本
└── backend/               # 后端代码目录
    ├── app.py
    ├── config.py
    ├── models.py
    ├── requirements.txt
    └── routes/
```

### 2. 上传到服务器

**Windows 用户 - 使用 PowerShell:**
```powershell
# 压缩文件
Compress-Archive -Path backend\*,deploy.sh,setup_services.sh -DestinationPath bro-deploy.zip

# 上传（需要 scp，Git Bash 或 WSL 中可用）
scp bro-deploy.zip ubuntu@43.132.168.188:/home/ubuntu/
```

**或使用 WinSCP/FileZilla 等 SFTP 工具上传**

### 3. 在服务器上执行部署

SSH 登录服务器：
```bash
ssh ubuntu@43.132.168.188
# 密码: Brody20260509
```

解压并部署：
```bash
cd /home/ubuntu
unzip bro-deploy.zip -d bro-deploy
cd bro-deploy

# 步骤1: 部署基础环境
chmod +x deploy.sh
./deploy.sh

# 步骤2: 配置服务
chmod +x setup_services.sh
sudo ./setup_services.sh
```

### 4. 验证部署

```bash
# 测试 API
curl http://43.132.168.188/api/health

# 预期输出:
# {"db":"connected","service":"bro-backend","status":"ok","version":"1.0.0"}
```

---

## 管理命令

```bash
# 查看服务状态
sudo systemctl status bro

# 重启服务
sudo systemctl restart bro

# 查看日志
sudo tail -f /var/log/bro/error.log
sudo tail -f /var/log/bro/access.log

# 查看 Nginx 状态
sudo systemctl status nginx

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 配置文件说明

### 1. Gunicorn 配置 (/var/www/bro/gunicorn.conf.py)
- 监听: 127.0.0.1:5001
- 工作进程: 2
- 线程: 4

### 2. Systemd 服务 (/etc/systemd/system/bro.service)
- 自动启动: 是
- 重启策略: 总是重启
- 用户: ubuntu

### 3. Nginx 配置 (/etc/nginx/sites-available/bro)
- 监听: 80 端口
- 代理到: 127.0.0.1:5001
- 静态文件: /var/www/bro/static

---

## 与现有服务共存

当前服务器已有：
- **yojee** (端口 5000, api.yojee-edu.com)
- **bro** (端口 5001, 本部署)

两个服务独立运行，互不影响。

---

## 故障排除

### 1. 端口被占用
```bash
sudo lsof -i :5001
sudo kill -9 <PID>
```

### 2. 权限问题
```bash
sudo chown -R ubuntu:ubuntu /var/www/bro
sudo chmod +x /var/www/bro/*.sh
```

### 3. Nginx 配置错误
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 数据库问题
```bash
cd /var/www/bro
source venv/bin/activate
python3 -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
```

---

## 下一步

部署完成后，更新小程序配置：

编辑 `wechat-miniapp/app.js`:
```javascript
App({
  globalData: {
    userInfo: null,
    region: 'mainland',
    apiBase: 'http://43.132.168.188/api'
  }
});
```

**注意:** 正式上线需要使用 HTTPS (配置 SSL 证书)。开发阶段可使用 HTTP。