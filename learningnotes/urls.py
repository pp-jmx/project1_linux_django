"""
============================================================================
  urls.py —— 路由层：URL 模式 → 视图
============================================================================
【职责】把浏览器地址映射到 views.py 里的视图，并用 app_name 建立命名空间。
【关系】被 project1/urls.py 用 include('learningnotes.urls') 挂到 /learning/ 下；
        本文件依赖 views.py；模板/视图通过 name 反向解析，所以 name 是三方约定。
【重要】因为声明了 app_name='learningnotes'，反向解析必须写成
        'learningnotes:note_detail'，否则会 NoReverseMatch。
============================================================================

Django URL配置 (URLconf) - Django的路由系统

URL配置定义URL模式与视图的映射关系。
Django根据URL配置来决定调用哪个视图函数/类。

核心概念：
1. path() - 定义URL模式（精确匹配）
2. re_path() - 使用正则表达式定义URL模式
3. include() - 包含其他URL配置
4. URL参数 - 从URL中捕获参数传递给视图
5. URL命名 - 为URL起名字，方便反向解析
"""

from django.urls import path, re_path, include
from . import views

"""
app_name - 应用命名空间

用于区分不同应用中的同名URL
在模板中使用：{% url 'learningnotes:note_list' %}
在视图中使用：reverse('learningnotes:note_list')
"""
app_name = 'learningnotes'

urlpatterns = [
    # ==================== 首页 ====================
    # path()的参数：
    # 1. route: URL模式（字符串）
    # 2. view: 视图函数或类
    # 3. kwargs: 额外的参数字典（可选）
    # 4. name: URL名称，用于反向解析（可选但强烈建议）

    path('', views.index, name='index'),

    # ==================== 笔记相关 ====================

    # 笔记列表
    # URL: /notes/
    path('notes/', views.note_list, name='note_list'),

    # 笔记详情 - 使用<类型:参数名>捕获URL参数
    # <int:pk>: 捕获整数类型的参数，参数名为pk
    # URL: /notes/123/ -> pk=123
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),

    # 创建笔记
    # URL: /notes/create/
    path('notes/create/', views.note_create, name='note_create'),

    # 编辑笔记
    # URL: /notes/123/edit/
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),

    # 删除笔记
    # URL: /notes/123/delete/
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),

    # ==================== 使用类视图 ====================

    # 类视图需要调用as_view()方法转换为视图函数
    # ListView - 列表视图
    path('categories/', views.CategoryListView.as_view(), name='category_list'),

    # DetailView - 详情视图
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),

    # CreateView - 创建视图（使用类视图）
    path('notes/new/', views.NoteCreateView.as_view(), name='note_create_cbv'),

    # UpdateView - 更新视图
    path('notes/<int:pk>/update/', views.NoteUpdateView.as_view(), name='note_update'),

    # DeleteView - 删除视图
    path('notes/<int:pk>/remove/', views.NoteDeleteView.as_view(), name='note_delete_cbv'),

    # ==================== 搜索功能 ====================

    # 搜索
    # URL: /search/?q=关键词
    path('search/', views.NoteSearchView.as_view(), name='search'),

    # ==================== API接口 ====================

    # API笔记列表
    # URL: /api/notes/
    path('api/notes/', views.note_api_list, name='api_note_list'),

    # API笔记详情
    # URL: /api/notes/123/
    path('api/notes/<int:pk>/', views.note_api_detail, name='api_note_detail'),

    # ==================== 认证（Django 自带）====================
    # include('django.contrib.auth.urls') 会一次性提供这些 URL（用 name 反向解析）：
    #   login / logout / password_change / password_change_done
    #   password_reset / password_reset_done / password_reset_confirm / password_reset_complete
    # 因为它们被包在 app_name='learningnotes' 里，所以是 'learningnotes:login'。
    path('accounts/', include('django.contrib.auth.urls')),

    # ==================== 更多URL参数类型示例 ====================

    # <str:参数名>: 捕获字符串（不包含/）
    # URL: /notes/tag/python/ -> tag_name='python'
    # path('notes/tag/<str:tag_name>/', views.notes_by_tag, name='notes_by_tag'),

    # <slug:参数名>: 捕获slug（字母、数字、连字符、下划线）
    # URL: /notes/slug/my-first-note/ -> slug='my-first-note'
    # path('notes/slug/<slug:slug>/', views.note_by_slug, name='note_by_slug'),

    # <uuid:参数名>: 捕获UUID
    # URL: /notes/uuid/550e8400-e29b-41d4-a716-446655440000/
    # path('notes/uuid/<uuid:uuid>/', views.note_by_uuid, name='note_by_uuid'),

    # <path:参数名>: 捕获路径（包含/）
    # URL: /files/documents/2024/report.pdf -> file_path='documents/2024/report.pdf'
    # path('files/<path:file_path>/', views.serve_file, name='serve_file'),
]

