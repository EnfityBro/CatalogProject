from django.contrib import admin
from .models import Cheese, MilkType


@admin.register(MilkType)
class MilkTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Cheese)
class CheeseAdmin(admin.ModelAdmin):
    list_display = ['name', 'milk_type', 'fat_content', 'weight', 'is_hard', 'has_mold']
    list_filter = ['milk_type', 'is_hard', 'has_mold']
    search_fields = ['name']
    autocomplete_fields = ['milk_type']