from django import forms
from .models import ResearchSubmission, Signature, Subscriber


class SignatureForm(forms.ModelForm):
    """ The 'Sign the Manifesto' form """

    # An extra tick box. It isn't a column in Signature, so it's written here, not in Meta.
    newsletter = forms.BooleanField(required=False, label='Also send me the newsletter')

    class Meta:
        model = Signature
        fields = ['name', 'organisation', 'email']
        labels = {'name': 'Your name', 'organisation': 'Organisation (optional)', 'email': 'Email'}

    def clean_email(self):
        """ Make sure the email is unique, and give a nice error message if not. """
        email = self.cleaned_data['email'].lower()                    # NEW: .lower() = small letters
        if Signature.objects.filter(email__iexact=email).exists():    # NEW: __iexact
            raise forms.ValidationError("This email has already signed the manifesto.")
        return email



class SubscriberForm(forms.ModelForm):
    """ The 'Sign up for newsletter' form """

    class Meta:
        model = Subscriber
        fields = ['email']
        labels = {'email': 'Email'}

    def clean_email(self):
        """ Make sure the email is unique, and give a nice error message if not. """
        email = self.cleaned_data['email'].lower()                    # NEW: .lower() = small letters
        if Subscriber.objects.filter(email__iexact=email).exists():   # NEW: __iexact
            raise forms.ValidationError("This email has already signed up for the newsletter.")
        return email



class ResearchSubmissionForm(forms.ModelForm):
    """ The 'Share your research' form """

    class Meta:
        model = ResearchSubmission
        fields = ['name', 'email', 'title', 'link', 'description']
        labels = {'name': 'Your name', 'email': 'Email', 'title': 'Title of the publication',
                  'link': 'Link to the publication (optional)', 'description': 'A short description of the work'}
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}

    def clean_email(self):
        """ Store the email in small letters, like the other forms """
        return self.cleaned_data['email'].lower()
