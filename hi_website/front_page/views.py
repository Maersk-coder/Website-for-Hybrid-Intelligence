from django.conf import settings
from django.core import signing
from django.db.models import Max, Min
from django.shortcuts import render, redirect
from .forms import ResearchSubmissionForm, SignatureForm, SubscriberForm, UseCaseSubmissionForm
from .models import FaqCategory, FaqQuestion, PressArticle, Publication, Signature, Subscriber, UseCase
from .emails import (send_latest_issue, send_newsletter_welcome_email, send_research_submission_email, send_signed_email,
                     send_use_case_submission_email)



def home(request):
    """ The front page of the website. The card on Page 1 ("Featured use case") shows the Iconic use cases,
        one after the other, in step with the animation (Page 1 (main)/JS - Animations/featured_case.js). """
    featured = list(UseCase.objects.filter(kind='iconic').values('organisation', 'title'))   # a list of {organisation, title}
    context = {'featured_cases': featured, 'first_case': featured[0] if featured else None}
    return render(request, 'Front_Page.html', context)


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


def manifesto(request):
    """ The Manifesto page (the first page in the Manifesto menu). Shows how many people have signed. """
    context = {'signature_count': Signature.objects.count()}
    return render(request, 'buttons/manifesto/Manifesto_bt.html', context)


def econ_manifesto(request):
    """ The ECON Manifesto page: The Economics of Hybrid Intelligence. All its text is in the template. """
    return render(request, 'buttons/manifesto/ECON_Manifesto_bt.html')


def education_manifesto(request):
    """ The Education Manifesto page. Its "Use cases" part shows the Educational use cases from the database. """
    cases = UseCase.objects.filter(kind='educational')
    context = {'cases': cases, 'case_count': cases.count()}
    return render(request, 'buttons/manifesto/Education_Manifesto_bt.html', context)


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


def research(request):
    """ The Research page: the newest publication first ("Latest"), the "Share your research" box,
        then all the other publications. """
    publications = list(Publication.objects.all())       # list() = fetch them all now, so we can split them

    # Everyone who wrote at least one of the publications, each name counted once
    authors = set()                                      # a set keeps each name only once
    for publication in publications:
        authors.update(name.strip() for name in publication.authors.split(',') if name.strip())

    context = {
        'latest': publications[0] if publications else None,
        'publications': publications[1:],                # all but the first
        'publication_count': len(publications),
        'author_count': len(authors),
        'contact_email': settings.CONTACT_EMAIL,
    }
    return render(request, 'buttons/Research_bt.html', context)


def share_research(request):
    """ The "Share your research" page: GET shows an empty form, POST saves it and emails the site's inbox.
        Works the same way as sign() and newsletter(). """
    if request.method == 'POST':
        form = ResearchSubmissionForm(data=request.POST)
        if form.is_valid():
            submission = form.save()                     # store it in the database (admin: Research submissions)
            send_research_submission_email(submission)   # and tell the site's inbox
            return redirect('thanks')
    else:
        form = ResearchSubmissionForm()

    context = {'form': form, 'contact_email': settings.CONTACT_EMAIL}
    return render(request, 'Share_Research.html', context)


def use_cases(request):
    """ The Use Cases page. The filter buttons add ?type=... to the address (a GET request with a
        "query string"); request.GET.get('type') reads it, and only that type is shown. """
    chosen = request.GET.get('type', '')                 # e.g. "iconic", or "" for all
    all_cases = UseCase.objects.all()
    cases = all_cases.filter(kind=chosen) if chosen else all_cases

    # The filter buttons: one per type, with how many use cases it has
    filters = [{'kind': kind, 'label': label.replace(' Use Case', ''), 'count': all_cases.filter(kind=kind).count()}
               for kind, label in UseCase.KINDS]

    context = {
        'cases': cases,
        'chosen': chosen,
        'filters': filters,
        'case_count': all_cases.count(),
        'organisation_count': all_cases.values('organisation').distinct().count(),   # each organisation once
        'contact_email': settings.CONTACT_EMAIL,
    }
    return render(request, 'buttons/Use_Cases_bt.html', context)


def share_use_case(request):
    """ The "Share your use case" page: GET shows an empty form, POST saves it and emails the site's inbox. """
    if request.method == 'POST':
        form = UseCaseSubmissionForm(data=request.POST)
        if form.is_valid():
            submission = form.save()
            send_use_case_submission_email(submission)
            return redirect('thanks')
    else:
        form = UseCaseSubmissionForm()

    context = {'form': form, 'contact_email': settings.CONTACT_EMAIL}
    return render(request, 'Share_Use_Case.html', context)


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
