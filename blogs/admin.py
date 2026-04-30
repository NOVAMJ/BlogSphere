from django.contrib import admin
from .models import (
    Blog,
    Category,
    Comment,
    ContactMessage,
    NewsletterSubscriber,
    Profile,
    Tag,
)


class BlogAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'category', 'author', 'status', 'is_featured', 'views')
    search_fields = ('id', 'title', 'category__category_name', 'status')
    list_filter = ('status', 'is_featured', 'category', 'tags')
    list_editable = ('is_featured',)
    filter_horizontal = ('tags', 'likes')


class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug', 'created_at')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'blog', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment', 'user__username', 'blog__title')


class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('email',)


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_handled', 'created_at')
    list_filter = ('is_handled', 'created_at')
    list_editable = ('is_handled',)
    search_fields = ('name', 'email', 'subject', 'message')


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'website', 'updated_at')
    search_fields = ('user__username', 'bio')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(Profile, ProfileAdmin)
