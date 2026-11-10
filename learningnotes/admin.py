"""
============================================================================
  admin.py —— 后台：几乎零配置就能管理数据库
============================================================================
【职责】把 models.py 里的模型注册到 /admin/，并定制列表列、过滤器、搜索、批量操作。
【关系】依赖 models.py；与 views/templates 无直接依赖（但共用同一份数据）。
        后台里新增的数据，前台视图/模板立刻能看到。
【本文件包含】CategoryAdmin / NoteAdmin / TagAdmin / AttachmentAdmin
        + AttachmentInline（在笔记页内联编辑附件）。
============================================================================

Django Admin后台 (Admin) - Django的自动化管理界面

Admin是Django最强大的功能之一。
只需简单配置，就能自动生成完整的后台管理界面。

核心概念：
1. ModelAdmin - 定制模型在Admin中的显示和行为
2. list_display - 列表页显示的字段
3. list_filter - 侧边栏过滤器
4. search_fields - 搜索字段
5. inlines - 内联编辑关联对象
6. actions - 批量操作
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Category, Note, Tag, Attachment


# ==================== 基础Admin配置 ====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    分类管理 - 基础Admin配置示例

    @admin.register装饰器等价于：
    admin.site.register(Category, CategoryAdmin)
    """

    # list_display: 列表页显示的字段
    # 可以是模型字段名、模型方法、ModelAdmin方法
    list_display = ['name', 'description', 'order', 'is_active', 'created_at', 'note_count_display']

    # list_filter: 右侧过滤器
    # 可以按字段值、日期等进行过滤
    list_filter = ['is_active', 'created_at']

    # search_fields: 搜索框搜索的字段
    # 支持 ^ (以...开始), = (精确匹配), @ (全文搜索), 无前缀 (包含)
    search_fields = ['name', 'description']

    # list_per_page: 每页显示数量
    list_per_page = 20

    # ordering: 默认排序
    ordering = ['order', '-created_at']

    # list_editable: 可以在列表页直接编辑的字段
    list_editable = ['order', 'is_active']

    # date_hierarchy: 日期层级导航
    date_hierarchy = 'created_at'

    # fields: 编辑页显示的字段（控制顺序）
    fields = ['name', 'description', 'order', 'is_active']

    # readonly_fields: 只读字段
    readonly_fields = ['created_at']

    # prepopulated_fields: 自动填充字段
    # 例如：根据name自动生成slug
    # prepopulated_fields = {'slug': ('name',)}

    def note_count_display(self, obj):
        """
        自定义显示方法 - 显示笔记数量

        参数：
            obj: 当前行的模型实例
        返回：
            要显示的内容（字符串或HTML）
        """
        count = obj.get_note_count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'gray',
            count
        )

    note_count_display.short_description = '笔记数量'  # 列标题
    # 说明：想按“笔记数量”排序需要先 annotate(Count('notes'))，
    # 直接写 admin_order_field='notes__count' 会在点击排序时抛 FieldError，故留空。


# ==================== 高级Admin配置 ====================

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """
    笔记管理 - 高级Admin配置示例

    展示更多Admin功能：
    - 字段分组
    - 内联编辑
    - 自定义操作
    - 过滤器
    """

    # list_display: 列表显示
    list_display = [
        'title',
        'category',
        'author',
        'status_display',  # 自定义方法
        'priority',
        'view_count',
        'created_at',
        'is_recent_display'
    ]

    # list_filter: 过滤器
    # 可以使用元组指定更详细的过滤选项
    list_filter = [
        'status',
        'priority',
        'category',
        ('created_at', admin.DateFieldListFilter),  # 日期过滤器
        ('tags', admin.RelatedOnlyFieldListFilter),  # 只显示有关联的标签
    ]

    # search_fields: 搜索
    # '^title' - 以title开始
    # '=title' - 精确匹配title
    # '@content' - 全文搜索content（需要数据库支持）
    search_fields = ['^title', 'content', 'author__username']

    # autocomplete_fields: 自动完成字段（用于外键和多对多）
    # 需要在关联模型的Admin中设置search_fields
    autocomplete_fields = ['category', 'tags']

    # filter_horizontal / filter_vertical: 多对多字段的选择器样式
    filter_horizontal = ['tags']  # 水平选择器
    # filter_vertical = ['tags']  # 垂直选择器（二选一）

    # raw_id_fields: 显示ID输入框而不是下拉框（用于大量数据）
    # raw_id_fields = ['author']

    # date_hierarchy: 日期导航
    date_hierarchy = 'created_at'

    # ordering: 排序
    ordering = ['-created_at']

    # list_per_page: 每页数量
    list_per_page = 25

    # list_select_related: 优化查询（自动使用select_related）
    list_select_related = ['category', 'author']

    # ===== 字段分组 =====
    # fieldsets: 将字段分组显示
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'content', 'category')
        }),
        ('标签和状态', {
            'fields': ('tags', 'status', 'priority'),
            'classes': ('wide',),  # CSS类名，'wide'表示宽显示，'collapse'表示默认折叠
        }),
        ('作者信息', {
            'fields': ('author',),
            'classes': ('collapse',),  # 默认折叠
        }),
        ('统计信息', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '这些字段是自动生成的统计信息'  # 分组描述
        }),
    )

    # readonly_fields: 只读字段
    readonly_fields = ['view_count', 'created_at', 'updated_at']

    # save_on_top: 在顶部也显示保存按钮
    save_on_top = True

    # ===== 自定义显示方法 =====

    def status_display(self, obj):
        """状态显示 - 带颜色"""
        colors = {
            'draft': 'gray',
            'published': 'green',
            'archived': 'orange',
        }
        status_text = obj.get_status_display()  # 获取choices的显示文本
        color = colors.get(obj.status, 'black')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status_text
        )

    status_display.short_description = '状态'
    status_display.admin_order_field = 'status'

    def is_recent_display(self, obj):
        """是否最近创建 - 显示图标"""
        if obj.is_recent:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">✗</span>')

    is_recent_display.short_description = '最近'
    is_recent_display.boolean = True  # 显示为布尔图标

    # ===== 自定义操作 (Actions) =====

    actions = ['make_published', 'make_draft', 'increment_priority']

    def make_published(self, request, queryset):
        """批量发布"""
        updated = queryset.update(status='published')
        self.message_user(request, f'成功发布 {updated} 篇笔记')

    make_published.short_description = '发布选中的笔记'

    def make_draft(self, request, queryset):
        """批量设为草稿"""
        updated = queryset.update(status='draft')
        self.message_user(request, f'成功将 {updated} 篇笔记设为草稿')

    make_draft.short_description = '将选中的笔记设为草稿'

    def increment_priority(self, request, queryset):
        """提高优先级"""
        for note in queryset:
            if note.priority < 3:
                note.priority += 1
                note.save()
        self.message_user(request, '已提高选中笔记的优先级')

    increment_priority.short_description = '提高优先级'

    # ===== 自定义查询 =====

    def get_queryset(self, request):
        """
        自定义查询集

        可以添加注解、过滤等
        """
        queryset = super().get_queryset(request)
        # 添加注解，统计标签数量
        queryset = queryset.annotate(tag_count=Count('tags'))
        return queryset


