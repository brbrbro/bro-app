#!/bin/bash
# deploy-server.sh - 在服务器上执行的部署脚本
# 将此文件和 backend/ 目录上传到服务器后执行

set -e

echo "========================================"
echo "BRO APP 服务器部署脚本"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /var/www/bro

# 1. 备份现有数据
echo -e "${YELLOW}[1/6] 备份现有数据...${NC}"
if [ -f "instance/bro.db" ]; then
    cp instance/bro.db instance/bro.db.backup.$(date +%Y%m%d_%H%M%S)
    echo "数据库已备份"
fi

# 2. 停止服务
echo -e "${YELLOW}[2/6] 停止现有服务...${NC}"
sudo systemctl stop bro || true
sudo systemctl stop nginx || true

# 3. 更新代码
echo -e "${YELLOW}[3/6] 更新代码...${NC}"
# 假设代码已通过SCP上传到 /var/www/bro/
# 如果需要从本地复制，取消下面注释
# cp -r /path/to/uploaded/backend/* .

# 4. 安装/更新依赖
echo -e "${YELLOW}[4/6] 安装 Python 依赖...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. 更新数据库
echo -e "${YELLOW}[5/6] 更新数据库...${NC}"
python3 -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('数据库表已更新')
"

# 6. 启动服务
echo -e "${YELLOW}[6/6] 启动服务...${NC}"
sudo systemctl start nginx
sudo systemctl start bro
sleep 3

# 验证
if sudo systemctl is-active --quiet bro; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}部署成功！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "服务状态:"
    sudo systemctl status bro --no-pager
    echo ""
    echo "测试命令:"
    echo "  curl http://localhost:5001/api/health"
else
    echo -e "${RED}服务启动失败，请检查日志:${NC}"
    echo "  sudo tail -f /var/log/bro/error.log"
    exit 1
fi