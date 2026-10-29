from django.shortcuts import render

# Create your views here.
def home(request):
    """ The front page of the website """
    return render(request, 'Front_Page.html')
