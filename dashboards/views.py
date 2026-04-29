from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify

from blogs.models import Blog, Category, Comment

from .forms import AddUserForm, BlogPostForm, CategoryForm, EditUserForm


# ---- Helpers ------------------------------------------------------------

def _is_admin_or_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Admin', 'Manager']).exists()


def _can_edit_any_post(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Admin', 'Manager', 'Editor']).exists()


def _ensure_can_edit_post(user, post):
    if _can_edit_any_post(user):
        return
    if post.author_id == user.id and user.has_perm('blogs.change_blog'):
        return
    raise PermissionDenied


# ---- Dashboard home -----------------------------------------------------

@login_required(login_url='login')
def dashboard(request):
    is_priv = _can_edit_any_post(request.user)
    if is_priv:
        category_count = Category.objects.count()
        blogs_count = Blog.objects.count()
        comments_count = Comment.objects.count()
        recent_posts = Blog.objects.all().order_by('-created_at')[:5]
    else:
        category_count = Category.objects.count()
        blogs_count = Blog.objects.filter(author=request.user).count()
        comments_count = Comment.objects.filter(blog__author=request.user).count()
        recent_posts = Blog.objects.filter(author=request.user).order_by('-created_at')[:5]
    context = {
        'category_count': category_count,
        'blogs_count': blogs_count,
        'comments_count': comments_count,
        'recent_posts': recent_posts,
        'is_priv': is_priv,
    }
    return render(request, 'dashboard/dashboard.html', context)


# ---- Categories (Admin/Manager only) ------------------------------------

@login_required(login_url='login')
def categories(request):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    cats = Category.objects.all().order_by('category_name')
    return render(request, 'dashboard/categories.html', {'categories_list': cats})


@login_required(login_url='login')
def add_category(request):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added.')
            return redirect('categories')
    else:
        form = CategoryForm()
    return render(request, 'dashboard/add_category.html', {'form': form})


@login_required(login_url='login')
def edit_category(request, pk):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'dashboard/edit_category.html', {'form': form, 'category': category})


@login_required(login_url='login')
def delete_category(request, pk):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, 'Category deleted.')
    return redirect('categories')


# ---- Posts --------------------------------------------------------------

@login_required(login_url='login')
def posts(request):
    if _can_edit_any_post(request.user):
        post_list = Blog.objects.all().order_by('-created_at')
    else:
        # Authors see only their own posts
        post_list = Blog.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'dashboard/posts.html', {'posts': post_list})


@login_required(login_url='login')
@permission_required('blogs.add_blog', raise_exception=True)
def add_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # Refresh slug to include the id (preserves original behaviour)
            post.slug = slugify(form.cleaned_data['title']) + '-' + str(post.id)
            post.save()
            messages.success(request, 'Post created.')
            return redirect('posts')
    else:
        form = BlogPostForm()
    return render(request, 'dashboard/add_post.html', {'form': form})


@login_required(login_url='login')
def edit_post(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    _ensure_can_edit_post(request.user, post)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            post.slug = slugify(form.cleaned_data['title']) + '-' + str(post.id)
            post.save()
            messages.success(request, 'Post updated.')
            return redirect('posts')
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'dashboard/edit_post.html', {'form': form, 'post': post})


@login_required(login_url='login')
def delete_post(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    _ensure_can_edit_post(request.user, post)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('posts')


# ---- Users (Admin/Manager only) -----------------------------------------

@login_required(login_url='login')
def users(request):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    users_list = User.objects.all().order_by('username')
    return render(request, 'dashboard/users.html', {'users': users_list})


@login_required(login_url='login')
def add_user(request):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created.')
            return redirect('users')
    else:
        form = AddUserForm()
    return render(request, 'dashboard/add_user.html', {'form': form})


@login_required(login_url='login')
def edit_user(request, pk):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated.')
            return redirect('users')
    else:
        form = EditUserForm(instance=user)
    return render(request, 'dashboard/edit_user.html', {'form': form})


@login_required(login_url='login')
def delete_user(request, pk):
    if not _is_admin_or_manager(request.user):
        raise PermissionDenied
    user = get_object_or_404(User, pk=pk)
    user.delete()
    messages.success(request, 'User deleted.')
    return redirect('users')
