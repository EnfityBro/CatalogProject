from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cheese/<int:pk>/', views.detail, name='detail'),
    path('about/', views.about, name='about'),
    path('add/', views.CheeseCreateView.as_view(), name='cheese_add'),
    path('cheese/<int:pk>/edit/', views.CheeseUpdateView.as_view(), name='cheese_edit'),
    path('cheese/<int:pk>/delete/', views.CheeseDeleteView.as_view(), name='cheese_delete'),
]