
import time

from django.conf import settings
from django.shortcuts import redirect, render

from blogs.models import Blog, Category
from assignments.models import About
from .forms import RegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth


def _is_login_locked(request):
    """Return True if this session has exceeded the allowed failed attempts."""
    attempts = request.session.get('login_attempts', 0)
    lockout_until = request.session.get('login_lockout_until', 0)
    max_attempts = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
    lockout_seconds = getattr(settings, 'LOGIN_LOCKOUT_SECONDS', 60)

    if lockout_until and time.time() < lockout_until:
        return True
    # Reset if lockout has expired
    if lockout_until and time.time() >= lockout_until:
        request.session['login_attempts'] = 0
        request.session['login_lockout_until'] = 0
    return False


def _record_failed_login(request):
    """Increment the failed-attempt counter and lock out if needed."""
    max_attempts = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
    lockout_seconds = getattr(settings, 'LOGIN_LOCKOUT_SECONDS', 60)
    attempts = request.session.get('login_attempts', 0) + 1
    request.session['login_attempts'] = attempts
    if attempts >= max_attempts:
        request.session['login_lockout_until'] = time.time() + lockout_seconds

def home(request):
    featured_posts = Blog.objects.filter(is_featured=True, status='Published').order_by('-updated_at')
    posts = Blog.objects.filter(is_featured=False, status='Published')
    
    # Fetch about us
    try:
        about = About.objects.get()
    except:
        about = None
    context = {
        'featured_posts': featured_posts,
        'posts': posts,
        'about': about,
    }
    return render(request, 'home.html', context)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('register')
        else:
            print(form.errors)
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'register.html', context)


def login(request):
    if _is_login_locked(request):
        return render(request, '403.html', {'lockout': True}, status=429)

    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                request.session.pop('login_attempts', None)
                request.session.pop('login_lockout_until', None)
                auth.login(request, user)
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            else:
                _record_failed_login(request)
    else:
        form = AuthenticationForm()
    context = {
        'form': form,
        'next': request.GET.get('next', ''),
    }
    return render(request, 'login.html', context)


def logout(request):
    auth.logout(request)
    return redirect('home')


def error_403(request, exception=None):
    return render(request, '403.html', status=403)


def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)