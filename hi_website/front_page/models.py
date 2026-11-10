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
