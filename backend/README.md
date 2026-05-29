# BRO APP 后端部署指南

## 部署步骤

### 1. 上传文件到服务器

使用 VS Code SFTP 或其他 SFTP 工具上传 `backend/` 目录到 `/var/www/bro/`。

### 2. 在服务器上运行部署脚本

```bash
cd /var/www/bro
chmod +x deploy.sh
./deploy.sh
```

### 3. 手动部署（如果脚本失败）

```bash
cd /var/www/bro
sudo systemctl stop bro

# 安装依赖
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库
python3 -c "from app import app; from models import db; with app.app_context(): db.create_all()"

# 重启服务
sudo systemctl start bro
sudo systemctl status bro
```

### 4. 验证部署

```bash
# 测试健康检查
curl http://106.53.188.248:5001/api/health

# 测试题库API
curl "http://106.53.188.248:5001/api/questions?region=mainland"
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/questions` | GET | 获取题目列表 |
| `/api/questions/<id>` | GET | 获取题目详情 |
| `/api/questions/random` | GET | 随机题目 |
| `/api/shares` | GET/POST | 笔记列表/发布 |
| `/api/sync/upload` | POST | 上传同步数据 |
| `/api/sync/download` | GET | 下载同步数据 |

## 管理后台

访问：`http://106.53.188.248:5001/static/admin/index.html`

## 文件说明

- `app.py` - Flask 应用入口
- `models.py` - 数据库模型
- `config.py` - 配置文件
- `routes/` - API 路由
- `admin/` - 管理后台静态页面
- `deploy.sh` - 一键部署脚本