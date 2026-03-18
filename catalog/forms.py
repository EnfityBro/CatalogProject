from django import forms
from .models import Cheese

class CheeseForm(forms.ModelForm):
    class Meta:
        model = Cheese
        fields = '__all__'  # ['name', 'milk_type', 'fat_content', 'weight', 'is_hard', 'has_mold']
        widgets = {
            'milk_type': forms.Select(attrs={'class': 'form-control'}),
            'fat_content': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
        }

    def clean_fat_content(self):
        fat = self.cleaned_data['fat_content']
        if fat <= 0:
            raise forms.ValidationError("Жирность должна быть больше 0.")
        if fat > 70:
            raise forms.ValidationError("Жирность не может превышать 70%.")
        return fat

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight <= 0:
            raise forms.ValidationError("Вес должен быть положительным числом.")
        return weight


class SearchForm(forms.Form):
    name = forms.CharField(max_length=100, required=False, label='Название',
                           widget=forms.TextInput(attrs={'placeholder': 'Введите название'}))
    milk_type = forms.ChoiceField(choices=[('', 'Все')] + list(Cheese.MILK_TYPES), required=False, label='Тип молока')
    fat_min = forms.FloatField(required=False, label='Жирность от', min_value=0, max_value=70,
                               widget=forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'мин'}))
    fat_max = forms.FloatField(required=False, label='Жирность до', min_value=0, max_value=70,
                               widget=forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'макс'}))
    is_hard = forms.NullBooleanField(required=False, label='Твёрдый',
                                      widget=forms.Select(choices=[('', 'Все'), ('true', 'Да'), ('false', 'Нет')]))
    has_mold = forms.NullBooleanField(required=False, label='С плесенью',
                                      widget=forms.Select(choices=[('', 'Все'), ('true', 'Да'), ('false', 'Нет')]))