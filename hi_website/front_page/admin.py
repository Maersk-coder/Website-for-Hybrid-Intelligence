from django.contrib import admin

from .emails import send_issue_to_everyone
from .models import Newsletter, Signature, Subscriber

# @admin.register(...) puts a table on the admin site (the same as admin.site.register(...)),
# and the class below it says how the list looks: which columns, a search box, etc.


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'organisation', 'email', 'signed_at']   # the columns in the list
    search_fields = ['name', 'organisation', 'email']               # a search box above the list


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at']
    search_fields = ['email']


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_at', 'sent_at']
    readonly_fields = ['sent_at']          # filled in by the website when it is sent, not by hand
    actions = ['send_now']                 # an extra choice in the "Action" menu above the list

    @admin.action(description="Send to all subscribers now")
    def send_now(self, request, queryset):
        """ For testing (or a newsletter that can't wait): send the ticked issue(s) right away. """
        for issue in queryset:
            sent = send_issue_to_everyone(issue)
            self.message_user(request, f"'{issue.subject}' was sent to {sent} subscriber(s).")
