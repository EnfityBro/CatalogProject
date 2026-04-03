from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Cheese, Cart, CartItem, MilkType
from .forms import CheeseForm, SearchForm


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_merchandiser(user):
    return user.groups.filter(name='Товаровед').exists()


def is_sales_manager(user):
    return user.groups.filter(name='Менеджер по продажам').exists()


def index(request):
    form = SearchForm(request.GET or None)
    cheeses = Cheese.objects.all()

    if form.is_valid():
        name = form.cleaned_data.get('name')
        if name:
            cheeses = cheeses.filter(name__icontains=name)

        milk_type = form.cleaned_data.get('milk_type')
        if milk_type:
            cheeses = cheeses.filter(milk_type=milk_type)

        fat_min = form.cleaned_data.get('fat_min')
        if fat_min is not None:
            cheeses = cheeses.filter(fat_content__gte=fat_min)
        fat_max = form.cleaned_data.get('fat_max')
        if fat_max is not None:
            cheeses = cheeses.filter(fat_content__lte=fat_max)

        is_hard = form.cleaned_data.get('is_hard')
        if is_hard is not None:
            cheeses = cheeses.filter(is_hard=is_hard)
        has_mold = form.cleaned_data.get('has_mold')
        if has_mold is not None:
            cheeses = cheeses.filter(has_mold=has_mold)

    # Передаём роли для шаблона
    context = {
        'cheeses': cheeses,
        'form': form,
        'is_merchandiser': is_merchandiser(request.user) if request.user.is_authenticated else False,
        'is_sales_manager': is_sales_manager(request.user) if request.user.is_authenticated else False,
        'is_admin': is_admin(request.user) if request.user.is_authenticated else False,
    }
    return render(request, 'catalog/index.html', context)


def detail(request, pk):
    cheese = get_object_or_404(Cheese, pk=pk)
    context = {
        'cheese': cheese,
        'is_merchandiser': is_merchandiser(request.user) if request.user.is_authenticated else False,
        'is_sales_manager': is_sales_manager(request.user) if request.user.is_authenticated else False,
        'is_admin': is_admin(request.user) if request.user.is_authenticated else False,
    }
    return render(request, 'catalog/detail.html', context)

def about(request):
    return render(request, 'catalog/about.html')

@login_required
def my_cart(request):
    if not (is_admin(request.user) or is_sales_manager(request.user)):
        return redirect('index')
    cart, _ = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
        'total': cart.get_total(),
    }
    return render(request, 'catalog/cart.html', context)


@login_required
def add_to_cart(request, cheese_pk):
    if not (is_admin(request.user) or is_sales_manager(request.user)):
        return redirect('index')
    cheese = get_object_or_404(Cheese, pk=cheese_pk)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, cheese=cheese)
    if not created:
        item.quantity += 1
    item.save()
    return redirect('my_cart')


@login_required
def remove_from_cart(request, item_pk):
    if not (is_admin(request.user) or is_sales_manager(request.user)):
        return redirect('index')
    item = get_object_or_404(CartItem, pk=item_pk, cart__user=request.user)
    item.delete()
    return redirect('my_cart')


@login_required
def update_cart_discount(request):
    if not (is_admin(request.user) or is_sales_manager(request.user)):
        return redirect('index')
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        try:
            cart.extra_discount_percent = float(request.POST.get('extra_discount_percent', 0))
            cart.save()
        except ValueError:
            pass
    return redirect('my_cart')


# CRUD сыров — только для товароведов и админов
class RoleRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (is_admin(request.user) or is_merchandiser(request.user)):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class CheeseCreateView(RoleRequiredMixin, CreateView):
    model = Cheese
    form_class = CheeseForm
    template_name = 'catalog/cheese_form.html'
    success_url = reverse_lazy('index')


class CheeseUpdateView(RoleRequiredMixin, UpdateView):
    model = Cheese
    form_class = CheeseForm
    template_name = 'catalog/cheese_form.html'
    success_url = reverse_lazy('index')


class CheeseDeleteView(RoleRequiredMixin, DeleteView):
    model = Cheese
    template_name = 'catalog/cheese_confirm_delete.html'
    success_url = reverse_lazy('index')