# ==================== 内联编辑 (Inline) ====================

class AttachmentInline(admin.TabularInline):
    """
    附件内联编辑 - 在笔记编辑页面中直接编辑附件

    TabularInline: 表格形式显示
    StackedInline: 堆叠形式显示（每个对象占多行）
    """
    model = Attachment
    extra = 1  # 额外显示的空表单数量
    max_num = 5  # 最多允许的数量
    fields = ['file', 'filename', 'file_size', 'uploaded_at']
    readonly_fields = ['file_size', 'uploaded_at']

    # can_delete: 是否允许删除
    can_delete = True

    # show_change_link: 显示"修改"链接
    show_change_link = True


# 将内联添加到NoteAdmin
NoteAdmin.inlines = [AttachmentInline]


# ==================== 简单注册方式 ====================

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """标签管理 - 简单配置"""
    list_display = ['name', 'color', 'note_count', 'created_at']
    search_fields = ['name']
    ordering = ['name']

    def note_count(self, obj):
        return obj.notes.count()

    note_count.short_description = '笔记数量'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """附件管理"""
    list_display = ['filename', 'note', 'file_size_display', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'note__title']
    readonly_fields = ['uploaded_at']

    def file_size_display(self, obj):
        return obj.get_file_size_display()

    file_size_display.short_description = '文件大小'


# ==================== 自定义Admin站点 ====================

"""
可以自定义Admin站点的标题和说明

在urls.py中：
    admin.site.site_header = '学习笔记管理系统'
    admin.site.site_title = '学习笔记'
    admin.site.index_title = '欢迎使用学习笔记管理系统'

或者创建自定义Admin站点：

from django.contrib import admin

class MyAdminSite(admin.AdminSite):
    site_header = '学习笔记管理系统'
    site_title = '学习笔记'
    index_title = '欢迎使用'

admin_site = MyAdminSite(name='myadmin')
admin_site.register(Note, NoteAdmin)
"""

"""
==================== Admin权限控制 ====================

可以控制用户在Admin中的权限

class NoteAdmin(admin.ModelAdmin):
    # ...

    def has_add_permission(self, request):
        # 控制是否有添加权限
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # 控制是否有修改权限
        if obj and obj.author != request.user:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # 控制是否有删除权限
        return request.user.is_superuser

    def has_module_permission(self, request):
        # 控制是否能看到这个模块
        return True
"""

"""
==================== Admin自定义模板 ====================

可以覆盖Admin的模板来自定义外观

在应用的templates目录下创建：
    admin/base_site.html  # 覆盖基础模板
    admin/change_list.html  # 覆盖列表页
    admin/change_form.html  # 覆盖编辑页
    admin/<app>/<model>/change_list.html  # 针对特定模型的列表页

例如，创建 templates/admin/base_site.html：

{% extends "admin/base.html" %}

{% block title %}学习笔记管理{% endblock %}

{% block branding %}
<h1 id="site-name">学习笔记管理系统</h1>
{% endblock %}

{% block nav-global %}{% endblock %}
"""
