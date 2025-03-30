from django.shortcuts import render, redirect
from .models import Message

def index(request):
    if request.method == 'POST':
        content = request.POST.get('content', '')
        Message.objects.create(content=content)
        return redirect('index')
    messages = Message.objects.all().order_by('-created_at')
    return render(request, 'messageboard/index.html', {'messages': messages})
