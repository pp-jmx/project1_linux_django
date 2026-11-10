"""
============================================================================
  models.py —— 数据层：用 Python 类描述数据库表
============================================================================
【职责】定义表结构（字段 / 关系 / 约束）、Meta 元数据、以及模型自身的业务方法。
【关系】被 views（增删改查）、forms（自动生成表单字段）、admin（注册后台）、
        tests 依赖；本文件变更后必须 makemigrations + migrate。
【数据流】
        HTTP 请求 → urls.py → views.py ⇄ models.py(ORM) → templates 渲染 → 响应
        （表单提交时：views → forms.py 校验 → models.py 落库）

本文件包含 4 个模型：
  Category ──1:N──▶ Note ──M:N──▶ Tag
                      └──1:N──▶ Attachment（文件上传）
============================================================================

Django 模型层 (Model) - Django的灵魂之一

模型是Django中数据的单一、明确的信息源。
它包含存储数据的基本字段和行为。
通常，每个模型映射到数据库中的一张表。

核心概念：
1. ORM (对象关系映射) - 用Python类操作数据库，无需写SQL
2. 字段类型 - 定义数据类型和约束
3. 关系 - 一对多、多对多、一对一
4. 模型方法 - 为模型添加业务逻辑
5. Meta类 - 模型的元数据配置
"""

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


# ==================== 基础模型示例 ====================
class Category(models.Model):
    """
    分类模型 - 展示基本字段类型

    这是一个简单的模型，展示了Django最常用的字段类型
    """

    # CharField: 字符串字段，必须指定max_length
    # unique=True: 保证分类名称唯一
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="分类名称",  # 在Admin后台显示的名称
        help_text="请输入分类名称，不能重复"
    )

    # TextField: 长文本字段，不限制长度
    # blank=True: 表单验证时允许为空
    # null=True: 数据库中允许NULL值
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="分类描述"
    )

    # DateTimeField: 日期时间字段
    # auto_now_add=True: 创建时自动设置为当前时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )

    # IntegerField: 整数字段
    # default: 默认值
    order = models.IntegerField(
        default=0,
        verbose_name="排序",
        help_text="数字越小越靠前"
    )

    # BooleanField: 布尔字段
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否激活"
    )

    class Meta:
        """
        Meta类 - 模型的元数据

        定义模型的各种选项，如排序、数据库表名、显示名称等
        """
        verbose_name = "分类"  # 单数形式的显示名称
        verbose_name_plural = "分类列表"  # 复数形式的显示名称
        ordering = ['order', '-created_at']  # 默认排序（order升序，created_at降序）
        db_table = 'learning_category'  # 自定义数据库表名

    def __str__(self):
        """
        字符串表示 - 在Admin后台和shell中显示

        这是Python的魔术方法，定义对象的字符串表示
        """
        return self.name

    def get_note_count(self):
        """
        自定义方法 - 获取该分类下的笔记数量

        模型方法可以封装业务逻辑，使代码更清晰
        """
        return self.notes.count()

    get_note_count.short_description = "笔记数量"  # 在Admin中显示的名称


