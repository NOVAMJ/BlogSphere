from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def assign_default_author_group(sender, instance, created, **kwargs):
    """
    When a new user signs up (regular form, social login, or admin
    creation), automatically add them to the 'Author' group so they
    can immediately create their own blog posts.

    Superusers and staff are skipped because they already have
    elevated permissions.
    """
    if not created:
        return
    if instance.is_superuser or instance.is_staff:
        return
    try:
        author_group = Group.objects.get(name='Author')
    except Group.DoesNotExist:
        return
    instance.groups.add(author_group)
