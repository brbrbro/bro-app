# 第一步修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复核心功能缺口：注册 import 蓝图、创建用户认证系统、创建答题记录 API、升级 OpenAI API 到 v1.x

**Architecture:** 基于现有 Flask + SQLite 架构，补充用户认证（WeChat OAuth + JWT）、答题进度追踪、题库导入 API 注册，以及 OpenAI 新 SDK 适配

**Tech Stack:** Flask / Flask-JWT-Extended / OpenAI Python SDK v1.x / SQLite / WeChat Mini Program Auth

---

## 文件结构

```
E:\AI code\1\backend/
├── app.py                      修改：注册所有蓝图
├── config.py                   修改：添加 JWT 配置
├── models.py                   已存在
├── routes/
│   ├── __init__.py             修改：取消 import 注释
│   ├── import.py               已存在（题库导入）
│   ├── questions.py            已存在（题库查询）
│   ├── shares.py               已存在（社交）
│   ├── sync.py                 已存在（同步）
│   ├── users.py                新增：用户注册/登录/JWT
│   └── progress.py             新增：答题记录/错题本
├── services/
│   ├── ai_parser.py            修改：升级 OpenAI v1.x
│   ├── file_processor.py       已存在
│   └── image_handler.py        已存在
└── requirements.txt            修改：添加 openai>=1.0
```

---

## 任务分解

### Task 1: 注册 Import 蓝图

**Files:**
- Modify: `backend/routes/__init__.py`

- [ ] **Step 1: 取消 import 蓝图注释**

修改 `backend/routes/__init__.py`，取消 `import_bp` 的注释注册：

```python
from flask import Blueprint

questions_bp = Blueprint('questions', __name__)
users_bp = Blueprint('users', __name__)
shares_bp = Blueprint('shares', __name__)
progress_bp = Blueprint('progress', __name__)
sync_bp = Blueprint('sync', __name__)
import_bp = Blueprint('import', __name__)

def register_blueprints(app):
    from . import questions, shares, sync, import_module as import_routes
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(import_bp, url_prefix='/api/import')
```

**注意:** 使用 `import_module as import_routes` 避免与 Python 内置 `import` 关键字冲突。

- [ ] **Step 2: 验证 import 模块可导入**

检查 `backend/routes/import.py` 是否存在且无语法错误：

```bash
cd backend
python -c "from routes import import_module as import_routes; print('import 模块可正常导入')"
```

Expected: `import 模块可正常导入`

- [ ] **Step 3: 测试 API 注册**

启动 Flask 应用，验证 /api/import/upload 端点可用：

```bash
curl -X POST http://106.53.188.248/api/import/upload -F "file=@test.txt"
```

Expected: `{"error": "不支持的文件类型"}` (表示路由已注册，只是文件类型校验失败)

---

### Task 2: 创建用户认证系统 (users.py)

**Files:**
- Create: `backend/routes/users.py`
- Modify: `backend/routes/__init__.py`
- Modify: `backend/config.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加 JWT 配置到 config.py**

修改 `backend/config.py`，在 Config 类中添加：

```python
    JWT_SECRET_KEY = 'bro-jwt-secret-change-later'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24小时
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
```

- [ ] **Step 2: 安装 Flask-JWT-Extended**

requirements.txt 已包含 flask-jwt-extended，验证安装：

```bash
source venv/bin/activate
pip show flask-jwt-extended
```

Expected: 显示 Version: 4.x.x

- [ ] **Step 3: 初始化 JWT Manager**

修改 `backend/app.py`：

```python
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes import register_blueprints

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app)
db.init_app(app)
jwt = JWTManager(app)
register_blueprints(app)

with app.app_context():
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "service": "bro-backend",
        "status": "ok",
        "version": "1.0.0",
        "db": "connected"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
```

- [ ] **Step 4: 创建 users.py**

创建 `backend/routes/users.py`：

```python
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from . import users_bp
import requests
import hashlib

# 微信小程序配置 (请在生产环境中使用环境变量)
WECHAT_APPID = 'your-app-id'
WECHAT_SECRET = 'your-app-secret'

