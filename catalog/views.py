from django.shortcuts import render, get_object_or_404
from .models import Cheese

def index(request):
    cheeses = Cheese.objects.all()
    return render(request, 'catalog/index.html', {'cheeses': cheeses})

def detail(request, cheese_id):
    cheese = get_object_or_404(Cheese, pk=cheese_id)
    return render(request, 'catalog/detail.html', {'cheese': cheese})

def about(request):
    return render(request, 'catalog/about.html')