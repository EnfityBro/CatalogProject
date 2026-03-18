from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models import Q
from .models import Cheese
from .forms import CheeseForm, SearchForm

def index(request):
    form = SearchForm(request.GET or None)
    cheeses = Cheese.objects.all()

    if form.is_valid():
        # Фильтрация по имени (частичное совпадение, регистронезависимое)
        name = form.cleaned_data.get('name')
        if name:
            cheeses = cheeses.filter(name__icontains=name)

        # Фильтрация по типу молока
        milk_type = form.cleaned_data.get('milk_type')
        if milk_type:
            cheeses = cheeses.filter(milk_type=milk_type)

        # Диапазон жирности
        fat_min = form.cleaned_data.get('fat_min')
        if fat_min is not None:
            cheeses = cheeses.filter(fat_content__gte=fat_min)
        fat_max = form.cleaned_data.get('fat_max')
        if fat_max is not None:
            cheeses = cheeses.filter(fat_content__lte=fat_max)

        # Булевы поля: is_hard, has_mold
        is_hard = form.cleaned_data.get('is_hard')
        if is_hard is not None:
            cheeses = cheeses.filter(is_hard=is_hard)
        has_mold = form.cleaned_data.get('has_mold')
        if has_mold is not None:
            cheeses = cheeses.filter(has_mold=has_mold)

    context = {
        'cheeses': cheeses,
        'form': form,
    }
    return render(request, 'catalog/index.html', context)

def detail(request, pk):
    cheese = get_object_or_404(Cheese, pk=pk)
    return render(request, 'catalog/detail.html', {'cheese': cheese})

def about(request):
    return render(request, 'catalog/about.html')

# CRUD представления на базе классов
class CheeseCreateView(CreateView):
    model = Cheese
    form_class = CheeseForm
    template_name = 'catalog/cheese_form.html'
    success_url = reverse_lazy('index')

class CheeseUpdateView(UpdateView):
    model = Cheese
    form_class = CheeseForm
    template_name = 'catalog/cheese_form.html'
    success_url = reverse_lazy('index')

class CheeseDeleteView(DeleteView):
    model = Cheese
    template_name = 'catalog/cheese_confirm_delete.html'
    success_url = reverse_lazy('index')