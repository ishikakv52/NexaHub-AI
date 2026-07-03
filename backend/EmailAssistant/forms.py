"""
forms.py - AI Email Assistant

Three forms:
1. GmailConfigForm  -> Gmail App Password setup (one-time per user)
2. EmailRequestForm -> Steps 1-6 (Receiver, Topic, Category, Tone, Length, Premium Level)
3. EmailEditForm    -> Preview page edit before send
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import EmailHistory, GmailConfig


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if name in files:
            return files.getlist(name)
        return super().value_from_datadict(data, files, name)


class MultipleFileField(forms.FileField):
    """Accept one or more uploaded files from the same input."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if data in (None, ""):
            return []
        if isinstance(data, (list, tuple)):
            files = []
            for item in data:
                if item in (None, ""):
                    continue
                files.append(super().clean(item, initial))
            return files
        if hasattr(data, "read"):
            return [super().clean(data, initial)]
        return [super().clean(data, initial)]


class SignUpForm(UserCreationForm):
    """
    Registration form. Email is REQUIRED and must be unique — the rest of
    the app auto-fetches request.user.email and uses it as the Gmail
    address that sends mail, so every account needs a real, unique email.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "you@gmail.com",
            "class": "form-input",
            "autofocus": True,
        }),
        help_text="Use your Gmail address — this is what your emails will be sent from.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "placeholder": "Choose a username",
            "class": "form-input",
        })
        self.fields["password1"].widget.attrs.update({
            "placeholder": "Create a password",
            "class": "form-input",
        })
        self.fields["password2"].widget.attrs.update({
            "placeholder": "Confirm password",
            "class": "form-input",
        })

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class GmailConfigForm(forms.ModelForm):
    """
    Lets the user enter their 16-character Gmail App Password.
    The Gmail address itself is auto-fetched from request.user.email
    and shown as a read-only display — it is NOT a field here.
    """

    app_password = forms.CharField(
        label="Gmail App Password",
        max_length=64,
        # PasswordInput so the characters are hidden while typing
        widget=forms.PasswordInput(attrs={
            "placeholder": "e.g.  abcd efgh ijkl mnop",
            "class": "form-input",
            "autocomplete": "off",
        }),
        help_text=(
            "Enter the 16-character App Password generated from your Google Account. "
            "Spaces are optional — we strip them automatically."
        ),
    )

    class Meta:
        model = GmailConfig
        fields = ["app_password"]

    def clean_app_password(self):
        pwd = self.cleaned_data["app_password"].replace(" ", "").strip()
        if len(pwd) < 8:
            raise ValidationError(
                "That doesn't look like a valid App Password. "
                "It should be 16 characters long (spaces are ignored)."
            )
        return pwd


class EmailRequestForm(forms.Form):
    """
    Step 1 to Step 6 of the wizard, combined into a single simple form.
    (Sender email is NOT here - it is taken automatically from request.user.email)
    """
    TOPIC_CHOICES = [
    ("Leave Application", "Leave Application"),
    ("Job Application", "Job Application"),
    ("Meeting Request", "Meeting Request"),
    ("Complaint", "Complaint"),
    ("Apology", "Apology"),
    ("Thank You", "Thank You"),
    ("Invitation", "Invitation"),
    ("Follow-up", "Follow-up"),
    ("Resignation", "Resignation"),
    ("Internship Request", "Internship Request"),
    ("Project Update", "Project Update"),
    ("Business Proposal", "Business Proposal"),
    ("Feedback", "Feedback"),
    ("Birthday Wishes", "Birthday Wishes"),
    ("Congratulations", "Congratulations"),
    ("Other", "Other"),
]

    # Maps each Topic dropdown value to the matching key in
    # email_generator.TEMPLATES, so the right template family is picked
    # every time instead of relying on fragile keyword guessing.
    TOPIC_KEY_MAP = {
        "Leave Application":  "leave",
        "Job Application":    "job",
        "Meeting Request":    "meeting",
        "Complaint":          "complaint",
        "Apology":            "apology",
        "Thank You":          "thank_you",
        "Invitation":         "invitation",
        "Follow-up":          "follow_up",
        "Resignation":        "resignation",
        "Internship Request": "internship",
        "Project Update":     "project",
        "Business Proposal":  "proposal",
        "Feedback":           "feedback",
        "Birthday Wishes":    "birthday",
        "Congratulations":    "congrats",
        "Other":              "generic",
    }

    # Sentinel value shown in every subtopic dropdown that lets the user
    # type their own specific detail instead of picking a preset one.
    CUSTOM_SUBTOPIC_VALUE = "__custom__"

    # For each Topic, a set of specific, real-world situations the user can
    # pick from. Picking one of these (instead of just the broad topic name)
    # is what lets the generated email talk about the *actual* situation —
    # "a defective product I received" instead of just "Complaint" — so
    # every generation reads as specific and human rather than generic,
    # and the number of realistically different emails multiplies far
    # beyond the 3-5 body templates per topic.
    SUBTOPICS = {
        "Leave Application": [
            "a family medical emergency",
            "my own health and recovery",
            "a close relative's wedding",
            "an urgent personal matter at home",
            "religious or festival observance",
            "relocating to a new house",
            "attending a family function out of town",
        ],
        "Job Application": [
            "Software Developer",
            "Marketing Executive",
            "Graphic Designer",
            "Customer Support Associate",
            "Data Analyst",
            "Sales Executive",
            "HR Executive",
        ],
        "Meeting Request": [
            "next quarter's marketing strategy",
            "the pending project deliverables",
            "a potential business partnership",
            "budget planning for the new fiscal year",
            "resolving an ongoing team issue",
            "the onboarding and training schedule",
        ],
        "Complaint": [
            "a defective product I received",
            "poor customer service during my last visit",
            "an unresolved billing discrepancy",
            "the delayed delivery of my recent order",
            "a rude interaction with your support staff",
            "repeated service outages",
        ],
        "Apology": [
            "missing yesterday's scheduled call",
            "a delay in submitting the report",
            "a miscommunication earlier this week",
            "an error in the invoice I sent",
            "not responding to your email sooner",
            "an oversight on my part during the project",
        ],
        "Thank You": [
            "your support during my onboarding",
            "the guidance you provided on the project",
            "your time during our recent meeting",
            "the opportunity to work with your team",
            "your quick help resolving my issue",
            "your kind hospitality during my visit",
        ],
        "Invitation": [
            "our upcoming product launch event",
            "the annual team get-together",
            "a webinar on industry best practices",
            "our office housewarming celebration",
            "a networking dinner next month",
            "the inauguration of our new branch",
        ],
        "Follow-up": [
            "the proposal I sent last week",
            "my job application status",
            "the invoice payment we discussed",
            "our previous conversation about the project",
            "the documents I submitted earlier",
            "the feedback on my recent submission",
        ],
        "Resignation": [
            "pursuing a new career opportunity",
            "relocating to another city",
            "personal and family reasons",
            "further studies I plan to pursue",
            "health reasons requiring a break",
            "a shift toward a different career path",
        ],
        "Internship Request": [
            "Web Development",
            "Digital Marketing",
            "Data Science",
            "Graphic Design",
            "Human Resources",
            "Content Writing",
        ],
        "Project Update": [
            "the website redesign project",
            "the mobile app development sprint",
            "the client onboarding process",
            "the quarterly sales campaign",
            "the inventory management system upgrade",
            "the marketing content calendar",
        ],
        "Business Proposal": [
            "a co-marketing partnership",
            "a bulk supply agreement",
            "a joint venture for the upcoming project",
            "a long-term vendor collaboration",
            "a reseller partnership opportunity",
            "a technology integration partnership",
        ],
        "Feedback": [
            "your recent purchase experience",
            "the customer support you received",
            "our new product features",
            "the recent training session",
            "the event you attended last week",
            "the service quality at our outlet",
        ],
        "Birthday Wishes": [
            "a close friend's birthday",
            "a colleague's birthday",
            "a family member's birthday",
            "my manager's birthday",
            "a mentor's birthday",
        ],
        "Congratulations": [
            "your recent promotion",
            "successfully closing the big client deal",
            "your well-deserved award",
            "the launch of your new venture",
            "passing your certification exam",
            "your team's outstanding quarterly results",
        ],
    }

    receiver_email = forms.EmailField(
        label="Receiver Email",
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "receiver@example.com",
            "class": "form-input",
        }),
    )

    topic = forms.ChoiceField(
    label="Topic",
    choices=TOPIC_CHOICES,
    widget=forms.Select(attrs={
        "class": "form-input",
        "id": "id_topic",
    }),
)

    # Populated client-side by JS based on the chosen Topic (see form.html).
    # Left as a plain CharField (not ChoiceField) because its valid options
    # depend on which Topic is selected; validity is checked in clean().
    subtopic = forms.CharField(
        label="Specific Type",
        required=False,
        widget=forms.Select(attrs={
            "class": "form-input",
            "id": "id_subtopic",
        }),
    )

    custom_detail = forms.CharField(
        label="Describe your situation",
        required=False,
        max_length=180,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "id": "id_custom_detail",
            "placeholder": "e.g. a scratched screen on the phone I received",
        }),
    )

    category = forms.ChoiceField(
        label="Email Category",
        choices=EmailHistory.CATEGORY_CHOICES,
        widget=forms.Select(attrs={"class": "form-input"}),
    )

    tone = forms.ChoiceField(
        label="Writing Tone",
        choices=EmailHistory.TONE_CHOICES,
        widget=forms.Select(attrs={"class": "form-input"}),
    )

    length = forms.ChoiceField(
        label="Email Length",
        choices=EmailHistory.LENGTH_CHOICES,
        widget=forms.Select(attrs={"class": "form-input"}),
    )
    

    premium_level = forms.ChoiceField(
        label="Quality Level",
        choices=EmailHistory.LEVEL_CHOICES,
        widget=forms.RadioSelect,
        initial="Basic",
    )

    attachments = MultipleFileField(
        label="Attachments",
        required=False,
        widget=forms.FileInput(attrs={
            "class": "form-input",
            "accept": "image/*,.pdf,.doc,.docx,.txt",
        }),
        help_text="You can attach images, PDFs, and other files.",
    )

    def clean_topic(self):
     return self.cleaned_data["topic"]

    def clean_receiver_email(self):
        email = self.cleaned_data["receiver_email"].strip()
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid receiver email address.")
        return email

    def clean(self):
        cleaned = super().clean()
        topic = cleaned.get("topic") or ""
        subtopic = (cleaned.get("subtopic") or "").strip()
        custom_detail = (cleaned.get("custom_detail") or "").strip()

        valid_subtopics = self.SUBTOPICS.get(topic, [])

        if topic == "Other":
            # "Other" has no preset list — the user must describe it.
            if not custom_detail:
                self.add_error(
                    "custom_detail",
                    "Please briefly describe what this email is about."
                )
        elif subtopic == self.CUSTOM_SUBTOPIC_VALUE:
            if not custom_detail:
                self.add_error(
                    "custom_detail",
                    "Please describe your specific situation."
                )
        elif valid_subtopics and subtopic not in valid_subtopics:
            self.add_error(
                "subtopic",
                "Please select a specific type for this topic."
            )

        return cleaned

    def get_topic_detail(self):
        """
        Return the final, specific phrase to weave into the generated
        email — the custom text if the user typed one, otherwise the
        picked subtopic, otherwise a blank (falls back to the raw topic
        name inside email_generator).
        """
        data = self.cleaned_data
        topic = data.get("topic") or ""
        subtopic = (data.get("subtopic") or "").strip()
        custom_detail = (data.get("custom_detail") or "").strip()

        if topic == "Other":
            return custom_detail
        if subtopic == self.CUSTOM_SUBTOPIC_VALUE:
            return custom_detail
        return subtopic

    def get_topic_key(self):
        """Return the explicit email_generator.TEMPLATES key for the chosen topic."""
        data = self.cleaned_data
        return self.TOPIC_KEY_MAP.get(data.get("topic"), "generic")


class EmailEditForm(forms.Form):
    """
    Shown on the Preview page. Pre-filled with the generated email.
    The user can tweak Subject/Body before confirming Send.
    Hidden fields carry the rest of the data through to the confirm step.
    """

    subject = forms.CharField(
        label="Subject",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    body = forms.CharField(
        label="Email Body",
        widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 16}),
    )

    receiver_email = forms.CharField(widget=forms.HiddenInput())
    topic = forms.CharField(widget=forms.HiddenInput())
    category = forms.CharField(widget=forms.HiddenInput())
    tone = forms.CharField(widget=forms.HiddenInput())
    length = forms.CharField(widget=forms.HiddenInput())
    premium_level = forms.CharField(widget=forms.HiddenInput())

    def clean_subject(self):
        subject = self.cleaned_data["subject"].strip()
        if not subject:
            raise ValidationError("Subject cannot be blank.")
        return subject

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise ValidationError("Email body cannot be blank.")
        return body
