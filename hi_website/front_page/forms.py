from django import forms
from .models import Signature, Subscriber


class SignatureForm(forms.ModelForm):
    """ The 'Sign the Manifesto' form """

    # An extra tick box. It isn't a column in Signature, so it's written here, not in Meta.
    newsletter = forms.BooleanField(required=False, label='Also send me the newsletter')

    class Meta:
        model = Signature
        fields = ['name', 'organisation', 'email']
        labels = {'name': 'Your name', 'organisation': 'Organisation (optional)', 'email': 'Email'}


class SubscriberForm(forms.ModelForm):
    """ The 'Sign up for newsletter' form """

    class Meta:
        model = Subscriber
        fields = ['email']
        labels = {'email': 'Email'}
