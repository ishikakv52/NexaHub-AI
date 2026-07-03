# AI Email Assistant — Integration Guide (NEXA HUB AI)

This is a self-contained Django app. It does **not** touch any of your existing
apps (VoiceAssistant, ImageToText, DietPlanner, subscriptions, etc.). Follow
these 4 steps to plug it in.

## 1. Copy the folder

Copy the whole `EmailAssistant/` folder into your `backend/` directory, next
to your other apps, so it looks like:

```
backend/
    EmailAssistant/
        __init__.py
        admin.py
        apps.py
        forms.py
        models.py
        urls.py
        views.py
        email_generator.py
        migrations/
            __init__.py
        templates/
            emailassistant/
                form.html
                preview.html
                confirm.html
                history.html
    config/
        settings.py
        urls.py
    ...your other existing apps...
```

## 2. Register the app — `config/settings.py`

Add `"EmailAssistant"` to `INSTALLED_APPS` (do not remove anything else):

```python
INSTALLED_APPS = [
    ...
    "EmailAssistant",
]
```

## 3. Add SMTP email settings — `config/settings.py`

If you don't already have email settings, add these (example uses Gmail SMTP
— swap in your own provider/credentials, ideally from environment variables):

```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your-app-email@gmail.com"
EMAIL_HOST_PASSWORD = "your-app-password"   # use a Gmail App Password, not your normal password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

Note: the assistant always sends **using the logged-in user's own email as
the "From" address** in the message itself (`request.user.email`), as
required. `EMAIL_HOST_USER` above is just the SMTP login account that
physically relays the message — that's how SMTP works.

## 4. Wire up the URLs — `config/urls.py`

```python
from django.urls import path, include

urlpatterns = [
    ...
    path("email-assistant/", include("EmailAssistant.urls")),
]
```

## 5. Run migrations

```bash
python manage.py makemigrations EmailAssistant
python manage.py migrate
```

## 6. Visit it

```
http://127.0.0.1:8000/email-assistant/          -> compose form
http://127.0.0.1:8000/email-assistant/history/   -> history page
```

---

## Notes on design choices

- **No REST API / no JSON / no AJAX**: Every step is a normal Django view
  that renders an HTML template and uses normal `<form method="post">`
  submissions. Django Sessions carry the generated draft between the
  Compose → Preview → Confirm steps.
- **Steps 1–6 combined into one form page** (`form.html`) instead of a
  multi-page wizard, to keep things simple and beginner-friendly while still
  collecting every field (Receiver, Topic, Category, Tone, Length, Quality
  Level) before generating the email — exactly as specified.
- **Confirmation box** on the final page is plain vanilla JavaScript (no
  libraries) — it shows a "Are you sure you want to send this email?" modal
  with YES/NO. NO just closes the modal; YES submits the real form, which
  triggers the SMTP send server-side.
- **`email_generator.py`** is fully offline — keyword-based topic detection
  (Leave, Job, Complaint, Meeting, Internship, Proposal, Resignation,
  Invitation, Cold Email, Follow Up, Thank You, Congratulations, Festival,
  Birthday, Reminder, Support, Refund, Order Delay, Project Update,
  Feedback, Payment Reminder, Sales, Marketing, Apology, Promotion Request,
  and a generic fallback) combined with random greetings/openings/
  transitions/closings/signatures so repeated generations for the same
  topic look different each time.
- **Security**: every view is `@login_required`; history is always filtered
  by `user=request.user`; all forms use Django's built-in CSRF protection
  automatically (`{% csrf_token %}`).
- **Error handling**: SMTP/auth/connection errors are caught in
  `email_confirm_view`, shown to the user via Django messages, and the
  attempt is still logged to history with `status="FAILED"` and the error
  message saved.

## Extending the generator further

To add more topic families, just add a new entry to `TOPIC_KEYWORDS` and a
matching entry to `TEMPLATES` in `email_generator.py` — the rest of the
engine (greetings, transitions, closings, length/premium logic) will apply
automatically to your new topic.