r"""
==================== 正则表达式URL示例 ====================

re_path() 使用正则表达式定义URL模式，提供更灵活的匹配

from django.urls import re_path

urlpatterns = [
    # 匹配4位数字的年份
    # URL: /archive/2024/ -> year='2024'
    re_path(r'^archive/(?P<year>[0-9]{4})/$', views.year_archive, name='year_archive'),

    # 匹配年月日
    # URL: /archive/2024/01/15/ -> year='2024', month='01', day='15'
    re_path(
        r'^archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$',
        views.day_archive,
        name='day_archive'
    ),

    # 匹配文章ID和可选的slug
    # URL: /articles/123/ 或 /articles/123/my-title/
    re_path(
        r'^articles/(?P<pk>\d+)(/(?P<slug>[\w-]+))?/$',
        views.article_detail,
        name='article_detail'
    ),
]
"""

"""
==================== include()的使用 ====================

include() 用于包含其他URL配置，实现模块化

在项目的主urls.py中：

from django.urls import path, include

urlpatterns = [
    # 包含应用的URL配置
    path('learning/', include('learningnotes.urls')),

    # 包含第三方包的URL
    path('api-auth/', include('rest_framework.urls')),

    # 包含命名空间
    path('admin/docs/', include('django.contrib.admindocs.urls')),
]

这样，learningnotes应用的所有URL都会加上'learning/'前缀
例如：/learning/notes/ 对应 notes/
"""

"""
==================== URL反向解析 ====================

URL命名后，可以通过名称获取URL，避免硬编码

在视图中：
    from django.urls import reverse
    url = reverse('learningnotes:note_detail', kwargs={'pk': 123})
    # 结果：/learning/notes/123/

    # 或使用args
    url = reverse('learningnotes:note_detail', args=[123])

在模板中：
    {% url 'learningnotes:note_detail' pk=123 %}
    或
    {% url 'learningnotes:note_detail' note.pk %}

在模型中：
    from django.urls import reverse

    class Note(models.Model):
        # ...

        def get_absolute_url(self):
            return reverse('learningnotes:note_detail', kwargs={'pk': self.pk})
"""

"""
==================== URL参数的默认值 ====================

可以为URL参数提供默认值

urlpatterns = [
    # 两个URL模式映射到同一个视图
    path('notes/', views.note_list_by_category, name='note_list_all'),
    path('notes/category/<int:category_id>/', views.note_list_by_category, name='note_list_category'),
]

在视图中：
    def note_list_by_category(request, category_id=None):
        if category_id:
            notes = Note.objects.filter(category_id=category_id)
        else:
            notes = Note.objects.all()
        # ...
"""

"""
==================== 传递额外参数到视图 ====================

可以通过kwargs参数向视图传递额外的参数

urlpatterns = [
    path('notes/featured/', views.note_list, {'featured': True}, name='featured_notes'),
    path('notes/archived/', views.note_list, {'archived': True}, name='archived_notes'),
]

在视图中：
    def note_list(request, featured=False, archived=False):
        notes = Note.objects.all()
        if featured:
            notes = notes.filter(is_featured=True)
        if archived:
            notes = notes.filter(status='archived')
        # ...
"""

"""
==================== HTTP方法的限制 ====================

虽然URL配置不直接限制HTTP方法，但可以在视图中处理

在视图中：
    from django.views.decorators.http import require_http_methods

    @require_http_methods(["GET", "POST"])
    def note_create(request):
        # 只接受GET和POST请求
        pass

    from django.views.decorators.http import require_GET, require_POST

    @require_GET
    def note_list(request):
        # 只接受GET请求
        pass

    @require_POST
    def note_delete(request, pk):
        # 只接受POST请求
        pass
"""
