from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count, F, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .models import Blog, Category, Comment, ContactMessage, NewsletterSubscriber, Tag


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

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count once per session, skipping the author themselves.
        blog = self.object
        seen = request.session.get('viewed_blogs', [])
        if blog.pk not in seen and request.user.id != blog.author_id:
            Blog.objects.filter(pk=blog.pk).update(views=F('views') + 1)
            seen.append(blog.pk)
            request.session['viewed_blogs'] = seen[-200:]
            blog.views = (blog.views or 0) + 1
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        blog = self.object
        # Top-level comments only; replies are accessed via comment.replies.all
        top_comments = (
            Comment.objects
            .filter(blog=blog, parent__isnull=True)
            .select_related('user', 'user__profile')
            .prefetch_related('replies__user', 'replies__user__profile')
            .order_by('-created_at')
        )
        ctx['comments'] = top_comments
        ctx['comment_count'] = Comment.objects.filter(blog=blog).count()
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
        # SEO meta
        request = self.request
        absolute_image = ''
        if blog.featured_image:
            absolute_image = request.build_absolute_uri(blog.featured_image.url)
        ctx['meta_title'] = f"{blog.title} — BlogSphere"
        ctx['meta_description'] = (blog.short_description or strip_tags(blog.blog_body or ''))[:160]
        ctx['meta_image'] = absolute_image
        ctx['meta_type'] = 'article'
        return ctx

    def post(self, request, *args, **kwargs):
        """Handle new comment submissions on the detail page (with optional reply parent)."""
        self.object = self.get_object()
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        text = (request.POST.get('comment') or '').strip()
        parent_id = request.POST.get('parent_id') or None
        parent = None
        if parent_id:
            parent = Comment.objects.filter(pk=parent_id, blog=self.object).first()
            # Only allow one level of nesting — replies to replies attach to the original parent.
            if parent and parent.parent_id:
                parent = parent.parent
        if text:
            Comment.objects.create(
                user=request.user,
                blog=self.object,
                comment=text,
                parent=parent,
            )
            messages.success(request, 'Reply posted.' if parent else 'Comment posted.')
        return HttpResponseRedirect(request.path_info + '#comments')


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


# Newsletter -------------------------------------------------------------

@require_POST
def newsletter_subscribe(request):
    email = (request.POST.get('email') or '').strip().lower()
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, 'Please enter a valid email address.')
        return redirect(next_url)
    sub, created = NewsletterSubscriber.objects.get_or_create(
        email=email, defaults={'is_active': True}
    )
    if not created and not sub.is_active:
        sub.is_active = True
        sub.save(update_fields=['is_active'])
    if created:
        messages.success(request, "You're subscribed — welcome to BlogSphere!")
    else:
        messages.info(request, "You're already on the list. Thanks for sticking with us!")
    return redirect(next_url)


# Contact / Static info pages -------------------------------------------

def contact(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        subject = (request.POST.get('subject') or '').strip()
        message = (request.POST.get('message') or '').strip()
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'contact.html', {
                'form_data': {'name': name, 'email': email, 'subject': subject, 'message': message},
            })
        if not name or not message:
            messages.error(request, 'Name and message are required.')
            return render(request, 'contact.html', {
                'form_data': {'name': name, 'email': email, 'subject': subject, 'message': message},
            })
        ContactMessage.objects.create(
            name=name[:100],
            email=email,
            subject=subject[:150],
            message=message[:2000],
        )
        messages.success(request, "Thanks! Your message reached us — we'll get back soon.")
        return redirect('contact')
    return render(request, 'contact.html')


def privacy(request):
    return render(request, 'privacy.html')


def terms(request):
    return render(request, 'terms.html')
