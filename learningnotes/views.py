"""
============================================================================
  views.py —— 逻辑层：接收请求、处理业务、返回响应
============================================================================
【职责】从 URL 拿到参数，通过 ORM 读写数据、用表单校验，最后渲染模板或返回 JSON。
【关系】被 urls.py 指向；依赖 models.py（数据）、forms.py（校验）、
        以及 templates/learningnotes/*.html（渲染）；
        redirect/reverse 中的名字必须与 urls.py 的 name 一致。
【本文件的对照学习】
        同一个功能给了两种写法，便于对比 FBV 与 CBV：
          FBV：note_create / note_edit / note_delete
          CBV：NoteCreateView / NoteUpdateView / NoteDeleteView
        另有 NoteSearchView（自定义 CBV）、note_api_list/detail（JSON API）。
============================================================================

Django 视图层 (View) - Django的灵魂之二

视图是Django应用中的"业务逻辑层"。
它接收Web请求，处理数据，并返回Web响应。

核心概念：
1. 函数视图 (Function-Based Views, FBV) - 用函数处理请求
2. 类视图 (Class-Based Views, CBV) - 用类处理请求，更易复用
3. 请求对象 (HttpRequest) - 包含客户端请求的所有信息
4. 响应对象 (HttpResponse) - 返回给客户端的响应
5. 快捷函数 - render, redirect, get_object_or_404等
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.core.paginator import Paginator

from .models import Note, Category, Tag
from .forms import NoteForm, CategoryForm


# ==================== 函数视图示例 ====================

def note_list(request):
    """
    笔记列表视图 - 基础函数视图示例

    功能：
    - 显示所有已发布的笔记
    - 支持按分类筛选
    - 支持搜索
    - 分页显示

    参数：
        request: HttpRequest对象，包含请求的所有信息
            - request.method: 请求方法 (GET, POST等)
            - request.GET: URL参数字典
            - request.POST: POST数据字典
            - request.user: 当前登录用户
            - request.session: 会话数据

    返回：
        HttpResponse对象，通常通过render()生成
    """

    # 1. 获取查询参数
    category_id = request.GET.get('category')  # 获取分类ID
    search_query = request.GET.get('q', '')  # 获取搜索关键词，默认为空字符串
    page_number = request.GET.get('page', 1)  # 获取页码，默认第1页

    # 2. 构建查询集 (QuerySet)
    # QuerySet是Django ORM的核心，表示数据库查询
    notes = Note.objects.filter(status='published')  # 只显示已发布的笔记

    # 3. 条件筛选
    if category_id:
        notes = notes.filter(category_id=category_id)

    # 4. 搜索功能 - 使用Q对象进行复杂查询
    # Q对象可以使用 | (或) 和 & (与) 进行组合
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |  # 标题包含关键词（不区分大小写）
            Q(content__icontains=search_query)  # 内容包含关键词
        )

    # 5. 性能优化 - select_related 和 prefetch_related
    # select_related: 用于外键关系，使用SQL JOIN，减少数据库查询
    # prefetch_related: 用于多对多和反向外键，使用IN查询
    notes = notes.select_related('category', 'author').prefetch_related('tags')

    # 6. 分页
    paginator = Paginator(notes, 10)  # 每页显示10条
    page_obj = paginator.get_page(page_number)

    # 7. 准备上下文数据
    context = {
        'notes': page_obj,  # 当前页的笔记
        'categories': Category.objects.filter(is_active=True),  # 所有激活的分类
        'search_query': search_query,
        'current_category': category_id,
        'page_obj': page_obj,  # 分页对象
    }

    # 8. 渲染模板并返回响应
    # render() 是快捷函数，等价于：
    # from django.template import loader
    # template = loader.get_template('learningnotes/note_list.html')
    # return HttpResponse(template.render(context, request))
    return render(request, 'learningnotes/note_list.html', context)


def note_detail(request, pk):
    """
    笔记详情视图 - 展示单个对象的查询和更新

    参数：
        request: 请求对象
        pk: 主键 (Primary Key)，从URL中捕获

    URL示例：/notes/123/ -> pk=123
    """

    # get_object_or_404: 快捷函数，获取对象或返回404错误
    # 等价于：
    # try:
    #     note = Note.objects.get(pk=pk)
    # except Note.DoesNotExist:
    #     raise Http404("笔记不存在")
    note = get_object_or_404(Note, pk=pk, status='published')

    # 增加浏览次数
    note.increment_view_count()

    # 获取相关笔记（同分类的其他笔记）
    related_notes = Note.objects.filter(
        category=note.category,
        status='published'
    ).exclude(pk=pk)[:5]  # 排除当前笔记，只取前5条

    context = {
        'note': note,
        'related_notes': related_notes,
    }

    return render(request, 'learningnotes/note_detail.html', context)


@login_required
def note_create(request):
    """
    创建笔记视图 - 展示表单处理

    处理两种HTTP方法：
    - GET: 显示空表单
    - POST: 处理表单提交
    """

    if request.method == 'POST':
        # POST请求 - 用户提交了表单
        form = NoteForm(request.POST)

        # 验证表单数据
        if form.is_valid():
            # 表单验证通过，保存数据
            note = form.save(commit=False)  # 先不保存到数据库

            # 设置作者为当前登录用户
            if request.user.is_authenticated:
                note.author = request.user

            note.save()  # 保存到数据库
            form.save_m2m()  # 保存多对多关系（标签）

            # 添加成功消息
            messages.success(request, '笔记创建成功！')

            # 重定向到笔记详情页
            # 注意：learningnotes/urls.py 声明了 app_name，反向解析必须带命名空间
            return redirect('learningnotes:note_detail', pk=note.pk)
        else:
            # 表单验证失败，显示错误信息
            messages.error(request, '请检查表单内容！')
    else:
        # GET请求 - 显示空表单
        form = NoteForm()

    context = {
        'form': form,
        'action': '创建',
    }

    return render(request, 'learningnotes/note_form.html', context)


@login_required
def note_edit(request, pk):
    """
    编辑笔记视图 - 展示更新操作
    """
    note = get_object_or_404(Note, pk=pk)

    # 权限检查
    if note.author and note.author != request.user:
        messages.error(request, '您没有权限编辑此笔记！')
        return redirect('learningnotes:note_detail', pk=pk)

    if request.method == 'POST':
        # 传入instance参数，表示更新已有对象
        form = NoteForm(request.POST, instance=note)

        if form.is_valid():
            form.save()
            messages.success(request, '笔记更新成功！')
            return redirect('learningnotes:note_detail', pk=note.pk)
    else:
        # 用已有对象初始化表单
        form = NoteForm(instance=note)

    context = {
        'form': form,
        'note': note,
        'action': '编辑',
    }

    return render(request, 'learningnotes/note_form.html', context)


@login_required
def note_delete(request, pk):
    """
    删除笔记视图 - 展示删除操作

    为了安全，删除操作通常要求POST方法
    """
    note = get_object_or_404(Note, pk=pk)

    # 权限检查
    if note.author and note.author != request.user:
        messages.error(request, '您没有权限删除此笔记！')
        return redirect('learningnotes:note_detail', pk=pk)

    if request.method == 'POST':
        note.delete()
        messages.success(request, '笔记已删除！')
        return redirect('learningnotes:note_list')

    # GET请求显示确认页面
    return render(request, 'learningnotes/note_confirm_delete.html', {'note': note})


# ==================== 类视图示例 ====================

class CategoryListView(ListView):
    """
    分类列表视图 - 使用通用类视图

    ListView是Django提供的通用类视图，用于显示对象列表
    只需配置几个属性，就能实现完整的列表功能

    类视图的优点：
    1. 代码复用性强
    2. 可以通过继承扩展功能
    3. Django提供了多个通用视图，减少重复代码
    """

    model = Category  # 指定模型
    template_name = 'learningnotes/category_list.html'  # 模板路径
    context_object_name = 'categories'  # 在模板中使用的变量名
    paginate_by = 20  # 每页显示数量

    def get_queryset(self):
        """
        自定义查询集

        这个方法可以重写，添加自定义过滤、排序等逻辑
        """
        # 使用annotate添加聚合字段
        # Count('notes'): 统计每个分类下的笔记数量
        queryset = Category.objects.filter(is_active=True).annotate(
            note_count=Count('notes')
        ).order_by('order', '-created_at')  # 显式排序，避免分页时 UnorderedObjectListWarning
        return queryset

    def get_context_data(self, **kwargs):
        """
        添加额外的上下文数据

        这个方法可以向模板传递额外的变量
        """
        context = super().get_context_data(**kwargs)
        # 添加总笔记数
        context['total_notes'] = Note.objects.filter(status='published').count()
        return context


class CategoryDetailView(DetailView):
    """
    分类详情视图 - 使用DetailView

    DetailView用于显示单个对象的详情
    """
    model = Category
    template_name = 'learningnotes/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取该分类下的笔记
        context['notes'] = self.object.notes.filter(status='published')[:10]
        return context


class NoteCreateView(LoginRequiredMixin, CreateView):
    """
    创建笔记视图 - 使用CreateView

    CreateView用于创建新对象
    自动处理GET（显示表单）和POST（保存数据）
    """
    model = Note
    form_class = NoteForm
    template_name = 'learningnotes/note_form.html'
    success_url = reverse_lazy('learningnotes:note_list')  # 成功后跳转的URL

    def form_valid(self, form):
        """
        表单验证通过时调用

        可以在保存前对对象进行修改
        """
        form.instance.author = self.request.user
        messages.success(self.request, '笔记创建成功！')
        return super().form_valid(form)

    def form_invalid(self, form):
        """表单验证失败时调用"""
        messages.error(self.request, '请检查表单内容！')
        return super().form_invalid(form)


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    """
    更新笔记视图 - 使用UpdateView

    UpdateView用于更新已有对象
    """
    model = Note
    form_class = NoteForm
    template_name = 'learningnotes/note_form.html'

    def get_success_url(self):
        """动态生成成功跳转URL"""
        return reverse_lazy('learningnotes:note_detail', kwargs={'pk': self.object.pk})


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    """
    删除笔记视图 - 使用DeleteView

    DeleteView用于删除对象
    """
    model = Note
    template_name = 'learningnotes/note_confirm_delete.html'
    success_url = reverse_lazy('learningnotes:note_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, '笔记已删除！')
        return super().delete(request, *args, **kwargs)


# ==================== 自定义类视图 ====================

class NoteSearchView(View):
    """
    笔记搜索视图 - 自定义类视图

    继承基础View类，手动处理不同的HTTP方法
    """

    def get(self, request):
        """处理GET请求"""
        query = request.GET.get('q', '')

        if not query:
            return render(request, 'learningnotes/search.html', {
                'query': query,
                'notes': [],
            })

        # 复杂搜索逻辑
        notes = Note.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query)
        ).filter(status='published').distinct()

        return render(request, 'learningnotes/search.html', {
            'query': query,
            'notes': notes,
        })


# ==================== API视图示例 ====================

def note_api_list(request):
    """
    笔记API列表 - 返回JSON数据

    展示如何创建简单的API接口
    """
    notes = Note.objects.filter(status='published').select_related('category')[:10]

    # 将QuerySet转换为字典列表
    data = []
    for note in notes:
        data.append({
            'id': note.pk,
            'title': note.title,
            'category': note.category.name,
            'author': note.author.username if note.author else None,
            'created_at': note.created_at.isoformat(),
            'view_count': note.view_count,
        })

    # 返回JSON响应
    return JsonResponse({
        'status': 'success',
        'count': len(data),
        'data': data
    })


def note_api_detail(request, pk):
    """笔记API详情"""
    try:
        note = Note.objects.select_related('category', 'author').prefetch_related('tags').get(
            pk=pk,
            status='published'
        )
    except Note.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '笔记不存在'
        }, status=404)

    data = {
        'id': note.pk,
        'title': note.title,
        'content': note.content,
        'category': note.category.name,
        'author': note.author.username if note.author else None,
        'tags': [tag.name for tag in note.tags.all()],
        'view_count': note.view_count,
        'created_at': note.created_at.isoformat(),
        'updated_at': note.updated_at.isoformat(),
    }

    return JsonResponse({
        'status': 'success',
        'data': data
    })


# ==================== 辅助视图 ====================

def index(request):
    """
    首页视图 - 展示汇总信息
    """
    # 统计数据
    stats = {
        'total_notes': Note.objects.filter(status='published').count(),
        'total_categories': Category.objects.filter(is_active=True).count(),
        'total_tags': Tag.objects.count(),
    }

    # 最新笔记
    latest_notes = Note.objects.filter(status='published').select_related(
        'category', 'author'
    ).prefetch_related('tags')[:5]

    # 热门笔记（按浏览次数排序）
    popular_notes = Note.objects.filter(status='published').order_by('-view_count')[:5]

    context = {
        'stats': stats,
        'latest_notes': latest_notes,
        'popular_notes': popular_notes,
    }

    return render(request, 'learningnotes/index.html', context)
