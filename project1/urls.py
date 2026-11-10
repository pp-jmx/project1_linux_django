"""
URL configuration for project1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 后台管理：Django 自带，几乎零配置
    path('admin/', admin.site.urls),

    # 留言板（最小示例，保持原样）
    path('', include('messageboard.urls')),

    # 学习笔记（本次补充的核心应用）
    # learningnotes/urls.py 里声明了 app_name='learningnotes'，
    # include 后自动形成命名空间，反向解析必须写 'learningnotes:xxx'。
    path('learning/', include('learningnotes.urls')),
]

# 开发环境由 Django 负责提供用户上传的媒体文件（生产环境应交给 Nginx 等）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

