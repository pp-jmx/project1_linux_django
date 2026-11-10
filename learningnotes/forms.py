"""
============================================================================
  forms.py —— 校验层：把“用户输入”变成“可信数据”
============================================================================
【职责】定义表单字段、渲染控件、校验（字段级 clean_<field> + 跨字段 clean）。
【关系】被 views.py 使用；ModelForm 依赖 models.py 自动生成字段；
        校验通过后可直接 save() 写回 models。
【本文件包含】
        NoteForm / CategoryForm / TagForm / DynamicNoteForm（ModelForm）
        NoteSearchForm（普通 Form，处理搜索的 GET 参数）
        AttachmentFormSet（内联表单集，处理一对多）
============================================================================

Django 表单 (Forms) - Django的数据验证层

表单是Django中用户输入数据的桥梁。
它负责数据的验证、清洗和转换。

核心概念：
1. Form类 - 普通表单，用于数据验证
2. ModelForm类 - 基于模型的表单，自动生成字段
3. 字段验证 - 内置验证器和自定义验证
4. 表单渲染 - 在模板中显示表单
5. 表单处理 - 验证、清洗、保存数据
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from .models import Note, Category, Tag


# ==================== ModelForm示例 ====================

class NoteForm(forms.ModelForm):
    """
    笔记表单 - ModelForm示例

    ModelForm是Django最常用的表单类型：
    - 自动从模型生成表单字段
    - 自动进行数据验证
    - 可以直接保存到数据库
    """

    class Meta:
        """
        Meta类 - 配置ModelForm

        定义表单基于哪个模型，包含哪些字段，如何显示等
        """
        model = Note

        # fields: 指定表单包含的字段
        # '__all__': 包含所有字段
        # ['field1', 'field2']: 只包含指定字段
        # exclude=['field1']: 排除某些字段
        fields = ['title', 'content', 'category', 'tags', 'status', 'priority']

        # labels: 自定义字段标签（显示名称）
        labels = {
            'title': '笔记标题',
            'content': '笔记内容',
            'category': '分类',
            'tags': '标签',
            'status': '状态',
            'priority': '优先级',
        }

        # help_texts: 字段帮助文本
        help_texts = {
            'title': '请输入简洁明了的标题，不超过200字',
            'content': '支持Markdown格式',
            'tags': '可以选择多个标签，按住Ctrl/Cmd多选',
        }

        # error_messages: 自定义错误消息
        error_messages = {
            'title': {
                'required': '标题不能为空',
                'max_length': '标题长度不能超过200字',
            },
            'content': {
                'required': '内容不能为空',
            },
        }

        # widgets: 自定义表单控件（HTML元素）
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',  # CSS类名
                'placeholder': '请输入标题',
                'maxlength': '200',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '请输入内容',
                'rows': 10,  # 文本框行数
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'tags': forms.CheckboxSelectMultiple(),  # 使用复选框而不是下拉框
            'status': forms.RadioSelect(),  # 使用单选框
            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def clean_title(self):
        """
        字段级验证 - 验证单个字段

        方法名格式：clean_<字段名>
        返回清洗后的数据
        如果验证失败，抛出ValidationError
        """
        title = self.cleaned_data.get('title')

        # 检查标题是否为空（虽然required已经检查，但这里演示自定义验证）
        if not title:
            raise ValidationError('标题不能为空')

        # 检查标题长度
        if len(title) < 5:
            raise ValidationError('标题至少需要5个字符')

        # 检查是否包含敏感词（示例）
        sensitive_words = ['测试敏感词', '禁用词']
        for word in sensitive_words:
            if word in title:
                raise ValidationError(f'标题不能包含"{word}"')

        # 返回清洗后的数据（可以进行格式化）
        return title.strip()

    def clean_content(self):
        """验证内容字段"""
        content = self.cleaned_data.get('content')

        if content and len(content) < 10:
            raise ValidationError('内容至少需要10个字符')

        return content.strip()

    def clean(self):
        """
        表单级验证 - 验证多个字段之间的关系

        在所有字段验证完成后调用
        可以访问所有字段的清洗数据
        """
        cleaned_data = super().clean()

        title = cleaned_data.get('title')
        content = cleaned_data.get('content')
        status = cleaned_data.get('status')

        # 跨字段验证：如果状态是"已发布"，必须有完整的标题和内容
        if status == 'published':
            if not title or len(title) < 5:
                raise ValidationError('已发布的笔记标题不能少于5个字符')

            if not content or len(content) < 50:
                raise ValidationError('已发布的笔记内容不能少于50个字符')

        # 检查标题和内容是否重复
        if title and content:
            if title.lower() in content.lower():
                # 这里只是警告，不阻止提交
                self.add_error(None, '提示：标题已包含在内容中，建议修改')

        return cleaned_data


class CategoryForm(forms.ModelForm):
    """
    分类表单 - 简单ModelForm示例
    """

    class Meta:
        model = Category
        fields = ['name', 'description', 'order', 'is_active']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '分类名称',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '分类描述（可选）',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean_name(self):
        """检查分类名称是否已存在"""
        name = self.cleaned_data.get('name')

        # 如果是编辑操作，排除自己
        if self.instance and self.instance.pk:
            exists = Category.objects.filter(name=name).exclude(pk=self.instance.pk).exists()
        else:
            exists = Category.objects.filter(name=name).exists()

        if exists:
            raise ValidationError('该分类名称已存在')

        return name


# ==================== 普通Form示例 ====================

class NoteSearchForm(forms.Form):
    """
    搜索表单 - 普通Form示例

    普通Form不绑定模型，用于：
    - 搜索表单
    - 登录表单
    - 其他不直接对应数据库表的表单
    """

    # CharField: 字符串字段
    query = forms.CharField(
        label='搜索关键词',
        max_length=100,
        required=False,  # 可选字段
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '输入关键词搜索笔记...',
        })
    )

    # ChoiceField: 选择字段
    category = forms.ModelChoiceField(
        label='分类',
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='全部分类',  # 空选项的显示文本
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    # MultipleChoiceField: 多选字段
    tags = forms.ModelMultipleChoiceField(
        label='标签',
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    # ChoiceField with choices: 固定选项
    status = forms.ChoiceField(
        label='状态',
        choices=[('', '全部')] + Note.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    # DateField: 日期字段
    date_from = forms.DateField(
        label='开始日期',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',  # HTML5日期选择器
        })
    )

    date_to = forms.DateField(
        label='结束日期',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    # ChoiceField: 排序选项
    ORDER_CHOICES = [
        ('-created_at', '创建时间（降序）'),
        ('created_at', '创建时间（升序）'),
        ('-view_count', '浏览次数（降序）'),
        ('view_count', '浏览次数（升序）'),
        ('title', '标题（A-Z）'),
        ('-title', '标题（Z-A）'),
    ]

    order_by = forms.ChoiceField(
        label='排序方式',
        choices=ORDER_CHOICES,
        initial='-created_at',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    def clean(self):
        """表单级验证"""
        cleaned_data = super().clean()

        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        # 验证日期范围
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError('开始日期不能晚于结束日期')

        return cleaned_data


# ==================== 带验证器的表单 ====================

class TagForm(forms.ModelForm):
    """
    标签表单 - 展示验证器的使用
    """

    class Meta:
        model = Tag
        fields = ['name', 'color']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '标签名称',
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',  # HTML5颜色选择器
            }),
        }

    # 添加额外的验证器
    name = forms.CharField(
        label='标签名称',
        max_length=50,
        validators=[
            MinLengthValidator(2, message='标签名称至少需要2个字符'),
            MaxLengthValidator(50, message='标签名称不能超过50个字符'),
        ]
    )

    def clean_color(self):
        """验证颜色代码格式"""
        color = self.cleaned_data.get('color')

        # 检查是否是有效的16进制颜色代码
        if not color.startswith('#'):
            raise ValidationError('颜色代码必须以#开头')

        if len(color) != 7:
            raise ValidationError('颜色代码格式错误，应为#RRGGBB格式')

        try:
            int(color[1:], 16)  # 验证是否是有效的16进制数
        except ValueError:
            raise ValidationError('颜色代码格式错误')

        return color.upper()  # 转换为大写


# ==================== 动态表单示例 ====================

class DynamicNoteForm(forms.ModelForm):
    """
    动态表单 - 根据条件动态调整字段
    """

    class Meta:
        model = Note
        fields = ['title', 'content', 'category', 'tags', 'status', 'priority']

    def __init__(self, *args, **kwargs):
        """
        __init__方法 - 表单初始化

        可以在这里：
        - 动态添加/删除字段
        - 修改字段属性
        - 根据用户权限调整表单
        """
        # 获取用户对象（如果传递了的话）
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # 根据用户权限调整字段
        if user and not user.is_staff:
            # 非管理员用户不能选择"已发布"状态
            self.fields['status'].choices = [
                choice for choice in Note.STATUS_CHOICES
                if choice[0] != 'published'
            ]

        # 动态设置分类选项（只显示激活的分类）
        self.fields['category'].queryset = Category.objects.filter(is_active=True)

        # 为所有字段添加CSS类
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                pass  # 保持原样
            else:
                field.widget.attrs['class'] = 'form-control'

        # 如果是编辑模式，添加提示
        if self.instance and self.instance.pk:
            self.fields['title'].help_text = f'最后更新：{self.instance.updated_at}'


# ==================== 内联表单集示例 ====================

from django.forms import inlineformset_factory
from .models import Attachment

# 内联表单集 - 用于处理一对多关系
# 例如：一个笔记可以有多个附件
AttachmentFormSet = inlineformset_factory(
    Note,  # 父模型
    Attachment,  # 子模型
    fields=['file', 'filename'],  # 包含的字段
    extra=1,  # 额外显示的空表单数量
    can_delete=True,  # 允许删除
    widgets={
        'filename': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '文件描述',
        }),
    }
)

"""
使用示例（在视图中）:

def note_with_attachments(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        formset = AttachmentFormSet(request.POST, request.FILES, instance=note)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('note_detail', pk=note.pk)
    else:
        form = NoteForm(instance=note)
        formset = AttachmentFormSet(instance=note)

    return render(request, 'template.html', {
        'form': form,
        'formset': formset,
    })
"""
