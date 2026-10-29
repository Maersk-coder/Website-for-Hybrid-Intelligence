# The app's list of addresses: which address runs which function in views.py.
# (The project's main list, config/urls.py, sends visitors here.)

from django.urls import path    # Django's function that links an address to a view
from . import views             # views.py from this same folder (the "." means "this folder")

urlpatterns = [
    # '' = the start page (http://127.0.0.1:8001/) -> runs home() in views.py.
    # name='home' is a label, so templates can link to it with {% url 'home' %}.
    path('', views.home, name='home'),
]