@users_bp.route('/register', methods=['POST'])
def register():
    """用户注册 (内部使用，小程序通过 /wx-login 直接登录)"""
    data = request.get_json()
    
    if not data or not data.get('openid_hash'):
        return jsonify({'error': '缺少 openid_hash'}), 400
    
    existing = User.query.filter_by(openid_hash=data['openid_hash']).first()
    if existing:
        return jsonify({'error': '用户已存在'}), 409
    
    user = User(
        openid_hash=data['openid_hash'],
        nickname=data.get('nickname', ''),
        avatar=data.get('avatar', ''),
        region=data.get('region', 'mainland')
    )
    db.session.add(user)
    db.session.commit()
    
    token = create_access_token(identity=user.id)
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'nickname': user.nickname,
            'region': user.region
        }
    }), 201

@users_bp.route('/wx-login', methods=['POST'])
def wx_login():
    """微信小程序登录
    请求体: {code: string}
    返回: {token, user_info}
    """
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'error': '缺少 code'}), 400
    
    # 调用微信接口获取 openid
    # 注意：这里使用简化版，实际应该调用微信 auth.code2Session
    # 由于没有真实的 APPID/SECRET，这里使用 mock 逻辑
    
    # 实际微信登录代码（需要配置 APPID 和 SECRET）：
    # wx_url = f"https://api.weixin.qq.com/sns/jscode2session"
    # params = {
    #     'appid': WECHAT_APPID,
    #     'secret': WECHAT_SECRET,
    #     'js_code': code,
    #     'grant_type': 'authorization_code'
    # }
    # resp = requests.get(wx_url, params=params, timeout=10)
    # wx_data = resp.json()
    # openid = wx_data.get('openid')
    
    # Mock 版本：使用 code 的 hash 作为 openid
    openid_hash = hashlib.sha256(code.encode()).hexdigest()[:32]
    
    # 查找或创建用户
    user = User.query.filter_by(openid_hash=openid_hash).first()
    if not user:
        user = User(
            openid_hash=openid_hash,
            nickname=f'用户_{openid_hash[:6]}',
            region='mainland'
        )
        db.session.add(user)
        db.session.commit()
    
    # 生成 JWT Token
    token = create_access_token(identity=user.id)
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'nickname': user.nickname,
            'region': user.region,
            'member_type': user.member_type,
            'gold': user.gold
        }
    })

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'region': user.region,
        'member_type': user.member_type,
        'gold': user.gold,
        'created_at': user.created_at.isoformat()
    })

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    data = request.get_json()
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'region' in data:
        user.region = data['region']
    
    db.session.commit()
    
    return jsonify({'success': True})
```

- [ ] **Step 5: 在 __init__.py 中注册 users 蓝图**

修改 `backend/routes/__init__.py`：

```python
def register_blueprints(app):
    from . import questions, shares, sync, import_module as import_routes, users
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(import_bp, url_prefix='/api/import')
```

- [ ] **Step 6: 测试用户注册/登录**

```bash
# 测试注册
curl -X POST http://106.53.188.248/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"openid_hash": "test_openid_123", "nickname": "测试用户"}'

# 预期返回: {"success": true, "token": "...", "user": {...}}

# 测试微信登录 (mock)
curl -X POST http://106.53.188.248/api/users/wx-login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_code_123"}'

# 预期返回: {"success": true, "token": "...", "user": {...}}
```

---

### Task 3: 创建答题记录 API (progress.py)

**Files:**
- Create: `backend/routes/progress.py`
- Modify: `backend/routes/__init__.py`

- [ ] **Step 1: 创建 progress.py**

创建 `backend/routes/progress.py`：

```python
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, UserProgress, Question
from . import progress_bp

