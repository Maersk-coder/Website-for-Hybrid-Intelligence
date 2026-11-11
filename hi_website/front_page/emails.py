# Emails: The emails the website sends: after signing the manifesto, and the newsletter
# FYI -> While building they are saved as files in sent_emails/ (next to manage.py). To see it the way the person would
# (attachment included): rename the file from .log to .eml and double-click it

from django.core import mail, signing
from django.core.mail import EmailMessage
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Newsletter, Subscriber

# The manifesto PDF that is attached. It is not on GitHub (see front_page/files/README.md).
MANIFESTO_PDF = settings.BASE_DIR / 'front_page' / 'files' / 'Hybrid Intelligence Manifesto.pdf'

def send_safely(email):
    """ Send the email. If that fails (no internet, a wrong password in .env, ...), don't crash the
        page: the signature is already saved, so the visitor still sees "Thank you". The problem is
        printed in the Django terminal instead. """
    try:
        email.send()
    except Exception as error:
        print(f"WARNING: the email to {email.to} could not be sent: {error}")


def send_signed_email(signature, newsletter):
    """ The 'Thank you for signing' email, with the manifesto attached.
        signature = the row that was just saved. newsletter = True if the newsletter box was ticked. """
    text = (
        f"Dear {signature.name},\n\n"
        "Thank you for signing the Hybrid Intelligence Manifesto.\n\n"
        "By signing, you support a future where AI strengthens what people can do instead of "
        "replacing them: humans and AI working together, each doing what they do best.\n\n"
        "The manifesto is attached as a PDF, so you can read it again and share it with others.\n\n"
    )

    if newsletter:
        text += (
            "You also signed up for the newsletter. We will send you occasional updates about "
            "Hybrid Intelligence and the manifesto.\n\n"
        )
    text += "Kind regards,\nThe Hybrid Intelligence team"

    email = EmailMessage(
        subject="Thank you for signing the Hybrid Intelligence Manifesto",
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[signature.email],
    )
    if MANIFESTO_PDF.exists():
        email.attach_file(MANIFESTO_PDF)
    else:
        print(f"Warning: Manifesto PDF not found at {MANIFESTO_PDF}. Email will be sent without attachment.")
    send_safely(email)


def send_newsletter_welcome_email(subscriber):
    """ The short 'Welcome to the newsletter' email, for people who signed up on the newsletter page.
        subscriber = the row that was just saved. No attachment. """
    text = (
        "Hello,\n\n"
        "Thank you for signing up for the Hybrid Intelligence newsletter.\n\n"
        "Once a month we will send you what is going on in Hybrid Intelligence: new research, tools and events.\n"
        "You will get the latest issue in a separate email in a moment.\n\n"
        "Kind regards,\nThe Hybrid Intelligence team"
        + unsubscribe_footer(subscriber.email)
    )
    email = EmailMessage(
        subject="Welcome to the Hybrid Intelligence newsletter",
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    send_safely(email)


# The monthly newsletter

def unsubscribe_link(email_address):
    """ The personal link that takes this person off the newsletter list.
        signing.dumps turns the email into a code with a secret stamp (made with Django's SECRET_KEY),
        so nobody can make a link that unsubscribes someone else. """
    code = signing.dumps(email_address, salt='unsubscribe')
    return settings.SITE_URL + reverse('unsubscribe', args=[code])


def unsubscribe_footer(email_address):
    """ The lines at the bottom of every newsletter email (EU rules: people must be able to stop it). """
    return (
        "\n\n---\n"
        "You get this email because you signed up for the Hybrid Intelligence newsletter.\n"
        f"Don't want it any more? Unsubscribe here: {unsubscribe_link(email_address)}"
    )


def newsletter_email(issue, email_address):
    """ One newsletter issue, as an email to one person (with their own unsubscribe link). """
    return EmailMessage(
        subject=issue.subject,
        body=issue.text + unsubscribe_footer(email_address),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_address],
    )


def send_latest_issue(email_address):
    """ Send the newest issue that has already gone out, to someone who just subscribed.
        Nothing is sent if no issue has been sent yet. """
    latest = Newsletter.objects.filter(sent_at__isnull=False).first()   # newest first (see Newsletter's ordering)
    if latest:
        send_safely(newsletter_email(latest, email_address))


def send_issue_to_everyone(issue):
    """ Send one issue to everyone on the list, one email per person (so nobody sees the other
        addresses), and note when it was sent. Returns how many were sent. """
    emails = [newsletter_email(issue, subscriber.email) for subscriber in Subscriber.objects.all()]
    sent = 0
    if emails:
        try:
            # One connection to the mail server for all of them, instead of logging in again for each email
            sent = mail.get_connection().send_messages(emails) or 0
        except Exception as error:
            print(f"WARNING: the newsletter '{issue.subject}' could not be sent: {error}")
            return 0
    issue.sent_at = timezone.now()
    issue.save()
    return sent