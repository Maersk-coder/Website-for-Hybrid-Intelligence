# Emails: The emails the website sends after signing the manifesto
# FYI -> While building they are saved as files in sent_emails/ (next to manage.py). To see it the way the person would
# (attachment included): rename the file from .log to .eml and double-click it

from django.core.mail import EmailMessage
from django.conf import settings

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
        "We will send you occasional updates about Hybrid Intelligence: new research, tools and events.\n\n"
        "Kind regards,\nThe Hybrid Intelligence team"
    )
    email = EmailMessage(
        subject="Welcome to the Hybrid Intelligence newsletter",
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    send_safely(email)