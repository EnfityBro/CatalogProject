from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class MilkType(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Тип молока'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип молока'
        verbose_name_plural = 'Типы молока'
        ordering = ['name']


class Cheese(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    milk_type = models.ForeignKey(
        MilkType,
        on_delete=models.PROTECT,
        verbose_name='Тип молока',
        related_name='cheeses'
    )
    fat_content = models.FloatField(
        verbose_name='Жирность, %',
        validators=[MinValueValidator(0.0), MaxValueValidator(70.0)]
    )
    weight = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Вес, г',
        validators=[MinValueValidator(0.0)]
    )
    is_hard = models.BooleanField(verbose_name='Твёрдый')
    has_mold = models.BooleanField(default=False, verbose_name='С плесенью')

    def clean(self):
        if self.fat_content == 0:
            raise ValidationError({'fat_content': 'Жирность не может быть равна 0.'})
        if self.weight is not None and self.weight == 0:
            raise ValidationError({'weight': 'Вес не может быть равен 0.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Сыр'
        verbose_name_plural = 'Сыры'
        ordering = ['name']