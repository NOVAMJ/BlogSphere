from django.db import migrations


GROUP_PERMISSIONS = {
    # Admin: full access to blogs/categories/comments/users/groups
    "Admin": [
        ("blogs", "blog", ["add", "change", "delete", "view"]),
        ("blogs", "category", ["add", "change", "delete", "view"]),
        ("blogs", "comment", ["add", "change", "delete", "view"]),
        ("auth", "user", ["add", "change", "delete", "view"]),
        ("auth", "group", ["add", "change", "delete", "view"]),
    ],
    # Manager: manage users + posts (no group mgmt)
    "Manager": [
        ("blogs", "blog", ["add", "change", "delete", "view"]),
        ("blogs", "category", ["add", "change", "delete", "view"]),
        ("blogs", "comment", ["change", "delete", "view"]),
        ("auth", "user", ["add", "change", "delete", "view"]),
    ],
    # Editor: edit all posts; no user mgmt
    "Editor": [
        ("blogs", "blog", ["add", "change", "delete", "view"]),
        ("blogs", "category", ["view"]),
        ("blogs", "comment", ["change", "delete", "view"]),
    ],
    # Author: create + edit own posts (ownership enforced in views)
    "Author": [
        ("blogs", "blog", ["add", "change", "delete", "view"]),
        ("blogs", "category", ["view"]),
        ("blogs", "comment", ["add", "delete", "view"]),
    ],
}


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    for group_name, perms_spec in GROUP_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        perm_objs = []
        for app_label, model_name, actions in perms_spec:
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
            except ContentType.DoesNotExist:
                continue
            for action in actions:
                codename = f"{action}_{model_name}"
                try:
                    perm_objs.append(Permission.objects.get(content_type=ct, codename=codename))
                except Permission.DoesNotExist:
                    pass
        group.permissions.set(perm_objs)


def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=list(GROUP_PERMISSIONS.keys())).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blogs", "0007_category_slug_unique"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
