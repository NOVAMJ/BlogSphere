from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse


def send_login_notification(user, request):
    """Send a login notification email to the user."""
    if not user.email:
        return
    site_url = getattr(settings, 'SITE_URL', f"{request.scheme}://{request.get_host()}")
    context = {
        'user': user,
        'site_url': site_url,
    }
    html_message = render_to_string('emails/login_notification.html', context)
    plain_message = strip_tags(html_message)
    try:
        send_mail(
            subject='New login to your BlogSphere account',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        pass


def send_featured_post_notification(post, email):
    """Send a featured post notification to a newsletter subscriber."""
    site_url = getattr(settings, 'SITE_URL', 'https://mriduldev.xyz').rstrip('/')
    try:
        post_url = reverse('blogs', kwargs={'slug': post.slug})
    except Exception:
        post_url = f'/blogs/{post.slug}/'
    context = {
        'post': post,
        'post_url': post_url,
        'site_url': site_url,
    }
    html_message = render_to_string('emails/featured_post.html', context)
    plain_message = strip_tags(html_message)
    try:
        send_mail(
            subject=f'Featured on BlogSphere: {post.title}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        pass


def send_newsletter_welcome(email, request):
    """Send a welcome email to a new newsletter subscriber."""
    site_url = getattr(settings, 'SITE_URL', f"{request.scheme}://{request.get_host()}")
    context = {
        'email': email,
        'site_url': site_url,
    }
    html_message = render_to_string('emails/newsletter_welcome.html', context)
    plain_message = strip_tags(html_message)
    try:
        send_mail(
            subject='Welcome to BlogSphere — you\'re on the list!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        pass
