# BlogSphere — Django Blog

## Overview
A Django-based blogging platform with categories, blog posts, comments, user authentication, and an admin dashboard for managing content.

## Tech Stack
- **Language**: Python 3.12
- **Framework**: Django 6.0
- **Database**: SQLite (`db.sqlite3`)
- **Forms**: django-crispy-forms with crispy-bootstrap4
- **Rich-text editor**: django-ckeditor (with built-in image uploader)
- **Image processing**: Pillow
- **Production server**: Gunicorn
- **Static files in production**: WhiteNoise (compressed manifest storage)
- **SEO**: django.contrib.sitemaps, robots.txt, OpenGraph + Twitter card meta

## Project Structure
- `blog_main/` — Django project settings, root URLs, and WSGI entry point
- `blogs/` — Blog app (Category, Blog, Comment models; views and templates context processors)
- `assignments/` — About info and social links
- `dashboards/` — Custom admin dashboard for managing users, posts, and categories
- `templates/` — HTML templates (public pages + `dashboard/` subfolder)
- `media/` — User-uploaded media (images for posts)
- `db.sqlite3` — SQLite database (committed to repo with seed data)

## Development
- The app runs via the `Start application` workflow:
  - Command: `python manage.py runserver 0.0.0.0:5000`
  - Port: 5000 (the only port exposed by Replit's preview)
- `ALLOWED_HOSTS = ['*']` and `CSRF_TRUSTED_ORIGINS` allow Replit's proxied preview domains.

## URL Highlights
- `/` — Homepage with featured and recent posts
- `/posts/` — All posts (search + pagination)
- `/blogs/<slug>/` — Single blog post detail (rich-text body, tags, related posts)
- `/category/<id>/` — Posts by category
- `/tag/<slug>/` — Posts by tag
- `/author/<username>/` — Public author profile (bio, avatar, posts)
- `/search/` — Search posts
- `/login/`, `/register/`, `/logout/` — Auth pages
- `/dashboard/` — Custom dashboard (login required) for posts, categories, users
- `/ckeditor/` — Image upload endpoint for the rich-text editor
- `/sitemap.xml` — Auto-generated sitemap (posts, categories, tags, authors)
- `/robots.txt` — Crawler rules
- `/admin/` — Django built-in admin

## Environment Variables (production)
Override these before deploying. Sensible dev defaults are used when unset.
- `SECRET_KEY` — Django secret key (required for production)
- `DEBUG` — `True`/`False`; defaults to `True` for development
- `SITE_URL` — Public site URL used for absolute links

## Deployment
- Target: **Autoscale** (stateless web app)
- Run: `gunicorn --bind=0.0.0.0:5000 --reuse-port blog_main.wsgi:application`

## Roles & RBAC
Four groups are seeded by migration `blogs/0008_create_rbac_groups.py`:

| Group   | Permissions |
|---------|-------------|
| Admin   | Full access to blogs, categories, comments, users, groups |
| Manager | Full blog/category CRUD + user management; can moderate comments |
| Editor  | Full blog CRUD on any post; can moderate comments |
| Author  | Add/edit/delete **own** posts only (ownership enforced in dashboard views) |

Group membership is assigned via the Django admin or `/dashboard/users/`.

## Likes & Comments
- Likes are a `Blog.likes` ManyToMany on `User`; toggled via `POST /blogs/<slug>/like/` (returns JSON, used by an inline `fetch` in `templates/blogs.html`).
- Comments: authenticated users post via the form on the blog detail page. Comment authors (and users with `delete_comment` permission, or superusers) can delete via `POST /comments/<id>/delete/`.

## Public URLs (added)
- `/posts/` — `BlogListView` with `?keyword=` search and 10-per-page pagination.
- `/blogs/<slug>/like/` — like/unlike toggle (POST, JSON).
- `/comments/<id>/delete/` — delete comment (POST).

## Recent Changes
- 2026-04-30: Added social login (Google + GitHub) via `django-allauth`. Mounted at `/accounts/`. Provider credentials are read from `GOOGLE_OAUTH_CLIENT_ID/SECRET` and `GITHUB_OAUTH_CLIENT_ID/SECRET` env vars; the buttons on `/login/` and `/register/` only appear when the matching env var is set, so the site degrades gracefully if a provider isn't configured.
- 2026-04-29: Initial Replit setup. Installed dependencies, set `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` for the Replit proxy, configured the workflow on port 5000, and added gunicorn for autoscale deployment.
- 2026-04-29: Major upgrade — added Category.slug + Blog.likes (with auto-slug on save), refactored public blog views to class-based (`BlogListView`/`BlogDetailView`) with search + pagination, added comment-delete and AJAX like endpoints, seeded RBAC groups (Admin/Manager/Editor/Author), restricted dashboard category/user CRUD to Admin/Manager, scoped author dashboard to own posts, gated edit/delete buttons on permissions, and changed login redirect to homepage (with `?next=` support).
- 2026-04-30: Production polish — hero banner on homepage, reading time + view counter on posts, social share bar (Twitter/Facebook/LinkedIn/WhatsApp/Copy), full SEO suite (sitemap.xml, robots.txt, OpenGraph + Twitter card meta), WhiteNoise for static files, env-var-driven SECRET_KEY/DEBUG, conditional production security hardening (HSTS, secure cookies, SSL redirect).
