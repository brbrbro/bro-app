# BRO APP MVP 设计规范

**日期：** 2026-05-20
**版本：** 1.0
**状态：** 完成

---

## 1. 项目概述

**项目名称：** BRO APP
**类型：** 微信小程序（教育类刷题学习 + 轻度社交）
**目标用户：** 高考/DSE 应试备考学生，及日常练习用户
**核心定位：** 刷题学习为主，轻社交为辅

---

## 2. 核心功能

### 2.1 题库模块（核心）

| 功能 | 说明 |
|------|------|
| 题库浏览 | 按 地区(内地/香港) → 科目 → 年级 → 考纲 → 知识点 逐级筛选 |
| 刷题练习 | 顺序练习 / 随机挑战 / 错题本 |
| 答题反馈 | 即时判分 + 答案解析 + 笔记记录 |
| 题目类型 | 选择题、填空题、解答题 |
| 难度等级 | 1-5 级 |

### 2.2 轻社交模块（辅助）

| 功能 | 说明 |
|------|------|
| 笔记分享 | 关联题目发布笔记，支持文字+图片 |
| 互动 | 点赞 / 评论 |
| 解题分享 | 解题思路可被引用 |
| 内容审核 | 管理员后台审核UGC内容 |

### 2.3 数据同步策略

| 策略 | 说明 |
|------|------|
| 本地优先 | 学习数据存微信小程序本地 storage |
| 手动同步 | 用户主动点击"同步"按钮上传/下载数据 |
| 未登录运行 | 未登录时纯本地运行，登录后云端同步 |

### 2.4 AI 题库扩充（后台工具）

| 功能 | 说明 |
|------|------|
| 种子题库 | 开发者按科目提供的小题库 |
| UGC 入库 | 用户上传题目经审核后作为 AI 学习素材 |
| AI 生成 | 后台运行脚本，学习种子题库后生成新题目 |
| 人工复核 | AI 生成题目需人工审核再入库 |

---

## 3. 数据模型

### 3.1 题库 (Question)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| region | String | 地区 (mainland/hk) |
| subject | String | 科目 |
| grade | String | 年级/学期 |
| syllabus | String | 考纲标签 |
| knowledge_point | String | 知识点标签 |
| type | String | 题目类型 (choice/blank/comprehensive) |
| difficulty | Integer | 难度 (1-5) |
| content | Text | 题目内容 |
| answer | Text | 答案 |
| explanation | Text | 解析 |
| options | Text | 选项 JSON (选择题) |
| solved_count | Integer | 解答次数 |
| correct_rate | Float | 正确率 |
| source | String | 来源 (seed/ugc/ai) |
| status | String | 状态 (pending_review/approved/rejected) |
| created_at | DateTime | 创建时间 |

### 3.2 用户进度 (UserProgress)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID (外键) |
| question_id | Integer | 题目ID (外键) |
| status | String | 状态 (favorite/wrong/done) |
| user_answer | Text | 用户答案 |
| is_correct | Boolean | 是否正确 |
| time_spent | Integer | 用时(秒) |
| answered_at | DateTime | 答题时间 |

### 3.3 笔记/分享 (Share)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID (外键) |
| question_id | Integer | 关联题目ID (可空) |
| type | String | 类型 (note/question/solution) |
| content | Text | 内容 |
| images | Text | 图片 JSON |
| like_count | Integer | 点赞数 |
| comment_count | Integer | 评论数 |
| status | String | 状态 |
| created_at | DateTime | 创建时间 |

### 3.4 用户 (User)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| openid_hash | String | 微信 OpenID 哈希 |
| nickname | String | 昵称 |
| avatar | String | 头像 |
| region | String | 地区偏好 (mainland/hk) |
| member_type | String | 会员类型 (free/normal/premium) |
| gold | Integer | 金币 |
| created_at | DateTime | 创建时间 |

---

## 4. 技术架构

### 4.1 技术栈

| 层级 | 技术 |
|------|------|
| 小程序端 | 微信小程序原生框架 |
| 后端 | Flask + SQLite (现有服务器 106.53.188.248) |
| 存储 | 本地 storage + 云端 SQLite |

### 4.2 项目结构

```
小程序/
├── pages/
│   ├── index/          首页（题库入口）
│   ├── practice/      刷题页面
│   ├── wrongbook/     错题本
│   ├── share/         笔记社区
│   ├── profile/       个人中心
│   └── sync/          数据同步
├── components/        公共组件
├── utils/
│   ├── api.js        API 调用
│   ├── storage.js    本地存储
│   └── sync.js       同步逻辑
└── app.js            应用入口

服务器/
├── app.py            Flask 应用
├── models.py         数据模型
├── routes/          API 路由
│   ├── questions.py  题库 API
│   ├── users.py      用户 API
│   └── shares.py     社交 API
└── scripts/
    └── ai_generator.py  AI 题库生成工具（后台独立运行）
```

### 4.3 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/auth/login | POST | 微信登录 |
| /api/questions | GET | 获取题目列表 |
| /api/questions/:id | GET | 获取题目详情 |
| /api/practice/submit | POST | 提交答题结果 |
| /api/progress | GET | 获取用户进度 |
| /api/shares | GET/POST | 获取/发布笔记 |
| /api/sync/upload | POST | 上传本地数据 |
| /api/sync/download | GET | 下载云端数据 |

---

## 5. MVP 范围

### 第一阶段交付

| 模块 | 功能点 |
|------|--------|
| 题库浏览 | 按地区→科目→年级→知识点筛选 |
| 刷题练习 | 顺序练习 + 即时判分解析 |
| 错题本 | 自动收集错题 |
| 笔记发布 | 关联题目发布笔记 |
| 笔记互动 | 点赞 + 评论 |
| 数据同步 | 本地存储 + 手动同步按钮 |
| 后台管理 | 管理员审核 H5 页面 |

### 暂不包含

- AI 题库生成工具（Phase 2）
- 金币悬赏功能（Phase 2）
- 会员系统（Phase 2）

---

## 6. 法律与合规

- 用户数据存储需符合微信小程序隐私政策
- UGC 内容需审核机制
- AI 生成题目需标注来源
- 服务器部署需备案（内地）/ 合规（香港）