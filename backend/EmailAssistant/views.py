"""
views.py - AI Email Assistant

Flow:
  0. gmail_setup_view    -> (first-time) shows step-by-step guide to get a
                             Gmail App Password and saves it to GmailConfig.
                             All other views redirect here if no config found.

  1. email_form_view     -> user fills Receiver / Topic / Category / Tone /
                             Length / Quality Level (Steps 1-6).
                             Sender email is auto-fetched from request.user.email.

  2. email_preview_view  -> shows the AI-generated email (editable Subject/Body).

  3. email_confirm_view  -> JS Yes/No modal, then POSTs here to actually send.
                             Uses the user's own Gmail + App Password via SMTP.

  4. email_history_view  -> user's own sent/failed history with search + filter.

Session key EMAIL_DRAFT carries the generated email across preview → confirm.
"""

import json
import mimetypes
from datetime import timedelta
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import GmailConfigForm, EmailRequestForm, EmailEditForm, SignUpForm
from .models import GmailConfig, EmailHistory
from .email_generator import generate_email


EMAIL_DRAFT = "email_assistant_draft"


def _save_uploaded_attachments(uploaded_files):
    """Persist uploaded files to storage and return metadata for the draft."""
    saved_attachments = []
    for uploaded in uploaded_files:
        if not uploaded or not getattr(uploaded, "name", None):
            continue
        safe_name = uploaded.name.replace(" ", "_")
        file_name = f"{uuid4().hex}_{safe_name}"
        saved_path = default_storage.save(f"attachments/{file_name}", uploaded)
        saved_attachments.append({
            "name": uploaded.name,
            "path": saved_path,
        })
    return saved_attachments


def _ensure_draft_attachments(draft):
    """Carry forward attachment metadata across preview/confirm steps."""
    if "attachments" not in draft:
        draft["attachments"] = []
    return draft


# ======================================================================
# SIGNUP
# ======================================================================

def signup_view(request):
    """
    New-account registration. Logs the user straight in afterwards and
    sends them to Gmail Setup, since every account needs an App Password
    before it can do anything else.
    """

    if request.user.is_authenticated:
        return redirect("emailassistant:form")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Now set up your Gmail App Password.")
            return redirect("emailassistant:gmail_setup")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


# ======================================================================
# 0. GMAIL SETUP
# ======================================================================

@login_required
def gmail_setup_view(request):
    """
    Step 0 – shown the very first time (or whenever user wants to update).

    Displays a visual step-by-step guide on how to get a Gmail App Password,
    then a form to paste it. The Gmail address is auto-fetched from
    request.user.email and shown read-only.
    """

    # Try to load existing config so we can pre-fill the form
    try:
        config = GmailConfig.objects.get(user=request.user)
    except GmailConfig.DoesNotExist:
        config = None

    if request.method == "POST":
        form = GmailConfigForm(request.POST, instance=config)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(
                request,
                "Gmail App Password saved! You can now compose and send emails."
            )
            return redirect("emailassistant:form")
        else:
            messages.error(request, "Please fix the error below.")
    else:
        form = GmailConfigForm(instance=config)

    return render(request, "emailassistant/gmail_setup.html", {
        "form": form,
        "sender_email": request.user.email,
        "has_config": config is not None,
    })


# ======================================================================
# 1. COMPOSE FORM  (Steps 1-6)
# ======================================================================

@login_required
def email_form_view(request):
    """
    Steps 1-6: collect Receiver / Topic / Category / Tone / Length / Level.
    Redirects to gmail_setup if the user has not yet saved an App Password.
    """

    # Gate: must have Gmail config first
    if not GmailConfig.objects.filter(user=request.user).exists():
        messages.info(
            request,
            "Please set up your Gmail App Password before composing an email."
        )
        return redirect("emailassistant:gmail_setup")

    if request.method == "POST":
        form = EmailRequestForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            attachment_sources = []
            if request.FILES:
                attachment_sources = request.FILES.getlist("attachments")
            if not attachment_sources:
                attachment_sources = data.get("attachments", [])
            attachment_data = _save_uploaded_attachments(attachment_sources)

            # Work out the specific situation the user picked (or typed),
            # and the reliable template key for their chosen Topic.
            topic_detail = form.get_topic_detail()
            topic_key    = form.get_topic_key()

            # A readable combined topic string for history/preview display,
            # e.g. "Complaint — a defective product I received".
            if topic_detail:
                topic_display = f"{data['topic']} — {topic_detail}"[:200]
            else:
                topic_display = data["topic"]

            # Generate email offline — zero API calls
            generated = generate_email(
                receiver_email=data["receiver_email"],
                sender_email=request.user.email,
                topic=data["topic"],
                category=data["category"],
                tone=data["tone"],
                length=data["length"],
                premium_level=data["premium_level"],
                sender_name=request.user.get_full_name() or request.user.username,
                topic_key=topic_key,
                topic_detail=topic_detail,
            )

            # Save draft to session for the next two steps
            draft = {
                "subject":       generated["subject"],
                "body":          generated["body"],
                "receiver_email": data["receiver_email"],
                "topic":         topic_display,
                "category":      data["category"],
                "tone":          data["tone"],
                "length":        data["length"],
                "premium_level": data["premium_level"],
                "attachments":   attachment_data,
            }
            request.session[EMAIL_DRAFT] = draft
            return redirect("emailassistant:preview")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = EmailRequestForm()

    return render(request, "emailassistant/form.html", {
        "form": form,
        "sender_email": request.user.email,
        "subtopics_json": json.dumps(EmailRequestForm.SUBTOPICS),
        "custom_subtopic_value": EmailRequestForm.CUSTOM_SUBTOPIC_VALUE,
    })


