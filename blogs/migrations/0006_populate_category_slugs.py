from django.db import migrations
from django.template.defaultfilters import slugify


def populate_slugs(apps, schema_editor):
    Category = apps.get_model("blogs", "Category")
    used = set()
    for cat in Category.objects.all():
        if cat.slug:
            used.add(cat.slug)
            continue
        base = slugify(cat.category_name) or f"category-{cat.pk}"
        slug = base
        n = 1
        while slug in used or Category.objects.filter(slug=slug).exclude(pk=cat.pk).exists():
            n += 1
            slug = f"{base}-{n}"
        cat.slug = slug
        used.add(slug)
        cat.save(update_fields=["slug"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("blogs", "0005_blog_likes_category_slug_nullable"),
    ]

    operations = [
        migrations.RunPython(populate_slugs, noop),
    ]
