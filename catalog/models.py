from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal


class MilkType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Тип молока')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип молока'
        verbose_name_plural = 'Типы молока'
        ordering = ['name']


class Cheese(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    milk_type = models.ForeignKey(
        MilkType, on_delete=models.PROTECT, verbose_name='Тип молока', related_name='cheeses'
    )
    fat_content = models.FloatField(
        verbose_name='Жирность, %',
        validators=[MinValueValidator(0.0), MaxValueValidator(70.0)]
    )
    weight = models.FloatField(
        null=True, blank=True, verbose_name='Вес, г',
        validators=[MinValueValidator(0.0)]
    )
    is_hard = models.BooleanField(verbose_name='Твёрдый')
    has_mold = models.BooleanField(default=False, verbose_name='С плесенью')

    # === Новые поля цен ===
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Цена за единицу'
    )
    small_wholesale_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Цена мелкого опта'
    )
    small_wholesale_quantity = models.PositiveIntegerField(
        default=1, verbose_name='От кол-ва для мелкого опта'
    )
    large_wholesale_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Цена крупного опта'
    )
    large_wholesale_quantity = models.PositiveIntegerField(
        default=10, verbose_name='От кол-ва для крупного опта'
    )

    def get_price_for_quantity(self, quantity: int) -> Decimal:
        """Расчёт цены с учётом оптовых условий"""
        if quantity >= self.large_wholesale_quantity:
            return self.large_wholesale_price
        elif quantity >= self.small_wholesale_quantity:
            return self.small_wholesale_price
        return self.price

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


class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='carts', verbose_name='Менеджер'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    extra_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Дополнительная скидка на заказ (%)',
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    def get_total(self) -> Decimal:
        total = sum(item.get_total() for item in self.items.all())
        if self.extra_discount_percent:
            total = round(total * (Decimal(1) - self.extra_discount_percent / Decimal(100)), 2)
        return total

    def __str__(self):
        return f'Партия {self.user.get_username()} ({self.created_at.date()})'

    class Meta:
        verbose_name = 'Партия (корзина)'
        verbose_name_plural = 'Партии (корзины)'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    cheese = models.ForeignKey(Cheese, on_delete=models.PROTECT, verbose_name='Сыр')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    def get_price(self) -> Decimal:
        return self.cheese.get_price_for_quantity(self.quantity)

    def get_total(self) -> Decimal:
        return self.get_price() * Decimal(self.quantity)

    def __str__(self):
        return f'{self.cheese.name} × {self.quantity}'

    class Meta:
        verbose_name = 'Позиция партии'
        verbose_name_plural = 'Позиции партии'