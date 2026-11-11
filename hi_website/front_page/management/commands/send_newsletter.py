"""
The monthly newsletter, as a command:   python manage.py send_newsletter

It sends the next issue that hasn't been sent yet (the oldest unsent one, written in the admin site) to everyone on the
list. If every issue has already been sent, it does nothing, so running it twice never sends twice.

Django only does something when someone visits a page, so it can't send "every month" by itself.
Instead, the computer runs this command once a month (Windows: Task Scheduler; a web server: cron).
See hi_website/README.md, "The monthly newsletter".
"""

from django.core.management.base import BaseCommand

from front_page.emails import send_issue_to_everyone
from front_page.models import Newsletter


class Command(BaseCommand):
    help = "Send the next unsent newsletter issue to all subscribers"

    def handle(self, *args, **options):
        # The oldest issue that hasn't been sent yet, so issues go out in the order they were written
        issue = Newsletter.objects.filter(sent_at__isnull=True).order_by('created_at').first()
        if issue is None:
            self.stdout.write("Nothing to send: every newsletter issue has already been sent.")
            return
        sent = send_issue_to_everyone(issue)
        self.stdout.write(f"Sent '{issue.subject}' to {sent} subscriber(s).")