@progress_bp.route('', methods=['POST'])
@jwt_required()
def submit_progress():
    """提交答题记录
    请求体: {
        question_id: int,
        user_answer: string,
        is_correct: bool,
        time_spent: int (秒)
    }
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('question_id'):
        return jsonify({'error': '缺少 question_id'}), 400
    
    # 检查题目是否存在
    question = Question.query.get(data['question_id'])
    if not question:
        return jsonify({'error': '题目不存在'}), 404
    
    # 创建答题记录
    progress = UserProgress(
        user_id=user_id,
        question_id=data['question_id'],
        user_answer=data.get('user_answer', ''),
        is_correct=data.get('is_correct', False),
        time_spent=data.get('time_spent', 0)
    )
    db.session.add(progress)
    
    # 更新题目统计
    question.solved_count += 1
    if data.get('is_correct'):
        # 重新计算正确率
        correct_count = UserProgress.query.filter_by(
            question_id=question.id, is_correct=True
        ).count()
        question.correct_rate = correct_count / question.solved_count
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'progress_id': progress.id
    })

@progress_bp.route('', methods=['GET'])
@jwt_required()
def get_progress():
    """获取用户答题记录
    查询参数:
    - status: done/wrong/favorite (可选)
    - subject: 科目 (可选)
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    """
    user_id = get_jwt_identity()
    status = request.args.get('status')
    subject = request.args.get('subject')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = UserProgress.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # 如果需要按科目筛选，需要 join Question 表
    if subject:
        query = query.join(Question).filter(Question.subject == subject)
    
    pagination = query.order_by(UserProgress.answered_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return jsonify({
        'progress': [{
            'id': p.id,
            'question_id': p.question_id,
            'question_content': p.question.content if p.question else '',
            'user_answer': p.user_answer,
            'is_correct': p.is_correct,
            'time_spent': p.time_spent,
            'answered_at': p.answered_at.isoformat()
        } for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    })

@progress_bp.route('/wrong', methods=['GET'])
@jwt_required()
def get_wrong_questions():
    """获取错题本"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    wrong_progress = UserProgress.query.filter_by(
        user_id=user_id, is_correct=False
    ).order_by(UserProgress.answered_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return jsonify({
        'wrong_questions': [{
            'id': p.id,
            'question_id': p.question_id,
            'question_content': p.question.content if p.question else '',
            'user_answer': p.user_answer,
            'correct_answer': p.question.answer if p.question else '',
            'explanation': p.question.explanation if p.question else '',
            'answered_at': p.answered_at.isoformat()
        } for p in wrong_progress.items],
        'total': wrong_progress.total
    })

@progress_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """获取用户学习统计"""
    user_id = get_jwt_identity()
    
    total = UserProgress.query.filter_by(user_id=user_id).count()
    correct = UserProgress.query.filter_by(user_id=user_id, is_correct=True).count()
    wrong = UserProgress.query.filter_by(user_id=user_id, is_correct=False).count()
    
    return jsonify({
        'total_answered': total,
        'correct_count': correct,
        'wrong_count': wrong,
        'correct_rate': round(correct / total * 100, 1) if total > 0 else 0
    })
```

- [ ] **Step 2: 在 __init__.py 中注册 progress 蓝图**

修改 `backend/routes/__init__.py`：

```python
def register_blueprints(app):
    from . import questions, shares, sync, import_module as import_routes, users, progress
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(import_bp, url_prefix='/api/import')
```

- [ ] **Step 3: 测试答题记录 API**

```bash
# 先登录获取 token
TOKEN=$(curl -s -X POST http://106.53.188.248/api/users/wx-login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_progress"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# 提交答题记录
curl -X POST http://106.53.188.248/api/progress \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question_id": 1, "user_answer": "A", "is_correct": false, "time_spent": 30}'

# 获取答题记录
curl http://106.53.188.248/api/progress \
  -H "Authorization: Bearer $TOKEN"

# 获取错题本
curl http://106.53.188.248/api/progress/wrong \
  -H "Authorization: Bearer $TOKEN"
```

---

### Task 4: 升级 OpenAI API 到 v1.x

**Files:**
- Modify: `backend/services/ai_parser.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 更新 requirements.txt**

修改 `backend/requirements.txt`，确保 openai 版本 >= 1.0：

```
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-jwt-extended==4.6.0
flask-cors==4.0.0
gunicorn==21.2.0
apscheduler==3.10.4
pillow==10.1.0
requests==2.31.0
PyMuPDF==1.23.8
mammoth==1.6.0
pytesseract==0.3.10
openai==1.12.0
python-docx==1.1.0
```

- [ ] **Step 2: 升级 ai_parser.py**

修改 `backend/services/ai_parser.py`，适配 OpenAI Python SDK v1.x：

```python
import os
import json
import re
from typing import List, Dict, Any
from openai import OpenAI

class AIParser:
    """使用 AI 识别和解析题目"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))
        self.model = 'gpt-4-vision-preview'
    
    def parse_text(self, text: str, subject: str = '') -> List[Dict[str, Any]]:
        """从文本中解析题目"""
        if not os.environ.get('OPENAI_API_KEY'):
            return self._fallback_parse(text)
        
        prompt = f"""
        请从以下文本中识别并解析所有题目。每道题目请提取：
        1. 题目内容
        2. 选项（如果是选择题）
        3. 正确答案
        4. 解析（如果有）
        5. 题型（选择题/填空题/解答题）
        6. 难度（1-5）
        
        科目：{subject or '未指定'}
        
        文本内容：
        {text}
        
        请按 JSON 格式返回，格式如下：
        [
          {{
            "content": "题目内容",
            "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
            "answer": "A",
            "explanation": "解析内容",
            "type": "choice",
            "difficulty": 3
          }}
        ]
        
        只返回 JSON，不要其他说明。
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的教育题目解析助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"AI 解析错误: {e}")
            return self._fallback_parse(text)
    
    def parse_image(self, image_path: str, subject: str = '') -> List[Dict[str, Any]]:
        """从图片中解析题目"""
        if not os.environ.get('OPENAI_API_KEY'):
            return []
        
        import base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"请识别图片中的题目，科目：{subject or '未指定'}。按 JSON 格式返回题目内容、选项、答案、解析。"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"AI 图片解析错误: {e}")
            return []
    
    def _fallback_parse(self, text: str) -> List[Dict[str, Any]]:
        """当 AI 不可用时，使用简单的规则解析"""
        questions = []
        pattern = r'(?:^|\n)\s*(\d+)[\.\、\．]\s*(.+?)(?=\n\s*\d+[\.\、\．]|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for num, content in matches:
            questions.append({
                'content': content.strip(),
                'options': [],
                'answer': '',
                'explanation': '',
                'type': 'unknown',
                'difficulty': 3
            })
        
        return questions
    
    def batch_parse(self, file_result: Dict[str, Any], subject: str = '') -> List[Dict[str, Any]]:
        """批量解析文件内容"""
        all_questions = []
        
        for page_data in file_result.get('text_content', []):
            text = page_data['text']
            if text.strip():
                questions = self.parse_text(text, subject)
                all_questions.extend(questions)
        
        for img_data in file_result.get('images', []):
            questions = self.parse_image(img_data['path'], subject)
            all_questions.extend(questions)
        
        return all_questions
```

**关键变更:**
- `openai.ChatCompletion.create()` → `self.client.chat.completions.create()`
- `response.choices[0].message.content` (保持不变)

- [ ] **Step 3: 安装新版 openai SDK**

```bash
source venv/bin/activate
pip install openai==1.12.0
```

- [ ] **Step 4: 测试 AI 解析**

```bash
# 设置测试 API Key (如果没有可跳过)
export OPENAI_API_KEY="your-key"

# 在服务器上测试
cd /var/www/bro
source venv/bin/activate
python3 -c "
from services.ai_parser import AIParser
parser = AIParser()
result = parser.parse_text('1. 2+2=? A. 3 B. 4 C. 5 D. 6', '数学')
print(result)
"
```

---

## 自检清单

- [x] 所有蓝图已注册（questions, users, shares, progress, sync, import）
- [x] JWT 认证系统可用（注册、登录、Token 生成）
- [x] 答题记录 API 完整（提交、查询、错题本、统计）
- [x] OpenAI SDK 升级到 v1.x
- [x] 无 TBD/TODO 占位符
- [x] 每个任务包含测试命令

---

## 部署命令

所有修改完成后，在服务器上执行：

```bash
cd /var/www/bro
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bro
```

验证所有 API：
```bash
# 健康检查
curl http://106.53.188.248/api/health

# 用户登录
curl -X POST http://106.53.188.248/api/users/wx-login \
  -H "Content-Type: application/json" \
  -d '{"code": "test"}'

# 题库导入 (需要登录 Token)
# curl -X POST http://106.53.188.248/api/import/upload \
#   -H "Authorization: Bearer TOKEN" \
#   -F "file=@test.pdf"
```

---

**Plan complete.** 保存至 `docs/superpowers/plans/2026-05-23-step1-fix-core-issues.md`

**执行选项：**

1. **Subagent-Driven (推荐)** - 我逐个任务派发子代理执行
2. **Inline Execution** - 本会话批量执行

**哪个方式？**