# ======================================================================
# 2. PREVIEW + EDIT
# ======================================================================

@login_required
def email_preview_view(request):
    """Shows the generated email; user can edit Subject/Body before sending."""

    draft = request.session.get(EMAIL_DRAFT)
    if not draft:
        messages.warning(request, "No draft found. Please start over.")
        return redirect("emailassistant:form")

    draft = _ensure_draft_attachments(draft)
    request.session[EMAIL_DRAFT] = draft

    if request.method == "POST":
        form = EmailEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            draft = _ensure_draft_attachments(draft)
            draft.update({
                "subject":       data["subject"],
                "body":          data["body"],
                "receiver_email": data["receiver_email"],
                "topic":         data["topic"],
                "category":      data["category"],
                "tone":          data["tone"],
                "length":        data["length"],
                "premium_level": data["premium_level"],
            })
            request.session[EMAIL_DRAFT] = draft
            return redirect("emailassistant:confirm")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = EmailEditForm(initial=draft)

    return render(request, "emailassistant/preview.html", {
        "form": form,
        "sender_email": request.user.email,
        "draft": draft,
    })


# ======================================================================
# 3. CONFIRM + SEND
# ======================================================================

@login_required
def email_confirm_view(request):
    """
    Shows the final email preview with a YES/NO modal.
    On YES (POST), sends via the user's own Gmail SMTP + App Password.
    Saves result to EmailHistory regardless of success or failure.
    """

    draft = request.session.get(EMAIL_DRAFT)
    if not draft:
        messages.warning(request, "No draft found. Please start over.")
        return redirect("emailassistant:form")

    draft = _ensure_draft_attachments(draft)
    request.session[EMAIL_DRAFT] = draft

    if request.method == "POST":

        # Fetch the saved App Password for this user
        try:
            config = GmailConfig.objects.get(user=request.user)
        except GmailConfig.DoesNotExist:
            messages.error(
                request,
                "Gmail App Password not found. Please set it up again."
            )
            return redirect("emailassistant:gmail_setup")

        gmail_address = request.user.email
        app_password  = config.clean_password()   # strips spaces

        status        = "FAILED"
        error_message = None

        try:
            # Build a one-off SMTP connection using THIS user's credentials.
            # This does NOT touch the project-wide settings.py EMAIL_* values.
            connection = SMTPBackend(
                host="smtp.gmail.com",
                port=587,
                username=gmail_address,
                password=app_password,
                use_tls=True,
                fail_silently=False,
            )

            msg = EmailMessage(
                subject=draft["subject"],
                body=draft["body"],
                from_email=gmail_address,
                to=[draft["receiver_email"]],
                connection=connection,
            )

            for attachment in draft.get("attachments", []):
                file_path = attachment.get("path")
                if not file_path or not default_storage.exists(file_path):
                    continue
                with default_storage.open(file_path, "rb") as handle:
                    content = handle.read()
                mime_type, _ = mimetypes.guess_type(attachment.get("name", ""))
                if not mime_type:
                    mime_type = "application/octet-stream"
                msg.attach(attachment.get("name", "attachment"), content, mime_type)
            msg.send()
            status = "SENT"
            messages.success(request, "Email sent successfully! 🎉")

        except Exception as exc:
            # Catches wrong password, 2FA not enabled, network errors, etc.
            error_message = str(exc)

            # Give the user a friendlier hint for the most common mistakes
            hint = ""
            err_lower = error_message.lower()
            if "username and password" in err_lower or "535" in err_lower:
                hint = (
                    " — It looks like your App Password is incorrect or Gmail "
                    "rejected it. Please go to Gmail Setup and re-enter it."
                )
            elif "smtplib" in err_lower or "connection" in err_lower:
                hint = " — Could not connect to Gmail. Please check your internet connection."

            messages.error(request, f"Email could not be sent: {error_message}{hint}")

        # Always log to history (Sent or Failed)
        EmailHistory.objects.create(
            user=request.user,
            sender_email=gmail_address,
            receiver_email=draft["receiver_email"],
            subject=draft["subject"],
            body=draft["body"],
            topic=draft["topic"],
            category=draft["category"],
            tone=draft["tone"],
            length=draft["length"],
            premium_level=draft["premium_level"],
            status=status,
            error_message=error_message,
        )

        # Clear the draft now that it's been processed
        if EMAIL_DRAFT in request.session:
            del request.session[EMAIL_DRAFT]

        return redirect("emailassistant:history")

    return render(request, "emailassistant/confirm.html", {
        "draft": draft,
        "sender_email": request.user.email,
    })


# ======================================================================
# 4. HISTORY
# ======================================================================

@login_required
def email_history_view(request):
    """
    Shows only the current user's history — newest first.
    Supports search by receiver / subject / topic and date filters.
    """

    history = EmailHistory.objects.filter(user=request.user)

    query = request.GET.get("q", "").strip()
    if query:
        from django.db.models import Q
        history = history.filter(
            Q(receiver_email__icontains=query)
            | Q(subject__icontains=query)
            | Q(topic__icontains=query)
        )

    date_filter = request.GET.get("filter", "all")
    now = timezone.now()
    if date_filter == "today":
        history = history.filter(created_at__date=now.date())
    elif date_filter == "7days":
        history = history.filter(created_at__gte=now - timedelta(days=7))
    elif date_filter == "month":
        history = history.filter(created_at__gte=now - timedelta(days=30))

    # Check if user has Gmail set up (shown as a banner)
    has_gmail_config = GmailConfig.objects.filter(user=request.user).exists()

    return render(request, "emailassistant/history.html", {
        "history":          history,
        "query":            query,
        "date_filter":      date_filter,
        "has_gmail_config": has_gmail_config,
    })
