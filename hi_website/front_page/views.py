from django.core import signing
from django.db.models import Max, Min
from django.shortcuts import render, redirect
from .forms import SignatureForm, SubscriberForm
from .models import FaqCategory, FaqQuestion, PressArticle, Subscriber
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


def faq(request):
    """ The FAQ page: all categories, each with its questions, from the database.
        prefetch_related('questions') fetches all the questions in ONE extra database query,
        instead of one query per category. """
    categories = FaqCategory.objects.prefetch_related('questions')
    context = {
        'categories': categories,
        # The numbers at the top of the page ("80 questions", "8 themes"), counted in the database
        'question_count': FaqQuestion.objects.count(),
        'category_count': categories.count(),
    }
    return render(request, 'buttons/FAQ_bt.html', context)


def press(request):
    """ The Press page: all the stories about Hybrid Intelligence in the news, newest first. """
    articles = PressArticle.objects.all()

    # The outlets the stories appeared in, each once, newest first ("DR (Danish ...)" -> "DR")
    outlets = []
    for article in articles:
        name = article.outlet.split(' (')[0].strip()
        if name and name not in outlets:
            outlets.append(name)

    # The first and last year: aggregate asks the database for the smallest and biggest date
    years = articles.aggregate(first=Min('date'), last=Max('date'))

    context = {
        'articles': articles,
        'article_count': articles.count(),
        'outlets': outlets,
        'first_year': years['first'].year if years['first'] else None,
        'last_year': years['last'].year if years['last'] else None,
    }
    return render(request, 'buttons/Press_bt.html', context)


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
