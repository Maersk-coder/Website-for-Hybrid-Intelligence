from django.shortcuts import render, redirect
from .forms import SignatureForm, SubscriberForm
from .models import Subscriber
from .emails import send_signed_email, send_newsletter_welcome_email



def home(request):
    """ The front page of the website """
    return render(request, 'Front_Page.html')


def sign(request):
    """ The 'Sign the Manifesto' page: GET shows an empty form, POST checks and saves it """
    if request.method == 'POST':
        # POST: the visitor has filled in the form and clicked the button
        form = SignatureForm(data=request.POST)
        if form.is_valid():
            signature = form.save()                    # store the signature in the database
            if form.cleaned_data['newsletter']:        # was "Also send me the newsletter" ticked?
                # Also put the email on the newsletter list (only if it isn't on it already)
                Subscriber.objects.get_or_create(email=signature.email)
            send_signed_email(signature, form.cleaned_data['newsletter'])  # send the "Thank you" email
            return redirect('thanks')                  # send the visitor on to the "Thank you" page
        # Not valid (e.g. "abc" as email): we go on below, and show the form again WITH the error messages
    else:
        # GET: the visitor has just opened the page, so show an empty form
        form = SignatureForm()

    context = {'form': form}
    return render(request, 'Sign_The_Manifesto.html', context)


def newsletter(request):
    """ The 'Sign up for newsletter' page: GET shows an empty form, POST checks and saves it.
        Works the same way as sign() above. """
    if request.method == 'POST':
        form = SubscriberForm(data=request.POST)
        if form.is_valid():                            # checks the email (and that it isn't on the list already)
            subscriber = form.save()                   # store the email on the newsletter list
            send_newsletter_welcome_email(subscriber)  # the short welcome email
            return redirect('thanks')
        # Not valid: show the form again with the error message
    else:
        form = SubscriberForm()

    context = {'form': form}
    return render(request, 'Newsletter.html', context)


def thanks(request):
    """ The 'Thank you' page, shown after a form is sent """
    return render(request, 'Thank_You.html')
