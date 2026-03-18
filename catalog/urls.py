from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cheese/<int:cheese_id>/', views.detail, name='detail'),
    path('about/', views.about, name='about'),
]