from django.contrib import admin

from .emails import send_issue_to_everyone
from .models import FaqCategory, FaqQuestion, Newsletter, PressArticle, Signature, Subscriber

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


# The FAQ: open a category, and all its questions are listed below it to edit in one go.
class FaqQuestionInline(admin.StackedInline):
    """ The questions shown INSIDE a category's page in the admin site ("inline" = in the same page). """
    model = FaqQuestion
    extra = 0                              # no empty extra forms (click "Add another" for a new question)
    fields = ['number', 'question', 'answer']


@admin.register(FaqCategory)
class FaqCategoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'anchor']
    list_display_links = ['title']
    inlines = [FaqQuestionInline]


@admin.register(FaqQuestion)
class FaqQuestionAdmin(admin.ModelAdmin):
    """ All 80 questions in one list, with a search box (handy for finding one question quickly). """
    list_display = ['number', 'question', 'category']
    list_filter = ['category']
    search_fields = ['question', 'answer']


@admin.register(PressArticle)
class PressArticleAdmin(admin.ModelAdmin):
    """ The press stories. "+ Add" lets you upload a picture for a new story. """
    list_display = ['date', 'title', 'outlet']
    list_display_links = ['title']
    search_fields = ['title', 'outlet', 'excerpt']
    date_hierarchy = 'date'                # click through years and months above the list
