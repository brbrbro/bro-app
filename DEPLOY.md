# BRO APP 题库导入平台 - 部署指南

**服务器:** 43.132.168.188 (腾讯云香港)  
**部署路径:** /var/www/bro  
**端口:** 5001 (Flask) → 80 (Nginx)

---

## 部署前准备

### 1. 本地准备部署包

在本地项目目录 `E:\AI code\1` 中创建 zip 文件：

**Windows PowerShell:**
```powershell
# 进入项目目录
cd "E:\AI code\1"

# 创建部署包（包含后端代码和部署脚本）
Compress-Archive -Path backend\*,deploy.sh,setup_services.sh,deploy-server.sh,DEPLOYMENT.md -DestinationPath bro-deploy.zip -Force
```

**或使用 WinRAR/7-Zip 手动压缩以下文件:**
- `backend/` 目录（完整后端代码）
- `deploy.sh`（初始部署脚本）
- `setup_services.sh`（服务配置脚本）
- `deploy-server.sh`（服务器端部署脚本）
- `DEPLOYMENT.md`（部署文档）

---

## 部署步骤

### 第一步：上传文件到服务器

**方法 A: 使用 WinSCP (推荐)**
1. 下载安装 WinSCP: https://winscp.net/
2. 连接服务器:
   - 主机名: 43.132.168.188
   - 用户名: ubuntu
   - 密码: Brody20260509
   - 端口: 22
3. 将 `bro-deploy.zip` 上传到 `/home/ubuntu/`

**方法 B: 使用命令行 SCP (需安装 Git Bash 或 WSL)**
```bash
# 在 Git Bash 中执行
scp bro-deploy.zip ubuntu@43.132.168.188:/home/ubuntu/
# 密码: Brody20260509
```

---

### 第二步：SSH 登录服务器并执行部署

```bash
# SSH 登录
ssh ubuntu@43.132.168.188
# 密码: Brody20260509

# 解压部署包
cd /home/ubuntu
unzip -o bro-deploy.zip -d bro-deploy
cd bro-deploy

# 执行部署
chmod +x *.sh
sudo ./deploy-server.sh
```

---

### 第三步：验证部署

```bash
# 测试 API
curl http://localhost:5001/api/health

# 预期输出:
# {"db":"connected","service":"bro-backend","status":"ok","version":"1.0.0"}

# 通过 Nginx 访问
curl http://43.132.168.188/api/health
```

---

## 安装系统依赖（Tesseract OCR）

如果 AI 识别需要使用本地 OCR：

```bash
# SSH 登录后执行
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra tesseract-ocr-eng

# 验证安装
tesseract --version
```

---

## 配置 OpenAI API Key（可选）

如果需要使用 AI 识别功能：

```bash
# 编辑配置文件
sudo nano /var/www/bro/backend/config.py

# 或设置环境变量
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**注意:** 如果不配置 OpenAI API Key，系统会使用本地 Tesseract OCR 进行基础识别。

---

## Web 管理后台部署

Web 后台是独立的前端项目，需要构建后部署：

### 1. 本地构建

```bash
# 在本地执行
cd "E:\AI code\1\web-admin"
npm install
npm run build

# 构建完成后，将 build/ 目录上传到服务器
```

### 2. 上传到服务器

```bash
# 使用 WinSCP 将 web-admin/build/ 上传到 /var/www/bro/web-admin/
# 或使用 SCP
scp -r web-admin/build/* ubuntu@43.132.168.188:/var/www/bro/web-admin/
```

### 3. 配置 Nginx 静态文件服务

```bash
# SSH 登录后编辑 Nginx 配置
sudo nano /etc/nginx/sites-available/bro
```

添加静态文件服务：
```nginx
server {
    listen 80;
    server_name 43.132.168.188;

    # Web 管理后台
    location /admin {
        alias /var/www/bro/web-admin;
        index index.html;
        try_files $uri $uri/ /admin/index.html;
    }

    # API
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态文件
    location /static {
        alias /var/www/bro/static;
    }
}
```

重启 Nginx：
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 访问 Web 后台

浏览器访问: `http://43.132.168.188/admin`

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

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/error.log
```

---

## 常见问题

### 1. 端口被占用
```bash
sudo lsof -i :5001
sudo kill -9 <PID>
```

### 2. 权限问题
```bash
sudo chown -R ubuntu:ubuntu /var/www/bro
```

### 3. 数据库锁定
```bash
# 如果 SQLite 数据库被锁定
sudo systemctl stop bro
# 检查是否有其他进程占用
lsof /var/www/bro/instance/bro.db
```

### 4. Nginx 配置错误
```bash
sudo nginx -t
# 如果报错，检查配置文件语法
```

---

## 安全建议

1. **修改默认密码:** 尽快修改服务器默认密码
2. **配置防火墙:** 只开放必要端口 (22, 80, 443)
3. **使用 HTTPS:** 配置 SSL 证书（有域名时）
4. **设置 API 认证:** 为 Web 后台添加登录认证

---

## 更新部署

后续更新代码时：

```bash
# 1. 上传新的 bro-deploy.zip
# 2. SSH 登录
# 3. 执行更新
sudo systemctl stop bro
cd /var/www/bro
# 复制新文件
sudo systemctl start bro
```