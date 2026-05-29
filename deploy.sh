#!/bin/bash
# deploy.sh - BRO APP 服务器部署脚本
# 使用方法: 上传此文件和 backend/ 目录到服务器，然后运行 ./deploy.sh

set -e

echo "========================================"
echo "BRO APP 服务器部署脚本"
echo "服务器: 106.53.188.248"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否以 root 或 ubuntu 运行
if [ "$USER" != "ubuntu" ] && [ "$USER" != "root" ]; then
    echo -e "${RED}错误: 请使用 ubuntu 或 root 用户运行此脚本${NC}"
    exit 1
fi

# 1. 更新系统
echo -e "${YELLOW}[1/8] 更新系统...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. 安装必要软件
echo -e "${YELLOW}[2/8] 安装必要软件...${NC}"
sudo apt install -y python3 python3-pip python3-venv nginx git

# 3. 创建应用目录
echo -e "${YELLOW}[3/8] 创建应用目录...${NC}"
sudo mkdir -p /var/www/bro
sudo chown ubuntu:ubuntu /var/www/bro

# 4. 复制代码
echo -e "${YELLOW}[4/8] 复制代码到 /var/www/bro...${NC}"
if [ -d "backend" ]; then
    cp -r backend/* /var/www/bro/
else
    echo -e "${RED}错误: 找不到 backend/ 目录${NC}"
    echo "请确保此脚本与 backend/ 目录在同一目录"
    exit 1
fi

# 5. 创建虚拟环境
echo -e "${YELLOW}[5/8] 创建 Python 虚拟环境...${NC}"
cd /var/www/bro
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 6. 安装依赖
echo -e "${YELLOW}[6/8] 安装 Python 依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 7. 创建日志目录
echo -e "${YELLOW}[7/8] 创建日志目录...${NC}"
sudo mkdir -p /var/log/bro
sudo chown ubuntu:ubuntu /var/log/bro

# 8. 初始化数据库
echo -e "${YELLOW}[8/8] 初始化数据库...${NC}"
mkdir -p instance
python3 -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('数据库初始化完成')
"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}基础环境部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "下一步: 配置 Gunicorn + Systemd + Nginx"
echo "运行: sudo ./setup_services.sh"