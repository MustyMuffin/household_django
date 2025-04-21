
# Django Deployment Checklist (Production - Debian 12 + PostgreSQL + Gunicorn + Nginx)

## 🔧 Code & Configuration
- [ ] Commit all code to GitHub.
- [ ] Use `.env` or `settings.py` to distinguish between dev and prod settings.
    - [ ] Disable `DEBUG`
    - [ ] Set `ALLOWED_HOSTS`
    - [ ] Configure static and media file paths
    - [ ] Use secure secret keys from environment variables
- [ ] Add production database settings (PostgreSQL) in `settings.py`.

## 📦 Dependencies
- [ ] Install all Python dependencies in a virtualenv (`pip install -r requirements.txt`).
- [ ] Install production-only tools like Gunicorn, psycopg2-binary, etc.

## 🗃️ Database
- [ ] Run `python manage.py makemigrations` (in dev).
- [ ] Push to GitHub.
- [ ] Pull on production server.
- [ ] Run `python manage.py migrate` on production.
- [ ] Create a superuser if needed (`python manage.py createsuperuser`).

## 🌐 Static/Media Files
- [ ] Collect static files with `python manage.py collectstatic`.
- [ ] Ensure `MEDIA_ROOT` and `STATIC_ROOT` are writable by your server.

## 🔐 Security Settings
- [ ] Use HTTPS (set up SSL cert with Let’s Encrypt via Certbot).
- [ ] Add security headers in `settings.py`:
    - `SECURE_SSL_REDIRECT = True`
    - `SESSION_COOKIE_SECURE = True`
    - `CSRF_COOKIE_SECURE = True`
    - `SECURE_HSTS_SECONDS = 31536000`
- [ ] Rotate secret keys periodically.

## 🚀 Gunicorn + Nginx
- [ ] Set up and test Gunicorn service (`systemd` unit).
- [ ] Configure Nginx as a reverse proxy.
- [ ] Point to your Gunicorn socket or port.
- [ ] Enable Nginx config and restart both services.

## 📈 Logging & Monitoring
- [ ] Set up logs for Gunicorn, Django, and Nginx.
- [ ] Consider monitoring tools like `htop`, `uptime`, `fail2ban`, or a third-party service.

## 🛠️ Post-Deploy Tests
- [ ] Test major user flows manually.
- [ ] Check permissions (static/media, db access).
- [ ] Hit endpoints to confirm functionality.
