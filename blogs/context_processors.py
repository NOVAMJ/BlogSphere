from django.conf import settings

from .models import Category
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