from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Cheese(models.Model):
    MILK_TYPES = [
        ('cow', 'коровье'),
        ('goat', 'козье'),
        ('sheep', 'овечье'),
        ('buffalo', 'буйволиное'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название')
    milk_type = models.CharField(max_length=20, choices=MILK_TYPES, verbose_name='Тип молока')
    fat_content = models.FloatField(
        verbose_name='Жирность, %',
        validators=[MinValueValidator(0.0), MaxValueValidator(70.0)]
    )
    weight = models.FloatField(
        null=True, blank=True,
        verbose_name='Вес, г',
        validators=[MinValueValidator(0.0)]
    )
    is_hard = models.BooleanField(verbose_name='Твёрдый')
    has_mold = models.BooleanField(default=False, verbose_name='С плесенью')

    def clean(self):
        # Дополнительные проверки, которые не покрывают стандартные валидаторы
        if self.fat_content == 0:
            raise ValidationError({'fat_content': 'Жирность не может быть равна 0.'})
        if self.weight is not None and self.weight == 0:
            raise ValidationError({'weight': 'Вес не может быть равен 0.'})

    def save(self, *args, **kwargs):
        self.full_clean()  # вызовет clean() и валидаторы полей
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name