from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import pre_save, post_save
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


# ---- Featured post newsletter -----------------------------------------------

@receiver(pre_save, sender='blogs.Blog')
def capture_old_featured_state(sender, instance, **kwargs):
    """Store the previous is_featured value on the instance before saving."""
    if instance.pk:
        try:
            instance._was_featured = sender.objects.filter(pk=instance.pk).values_list('is_featured', flat=True).first()
        except Exception:
            instance._was_featured = False
    else:
        instance._was_featured = False


@receiver(post_save, sender='blogs.Blog')
def notify_subscribers_on_feature(sender, instance, created, **kwargs):
    """
    When a blog post is marked as featured for the first time
    (is_featured flips from False → True), email all active
    newsletter subscribers automatically.
    """
    was_featured = getattr(instance, '_was_featured', False)
    if instance.is_featured and not was_featured:
        from .emails import send_featured_post_notification
        from .models import NewsletterSubscriber
        subscribers = NewsletterSubscriber.objects.filter(is_active=True).values_list('email', flat=True)
        for email in subscribers:
            send_featured_post_notification(instance, email)
