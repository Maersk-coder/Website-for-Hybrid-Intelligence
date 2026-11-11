from django.core import signing
from django.shortcuts import render, redirect
from .forms import SignatureForm, SubscriberForm
from .models import Subscriber
from .emails import send_signed_email, send_newsletter_welcome_email, send_latest_issue



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
            newly_subscribed = False
            if form.cleaned_data['newsletter']:        # was "Also send me the newsletter" ticked?
                # Also put the email on the newsletter list (only if it isn't on it already).
                # get_or_create gives back the row AND whether it was new (True) or already there (False).
                subscriber, newly_subscribed = Subscriber.objects.get_or_create(email=signature.email)
            send_signed_email(signature, form.cleaned_data['newsletter'])  # send the "Thank you" email
            if newly_subscribed:
                send_latest_issue(signature.email)    # new on the list: also send the newest newsletter
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
            send_newsletter_welcome_email(subscriber)  # email 1: the short welcome
            send_latest_issue(subscriber.email)        # email 2: the newest newsletter (if one has been sent)
            return redirect('thanks')
        # Not valid: show the form again with the error message
    else:
        form = SubscriberForm()

    context = {'form': form}
    return render(request, 'Newsletter.html', context)


def unsubscribe(request, code):
    """ The page behind the "Unsubscribe" link in every newsletter email.
        code = the email address with a secret stamp (see unsubscribe_link in emails.py).
        GET shows a button; only clicking it (POST) removes the email. That way, mail programs that
        open links by themselves to check them can't unsubscribe anyone by accident. """
    try:
        email_address = signing.loads(code, salt='unsubscribe')   # unpack the code; fails if it was changed
    except signing.BadSignature:
        return render(request, 'Unsubscribe.html', {'state': 'bad_link'})

    if request.method == 'POST':
        Subscriber.objects.filter(email=email_address).delete()   # take it off the list
        return render(request, 'Unsubscribe.html', {'state': 'done', 'email': email_address})

    return render(request, 'Unsubscribe.html', {'state': 'ask', 'email': email_address})


def thanks(request):
    """ The 'Thank you' page, shown after a form is sent """
    return render(request, 'Thank_You.html')
