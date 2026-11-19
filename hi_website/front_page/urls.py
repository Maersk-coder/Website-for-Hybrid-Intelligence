# The app's list of addresses: which address runs which function in views.py.
# (The project's main list, config/urls.py, sends visitors here.)

from django.urls import path    # Django's function that links an address to a view
from . import views             # views.py from this same folder (the "." means "this folder")

urlpatterns = [
    # '' = the start page (http://127.0.0.1:8001/) -> runs home() in views.py.
    # name='home' is a label, so templates can link to it with {% url 'home' %}.
    path('', views.home, name='home'),
    path('sign/', views.sign, name='sign'),        # the "Sign the Manifesto" page
    path('newsletter/', views.newsletter, name='newsletter'),  # the "Sign up for newsletter" page
    # The three pages in the Manifesto menu (the dropdown in header.html)
    path('manifesto/', views.manifesto, name='manifesto'),
    path('manifesto/economics/', views.econ_manifesto, name='econ_manifesto'),
    path('manifesto/education/', views.education_manifesto, name='education_manifesto'),
    path('research/', views.research, name='research'),                    # the Research page (publications)
    path('research/share/', views.share_research, name='share_research'),  # the "Share your research" form
    path('use-cases/', views.use_cases, name='use_cases'),                  # the Use Cases page
    path('use-cases/share/', views.share_use_case, name='share_use_case'),  # the "Share your use case" form
    path('press/', views.press, name='press'),      # the Press page (stories from the database)
    path('faq/', views.faq, name='faq'),            # the FAQ page (questions and answers from the database)
    path('thanks/', views.thanks, name='thanks'),  # the "Thank you" page
    # <str:code> = the rest of the address is handed to the view as "code" (the stamped email address)
    path('unsubscribe/<str:code>/', views.unsubscribe, name='unsubscribe'),  # the link in every newsletter
]
