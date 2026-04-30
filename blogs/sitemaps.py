from django.contrib.auth.models import User
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Blog, Category, Tag


class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Blog.objects.filter(status='Published').order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('blogs', args=[obj.slug])


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        return Category.objects.all().order_by('id')

    def location(self, obj):
        return reverse('posts_by_category', args=[obj.id])


class TagSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.4

    def items(self):
        return Tag.objects.all()

    def location(self, obj):
        return reverse('posts_by_tag', args=[obj.slug])


class AuthorSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.4

    def items(self):
        return User.objects.filter(blog__status='Published').distinct().order_by('username')

    def location(self, obj):
        return reverse('author_profile', args=[obj.username])


class StaticSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['home', 'post_list']

    def location(self, item):
        return reverse(item)


SITEMAPS = {
    'static': StaticSitemap,
    'posts': BlogSitemap,
    'categories': CategorySitemap,
    'tags': TagSitemap,
    'authors': AuthorSitemap,
}
