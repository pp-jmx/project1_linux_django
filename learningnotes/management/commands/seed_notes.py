"""
============================================================================
  seed_notes —— 自定义管理命令（management command）
============================================================================

【本文件在项目中的位置与关系】
  - 调用方式：python manage.py seed_notes
  - 它依赖 models.py 里的 Category / Tag / Note（这是它与 ORM 层的唯一关系）
  - 生成的“已发布”笔记，会被 views.note_list / index 等视图查询并渲染到模板
  - 它是纯数据准备工具，不参与请求-响应流程

Django 约定：
  <app>/management/commands/<命令名>.py 会被 manage.py 自动发现，
  文件名就是命令名。类必须继承 BaseCommand，并实现 handle()。

为什么需要它？
  刚 migrate 完数据库是空的，页面看不到效果。这个命令用 get_or_create
  幂等地灌入演示数据，可反复执行而不会产生重复记录。
============================================================================
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from learningnotes.models import Category, Tag, Note


class Command(BaseCommand):
    help = "生成演示用的分类 / 标签 / 笔记（可重复执行，不会重复插入）"

    def add_arguments(self, parser):
        """声明可选命令行参数：python manage.py seed_notes --reset"""
        parser.add_argument(
            '--reset',
            action='store_true',
            help='先删除演示账号 demo 名下的笔记，再重新生成',
        )

    def handle(self, *args, **options):
        """命令的真正入口：handle() 里的代码就是命令执行的逻辑"""

        # 1) 演示用户（登录用），get_or_create 保证幂等
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@example.com'},
        )
        if created:
            user.set_password('demo12345')
            user.save()
            self.stdout.write(self.style.SUCCESS('已创建演示用户 demo / demo12345'))
        else:
            self.stdout.write('演示用户 demo 已存在，跳过创建')

        if options['reset']:
            deleted, _ = Note.objects.filter(author=user).delete()
            self.stdout.write(self.style.WARNING(f'--reset：已删除 demo 的 {deleted} 条旧记录'))

        # 2) 分类：name 唯一，直接 get_or_create
        categories_data = [
            ('Django 基础', 'MTV、ORM、URL、模板的入门知识', 1),
            ('Django 进阶', '表单、类视图、Admin、中间件', 2),
            ('Python 拾遗', '与 Django 相关的 Python 技巧', 3),
        ]
        categories = {}
        for name, desc, order in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'order': order, 'is_active': True},
            )
            categories[name] = cat

        # 3) 标签：模型有 color 字段，顺便演示 color 字段的用途
        tags_data = [
            ('orm', '#0ea5e9'),
            ('模板', '#22c55e'),
            ('表单', '#f59e0b'),
            ('类视图', '#8b5cf6'),
            ('最佳实践', '#ef4444'),
        ]
        tags = {}
        for name, color in tags_data:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={'color': color})
            tags[name] = tag

        # 4) 笔记：每条记录挂到某个分类、作者是 demo，并关联若干标签
        notes_data = [
            {
                'title': 'Django 的 MTV 模式是什么',
                'content': (
                    'Django 把一次请求拆成 Model（数据）、Template（展示）、View（逻辑）三层。\n\n'
                    '请求先经过 URLconf 找到 View，View 通过 ORM 从 Model 取数据，'
                    '再交给 Template 渲染成 HTML 返回。理解这条链路，就理解了 Django 的主干。'
                ),
                'category': 'Django 基础',
                'tags': ['orm', '模板'],
                'priority': 3,
            },
            {
                'title': 'QuerySet 的惰性求值',
                'content': (
                    'QuerySet 在你真正迭代、切片或打印之前不会碰数据库，这叫“惰性求值”。\n\n'
                    '正因如此，才可以把 filter() 一层层串起来，Django 只会在最后拼成一条 SQL。'
                    '配合 select_related / prefetch_related 还能避免 N+1 查询。'
                ),
                'category': 'Django 基础',
                'tags': ['orm', '最佳实践'],
                'priority': 2,
            },
            {
                'title': '函数视图还是类视图',
                'content': (
                    'FBV（函数视图）直白、易读，适合逻辑简单的页面；'
                    'CBV（类视图）通过继承复用功能，ListView/CreateView 等通用视图能省掉大量样板代码。\n\n'
                    '建议：先写 FBV 把逻辑理顺，需要复用或标准 CRUD 时再换成 CBV。'
                ),
                'category': 'Django 进阶',
                'tags': ['类视图', '最佳实践'],
                'priority': 2,
            },
            {
                'title': '表单校验的三个层次',
                'content': (
                    '第一层是字段自身的约束（max_length、required）；'
                    '第二层是字段级校验 clean_<field>；'
                    '第三层是跨字段校验 clean()。\n\n'
                    '把校验写在 Form/ModelForm 里，视图就只负责“根据 is_valid() 分支”，职责清晰。'
                ),
                'category': 'Django 进阶',
                'tags': ['表单'],
                'priority': 2,
            },
            {
                'title': 'Admin 为什么是 Django 的杀手锏',
                'content': (
                    '只要注册模型，Django 就能自动生成增删改查后台。'
                    '再配合 list_display、list_filter、search_fields、inlines，'
                    '几行配置就能得到一个可用的运营工具。\n\n'
                    '很多项目在业务后台成熟之前，都先靠 Admin 顶着。'
                ),
                'category': 'Django 进阶',
                'tags': ['最佳实践'],
                'priority': 1,
            },
            {
                'title': 'slugify 与 URL 友好字符串',
                'content': (
                    'slugify 把「Hello World 你好」这类文本转成 URL 友好的字符串。'
                    '虽然本项目 URL 用主键 <int:pk>，但在需要可读 URL 时它很有用。'
                ),
                'category': 'Python 拾遗',
                'tags': ['最佳实践'],
                'priority': 1,
            },
        ]

        created_count = 0
        for item in notes_data:
            note, created = Note.objects.get_or_create(
                title=item['title'],
                defaults={
                    'content': item['content'],
                    'category': categories[item['category']],
                    'author': user,
                    'status': 'published',
                    'priority': item['priority'],
                },
            )
            if created:
                created_count += 1
                # 设置多对多关系要在对象保存之后
                note.tags.set([tags[t] for t in item['tags']])

        self.stdout.write(self.style.SUCCESS(
            f'完成：新增 {created_count} 条笔记，'
            f'共 {Note.objects.filter(status="published").count()} 条已发布笔记。'
        ))
        self.stdout.write('登录页：/learning/accounts/login/  账号 demo / demo12345')
