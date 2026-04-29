from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .models import Blog, Category, Comment, Tag


class BlogListView(ListView):
    """Public list of published posts with search + pagination."""
    model = Blog
    template_name = 'posts_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        qs = Blog.objects.filter(status='Published').order_by('-created_at')
        keyword = self.request.GET.get('keyword', '').strip()
        if keyword:
            qs = qs.filter(
                Q(title__icontains=keyword)
                | Q(short_description__icontains=keyword)
                | Q(blog_body__icontains=keyword)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['keyword'] = self.request.GET.get('keyword', '')
        return ctx


class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blogs.html'
    context_object_name = 'single_blog'

    def get_queryset(self):
        return Blog.objects.filter(status='Published')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        blog = self.object
        comments = Comment.objects.filter(blog=blog)
        ctx['comments'] = comments
        ctx['comment_count'] = comments.count()
        ctx['liked'] = (
            self.request.user.is_authenticated
            and blog.likes.filter(pk=self.request.user.pk).exists()
        )
        ctx['total_likes'] = blog.total_likes()
        ctx['post_tags'] = blog.tags.all()
        ctx['related_posts'] = (
            Blog.objects.filter(status='Published', category=blog.category)
            .exclude(pk=blog.pk)
            .order_by('-created_at')[:3]
        )
        return ctx

    def post(self, request, *args, **kwargs):
        """Handle new comment submissions on the detail page."""
        self.object = self.get_object()
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        text = (request.POST.get('comment') or '').strip()
        if text:
            Comment.objects.create(user=request.user, blog=self.object, comment=text)
            messages.success(request, 'Comment posted.')
        return HttpResponseRedirect(request.path_info)


# Backwards-compatible function wrappers for existing URL names ----------

def blogs(request, slug):
    view = BlogDetailView.as_view()
    return view(request, slug=slug)


def posts_by_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    posts = Blog.objects.filter(status='Published', category=category).order_by('-created_at')
    return render(request, 'posts_by_category.html', {'posts': posts, 'category': category})


def search(request):
    keyword = request.GET.get('keyword', '').strip()
    blogs_qs = Blog.objects.filter(status='Published')
    if keyword:
        blogs_qs = blogs_qs.filter(
            Q(title__icontains=keyword)
            | Q(short_description__icontains=keyword)
            | Q(blog_body__icontains=keyword)
        )
    return render(request, 'search.html', {'blogs': blogs_qs, 'keyword': keyword})


# Comments ----------------------------------------------------------------

@login_required(login_url='login')
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    can_delete = (
        comment.user_id == request.user.id
        or request.user.is_superuser
        or request.user.has_perm('blogs.delete_comment')
    )
    if not can_delete:
        messages.error(request, "You can't delete this comment.")
        return redirect('blogs', slug=comment.blog.slug)
    blog_slug = comment.blog.slug
    comment.delete()
    messages.success(request, 'Comment deleted.')
    return redirect('blogs', slug=blog_slug)


# Likes (AJAX) ------------------------------------------------------------

@login_required(login_url='login')
@require_POST
def like_blog(request, slug):
    blog = get_object_or_404(Blog, slug=slug, status='Published')
    if blog.likes.filter(pk=request.user.pk).exists():
        blog.likes.remove(request.user)
        liked = False
    else:
        blog.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'total_likes': blog.total_likes()})


# Tags -------------------------------------------------------------------

def posts_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = (
        Blog.objects.filter(status='Published', tags=tag)
        .order_by('-created_at')
    )
    return render(request, 'posts_by_tag.html', {'tag': tag, 'posts': posts})


# Author profile ---------------------------------------------------------

def author_profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = (
        Blog.objects.filter(status='Published', author=author)
        .order_by('-created_at')
    )
    return render(
        request,
        'author_profile.html',
        {'author': author, 'posts': posts, 'post_count': posts.count()},
    )
