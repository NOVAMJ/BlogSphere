from django.conf import settings
from django.db.models import Count, Q

from .models import Category, Tag
from assignments.models import SocialLink

def get_categories(request):
    categories = Category.objects.all()
    return dict(categories=categories)


def get_social_links(request):
    social_links = SocialLink.objects.all()
    return dict(social_links=social_links)


def oauth_flags(request):
    """Expose which OAuth providers are configured to all templates."""
    return {
        'google_oauth_enabled': getattr(settings, 'GOOGLE_OAUTH_ENABLED', False),
        'github_oauth_enabled': getattr(settings, 'GITHUB_OAUTH_ENABLED', False),
    }


def popular_tags(request):
    """Top tags by number of published posts — used by the footer and sidebar."""
    tags = (
        Tag.objects
        .annotate(post_count=Count('blogs', filter=Q(blogs__status='Published')))
        .filter(post_count__gt=0)
        .order_by('-post_count', 'name')[:12]
    )
    return {'popular_tags': tags}