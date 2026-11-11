from django.db import models

class Signature(models.Model):
    """ Someone who signed the manifesto """
    name = models.CharField(max_length=100)
    organisation = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, error_messages={'unique': "This email has already signed the manifesto."})
    signed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """ How a signature is shown, e.g. in the admin site """
        return self.name


class Subscriber(models.Model):
    """ Someone who wants the newsletter """
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Newsletter(models.Model):
    """ One issue of the monthly newsletter: what is going on in Hybrid Intelligence this month.
        Written in the admin site. sent_at stays empty until the issue has been sent to everyone. """
    subject = models.CharField(max_length=200)
    text = models.TextField()                                   # TextField = text of any length, with line breaks
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)       # empty = not sent yet (a draft)

    class Meta:
        ordering = ['-created_at']                              # newest first ("-" means newest to oldest)

    def __str__(self):
        return self.subject
