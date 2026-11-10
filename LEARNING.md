# project1_linux_django · Django 学习地图

一个用于学习 **Django 精髓** 的小项目：留言板（`messageboard`，最小示例）+
学习笔记（`learningnotes`，完整示例）。每个文件顶部都有「本文件在项目中的位置与关系」注释。

---

## 1. 一次请求是怎么走完的

```
浏览器
  │  HTTP 请求 (GET /learning/notes/3/)
  ▼
project1/urls.py ──include──▶ learningnotes/urls.py   ← 路由层：URL → 视图
  │
  ▼
learningnotes/views.py                                 ← 逻辑层：拿到 request，决定干什么
  │   ├─ 读数据：models.py（ORM 生成 SQL）
  │   └─ 校验/写数据：forms.py（用户提交时）
  ▼
learningnotes/templates/.../*.html                     ← 表现层：把数据渲染成 HTML
  │
  ▼
HTTP 响应返回浏览器
```

**核心口诀**：`URL 找视图，视图用模型取数据 / 用表单校验数据，最后交给模板渲染`。

---

## 2. 目录结构与每个文件的职责

```
project1_linux_django/
├── manage.py                        Django 命令行入口（runserver/migrate/...）
├── db.sqlite3                       开发用数据库（迁移后自动生成表）
├── LEARNING.md                       本文件
│
├── project1/                        项目配置包（一个项目可以有多个 app）
│   ├── settings.py                  全局配置：INSTALLED_APPS / 数据库 / 模板 / 认证 / 媒体
│   ├── urls.py                       根路由：把 URL 前缀分发给各个 app
│   ├── wsgi.py / asgi.py             部署入口（学习阶段不用改）
│
├── messageboard/                    留言板 app —— 最小可运行示例
│   ├── models.py                    Message 模型
│   ├── views.py                     index 视图：显示 + 提交留言
│   ├── urls.py                      该 app 的路由
│   └── templates/messageboard/index.html
│
└── learningnotes/                   学习笔记 app —— 本项目的主体
    ├── settings 注册于 project1/settings.py 的 INSTALLED_APPS
    │
    ├── models.py                     【数据层】Category / Note / Tag / Attachment
    ├── views.py                      【逻辑层】FBV + CBV + 搜索 + JSON API
    ├── forms.py                      【校验层】ModelForm / Form / 自定义校验 / FormSet
    ├── urls.py                       【路由层】URL 模式、命名空间、反向解析
    ├── admin.py                      【后台】模型在 Admin 中的展示与操作配置
    ├── tests.py                      【测试】模型 / 表单 / 视图三层的示例测试
    │
    ├── migrations/                   数据库迁移文件（models 变更的历史记录）
    │
    ├── templates/
    │   ├── learningnotes/
    │   │   ├── base.html             模板继承的父模板（导航/样式/消息）
    │   │   ├── _pagination.html      可复用分页片段（include）
    │   │   ├── index.html            首页：统计 + 最新 + 热门
    │   │   ├── note_list.html        笔记列表（筛选 + 搜索 + 分页）
    │   │   ├── note_detail.html      笔记详情
    │   │   ├── note_form.html        新建/编辑共用表单页
    │   │   ├── note_confirm_delete.html 删除确认页
    │   │   ├── category_list.html    分类列表（CBV ListView）
    │   │   ├── category_detail.html  分类详情（CBV DetailView）
    │   │   └── search.html           搜索页（自定义 CBV）
    │   └── registration/
    │       └── login.html            登录页（auth 视图的默认模板名）
    │
    └── management/commands/
        └── seed_notes.py             自定义命令：一键灌入演示数据
```

---

## 3. 文件之间的关系（谁依赖谁）

| 文件 | 依赖 / 被依赖 | 说明 |
|---|---|---|
| `project1/settings.py` | 被全项目依赖 | 注册 app、配置数据库/模板/认证/媒体 |
| `project1/urls.py` | 依赖各 app 的 `urls.py` | 用 `include()` 做 URL 分发 |
| `learningnotes/urls.py` | 依赖 `views.py` | 把 URL 模式映射到视图，`app_name` 决定命名空间 |
| `learningnotes/views.py` | 依赖 `models.py`、`forms.py`、模板 | 三者之间的“协调者” |
| `learningnotes/models.py` | 被 `views/forms/admin/tests` 依赖 | 数据的唯一来源 |
| `learningnotes/forms.py` | 依赖 `models.py` | 由模型自动生成字段，做校验 |
| `learningnotes/admin.py` | 依赖 `models.py` | 注册后即可在 `/admin/` 管理数据 |
| `templates/base.html` | 被所有页面模板 `extends` | 公共布局 |
| `templates/learningnotes/*.html` | 依赖 `views.py` 传来的 `context` | 变量名要和视图里的 `context` 对上 |
| `tests.py` | 依赖 `models/forms/views` | 验证三层行为 |

**反向解析（`{% url %}` 与 `reverse()`）是连接点**：模板和视图都靠 `name` 找 URL，
所以 `urls.py` 里每个 `name=` 都是它们之间的“约定”。

---

## 4. 按 Django 精髓的阅读顺序

1. **模型与 ORM** → `learningnotes/models.py`
2. **迁移** → `learningnotes/migrations/0001_initial.py`（了解 `makemigrations`/`migrate`）
3. **路由与命名空间** → `learningnotes/urls.py` + `project1/urls.py`
4. **视图：FBV 与 CBV** → `learningnotes/views.py`
5. **表单与校验** → `learningnotes/forms.py`
6. **模板继承与标签** → `templates/learningnotes/base.html` → 各页面
7. **Admin** → `learningnotes/admin.py`，然后登录 `/admin/` 体验
8. **认证** → `settings.py` 的 LOGIN_* + `templates/registration/login.html` + `@login_required`
9. **测试** → `learningnotes/tests.py`
10. **管理命令** → `learningnotes/management/commands/seed_notes.py`

---

## 5. 快速开始

```bash
cd project1_linux_django
source venv/bin/activate

python manage.py migrate             # 建表（首次或模型变更后）
python manage.py seed_notes          # 灌入演示数据 + 演示账号 demo/demo12345
python manage.py createsuperuser     # 另建一个后台管理员（可选）
python manage.py runserver
```

- 前台首页：<http://127.0.0.1:8000/learning/>
- 登录：<http://127.0.0.1:8000/learning/accounts/login/>（demo / demo12345）
- 后台：<http://127.0.0.1:8000/admin/>
- 留言板：<http://127.0.0.1:8000/>

运行测试：

```bash
python manage.py test learningnotes
```

---

## 6. 动手练习（把知识变成手感）

1. 给 `Note` 加一个 `is_featured` 布尔字段，跑通 `makemigrations` + `migrate`，在 Admin 里勾选。
2. 在 `notes_by_tag` 路由（`urls.py` 里已注释示例）实现“按标签筛选”的视图与模板。
3. 把 `note_list` 的筛选逻辑抽到 `NoteSearchForm`（`forms.py` 里已备好），体会 Form 处理 GET 参数。
4. 给 `Note` 加 slug 字段并在 URL 里用 `<slug:slug>`，理解 URL 参数类型。
5. 给写操作加权限：只允许作者本人编辑/删除（`views.py` 里已有雏形）。
