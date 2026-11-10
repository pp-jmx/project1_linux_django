"""
============================================================================
  tests.py —— 示例测试（Django TestCase）
============================================================================

【本文件在项目中的位置与关系】
  - 测试对象：models.py（模型行为）、forms.py（表单校验）、views.py（视图响应）
  - 运行方式：python manage.py test learningnotes
  - 与生产代码隔离：Django 会为测试单独建一个临时数据库，跑完自动销毁，
    不会污染 db.sqlite3。

三个测试类分别对应 Django 的三层：
  ModelTests —— 数据层：模型方法、str、get_absolute_url、字段更新
  FormTests  —— 校验层：ModelForm 在不同输入下 is_valid() 的结果
  ViewTests  —— 视图层：HTTP 状态码、重定向、登录保护、副作用（浏览数 +1）
============================================================================
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from learningnotes.forms import NoteForm
from learningnotes.models import Category, Note, Tag


class ModelTests(TestCase):
    """模型层测试"""

    def setUp(self):
        """每个测试方法执行前都会调用，用来准备公共数据"""
        self.category = Category.objects.create(name='测试分类', order=1)
        self.note = Note.objects.create(
            title='一条测试笔记',
            content='内容' * 30,
            category=self.category,
            status='published',
        )

    def test_str_representation(self):
        """__str__ 决定对象在 Admin/shell 里的显示名"""
        self.assertEqual(str(self.category), '测试分类')
        self.assertEqual(str(self.note), '一条测试笔记')

    def test_get_absolute_url(self):
        """get_absolute_url 必须与 urls.py 里的 note_detail 一致"""
        expected = reverse('learningnotes:note_detail', kwargs={'pk': self.note.pk})
        self.assertEqual(self.note.get_absolute_url(), expected)

    def test_increment_view_count(self):
        """increment_view_count 应把浏览数 +1 并写回数据库"""
        self.note.increment_view_count()
        self.note.refresh_from_db()  # 从数据库重新读取，确认真的持久化了
        self.assertEqual(self.note.view_count, 1)

    def test_reverse_relation_note_count(self):
        """通过 related_name='notes' 反向查询该分类下的笔记数"""
        self.assertEqual(self.category.get_note_count(), 1)

    def test_many_to_many_tags(self):
        """多对多关系：一条笔记可挂多个标签"""
        t1 = Tag.objects.create(name='orm')
        t2 = Tag.objects.create(name='测试')
        self.note.tags.set([t1, t2])
        self.assertEqual(self.note.tags.count(), 2)
        self.assertIn(self.note, t1.notes.all())  # 反向查询


class FormTests(TestCase):
    """表单校验层测试"""

    def setUp(self):
        self.category = Category.objects.create(name='测试分类')

    def test_valid_draft(self):
        """合法的草稿应通过校验"""
        form = NoteForm(data={
            'title': '一个足够长的标题',
            'content': '这是一段足够长的正文内容。' * 3,
            'category': self.category.pk,
            'status': 'draft',
            'priority': 2,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_title_too_short_is_invalid(self):
        """标题少于 5 个字符应报错（forms.NoteForm.clean_title 的规则）"""
        form = NoteForm(data={
            'title': '短',
            'content': '这是一段足够长的正文内容。' * 3,
            'category': self.category.pk,
            'status': 'draft',
            'priority': 2,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_published_needs_long_content(self):
        """状态为 published 时正文少于 50 字应报错（跨字段校验 clean 的规则）"""
        form = NoteForm(data={
            'title': '一个足够长的标题',
            'content': '太短了',
            'category': self.category.pk,
            'status': 'published',
            'priority': 2,
        })
        self.assertFalse(form.is_valid())


class ViewTests(TestCase):
    """视图层测试"""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='pass12345')
        self.category = Category.objects.create(name='测试分类')
        self.note = Note.objects.create(
            title='已发布的笔记标题', content='正文' * 30,
            category=self.category, author=self.user, status='published',
        )

    def test_note_list_status_ok(self):
        """笔记列表页应正常返回 200，并包含笔记标题"""
        response = self.client.get(reverse('learningnotes:note_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '已发布的笔记标题')

    def test_note_detail_increments_view_count(self):
        """访问详情页应让浏览数 +1"""
        before = self.note.view_count
        response = self.client.get(self.note.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertEqual(self.note.view_count, before + 1)

    def test_create_requires_login(self):
        """未登录访问创建页应被重定向到登录页（@login_required）"""
        url = reverse('learningnotes:note_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('learningnotes:login'), response.url)
        self.assertIn(url, response.url)  # ?next= 带上原地址

    def test_create_when_logged_in(self):
        """登录后提交合法表单，应创建笔记并重定向到详情页"""
        self.client.force_login(self.user)
        response = self.client.post(reverse('learningnotes:note_create'), {
            'title': '登录后新建的笔记',
            'content': '正文内容' * 20,  # 已发布状态要求正文 ≥ 50 字
            'category': self.category.pk,
            'status': 'published',
            'priority': 2,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Note.objects.filter(title='登录后新建的笔记').exists())

    def test_search_view(self):
        """搜索视图：关键词命中时应返回结果"""
        response = self.client.get(reverse('learningnotes:search'), {'q': '已发布'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '已发布的笔记标题')
