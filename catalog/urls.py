from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cheese/<int:pk>/', views.detail, name='detail'),
    path('about/', views.about, name='about'),
    path('add/', views.CheeseCreateView.as_view(), name='cheese_add'),
    path('cheese/<int:pk>/edit/', views.CheeseUpdateView.as_view(), name='cheese_edit'),
    path('cheese/<int:pk>/delete/', views.CheeseDeleteView.as_view(), name='cheese_delete'),

    # === Новый функционал ===
    path('login/', auth_views.LoginView.as_view(template_name='catalog/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('cart/', views.my_cart, name='my_cart'),
    path('add-to-cart/<int:cheese_pk>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-discount/', views.update_cart_discount, name='update_cart_discount'),
]