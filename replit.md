# BlogSphere — Django Blog

## Overview
A Django-based blogging platform with categories, blog posts, comments, user authentication, and an admin dashboard for managing content.

## Tech Stack
- **Language**: Python 3.12
- **Framework**: Django 6.0
- **Database**: SQLite (`db.sqlite3`)
- **Forms**: django-crispy-forms with crispy-bootstrap4
- **Image processing**: Pillow
- **Production server**: Gunicorn

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
- `/blogs/<slug>/` — Single blog post detail
- `/category/<id>/` — Posts by category
- `/search/` — Search posts
- `/login/`, `/register/`, `/logout/` — Auth pages
- `/dashboard/` — Custom dashboard (login required) for posts, categories, users
- `/admin/` — Django built-in admin

## Deployment
- Target: **Autoscale** (stateless web app)
- Run: `gunicorn --bind=0.0.0.0:5000 --reuse-port blog_main.wsgi:application`

## Recent Changes
- 2026-04-29: Initial Replit setup. Installed dependencies, set `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` for the Replit proxy, configured the workflow on port 5000, and added gunicorn for autoscale deployment.