# ==================== 复杂模型示例 ====================
class Note(models.Model):
    """
    笔记模型 - 展示关系字段和高级特性

    这个模型展示了：
    - 外键关系 (ForeignKey)
    - 多对多关系 (ManyToManyField)
    - 选择字段 (choices)
    - 自动时间戳
    - 自定义方法
    """

    # 状态选择 - 使用元组定义选项
    # 第一个元素是存储在数据库中的值，第二个是显示给用户的文本
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    PRIORITY_CHOICES = [
        (1, '低'),
        (2, '中'),
        (3, '高'),
    ]

    # ===== 基本信息字段 =====
    title = models.CharField(
        max_length=200,
        verbose_name="标题",
        db_index=True  # 创建数据库索引，加快查询速度
    )

    content = models.TextField(
        verbose_name="内容"
    )

    # CharField with choices: 选择字段
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="状态"
    )

    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        verbose_name="优先级"
    )

    # ===== 关系字段 =====

    # ForeignKey: 多对一关系
    # 一个分类可以有多个笔记，一个笔记只属于一个分类
    # on_delete=models.CASCADE: 删除分类时，关联的笔记也会被删除
    # related_name: 反向查询的名称，可以用 category.notes.all() 获取分类下的所有笔记
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="分类"
    )

    # ForeignKey to User: 关联到Django内置的用户模型
    # on_delete=models.SET_NULL: 删除用户时，笔记的作者字段设为NULL
    # null=True, blank=True: 允许为空
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes',
        verbose_name="作者"
    )

    # ManyToManyField: 多对多关系
    # 一个笔记可以有多个标签，一个标签可以属于多个笔记
    # blank=True: 允许不选择标签
    tags = models.ManyToManyField(
        'Tag',  # 可以用字符串引用还未定义的模型
        blank=True,
        related_name='notes',
        verbose_name="标签"
    )

    # ===== 统计字段 =====
    view_count = models.IntegerField(
        default=0,
        verbose_name="浏览次数"
    )

    # ===== 时间戳字段 =====
    created_at = models.DateTimeField(
        auto_now_add=True,  # 创建时自动设置，之后不再改变
        verbose_name="创建时间"
    )

    updated_at = models.DateTimeField(
        auto_now=True,  # 每次保存时自动更新
        verbose_name="更新时间"
    )

    class Meta:
        verbose_name = "学习笔记"
        verbose_name_plural = "学习笔记列表"
        ordering = ['-created_at']  # 按创建时间降序排序
        # 组合索引 - 提高多字段查询性能
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['status', 'priority']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        规范 URL - Django 的约定方法

        很多通用视图（CreateView/UpdateView）成功后会自动跳转到这里；
        Admin 的“在站点上查看”按钮、模板里的 {{ note.get_absolute_url }} 也会用到。
        """
        return reverse('learningnotes:note_detail', kwargs={'pk': self.pk})

    def increment_view_count(self):
        """增加浏览次数"""
        self.view_count += 1
        self.save(update_fields=['view_count'])  # 只更新指定字段，提高性能

    def is_published(self):
        """判断是否已发布"""
        return self.status == 'published'

    is_published.boolean = True  # 在Admin中显示为布尔图标
    is_published.short_description = "已发布"

    def get_tag_names(self):
        """获取所有标签名称"""
        return ", ".join([tag.name for tag in self.tags.all()])

    get_tag_names.short_description = "标签"

    @property
    def is_recent(self):
        """
        属性方法 - 判断是否是最近创建的

        使用@property装饰器，可以像访问属性一样调用方法
        例如: note.is_recent 而不是 note.is_recent()
        """
        from datetime import timedelta
        return timezone.now() - self.created_at < timedelta(days=7)


# ==================== 简单关联模型 ====================
class Tag(models.Model):
    """
    标签模型 - 用于多对多关系

    这是一个简单的模型，用于展示多对多关系
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="标签名称"
    )

    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name="标签颜色",
        help_text="16进制颜色代码，如：#007bff"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签列表"
        ordering = ['name']

    def __str__(self):
        return self.name


# ==================== 附件模型 ====================
class Attachment(models.Model):
    """
    附件模型 - 展示文件字段

    展示如何处理文件上传
    """
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="所属笔记"
    )

    # FileField: 文件字段
    # upload_to: 文件上传路径，支持时间格式化
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',  # 按年/月/日组织文件
        verbose_name="文件"
    )

    # 可以单独存储文件名，方便显示
    filename = models.CharField(
        max_length=255,
        verbose_name="文件名"
    )

    # 文件大小（字节）
    file_size = models.IntegerField(
        default=0,
        verbose_name="文件大小"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="上传时间"
    )

    class Meta:
        verbose_name = "附件"
        verbose_name_plural = "附件列表"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename

    def get_file_size_display(self):
        """格式化显示文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    get_file_size_display.short_description = "文件大小"
