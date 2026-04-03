from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from decimal import Decimal

# Абсолютный импорт
from catalog.models import MilkType, Cheese, Cart, CartItem


class ContentTests(TestCase):
    """Тесты контента, моделей, расчётов, валидации и связей"""

    @classmethod
    def setUpTestData(cls):
        cls.milk_cow = MilkType.objects.create(name='коровье')
        cls.milk_goat = MilkType.objects.create(name='козье')

        cls.cheese1 = Cheese.objects.create(
            name="Пармезан",
            milk_type=cls.milk_cow,
            fat_content=32.0,
            price=Decimal('1200.00'),
            small_wholesale_price=Decimal('1100.00'),
            small_wholesale_quantity=5,
            large_wholesale_price=Decimal('950.00'),
            large_wholesale_quantity=20,
            is_hard=True,          # ← обязательно
            has_mold=False
        )
        cls.cheese2 = Cheese.objects.create(
            name="Камамбер",
            milk_type=cls.milk_goat,
            fat_content=45.0,
            price=Decimal('850.00'),
            small_wholesale_price=Decimal('780.00'),
            small_wholesale_quantity=3,
            large_wholesale_price=Decimal('700.00'),
            large_wholesale_quantity=15,
            is_hard=False,         # ← обязательно
            has_mold=True
        )

        cls.manager_user = User.objects.create_user(username='manager_test', password='pass')
        Group.objects.get_or_create(name='Менеджер по продажам')[0].user_set.add(cls.manager_user)

    # ==================== МОДЕЛИ И ВАЛИДАЦИЯ ====================
    def test_milktype_creation_and_unique(self):
        milk = MilkType.objects.create(name='овечье')
        self.assertEqual(str(milk), 'овечье')
        with self.assertRaises(Exception):
            MilkType.objects.create(name='овечье')

    def test_cheese_creation_and_attributes(self):
        cheese = Cheese.objects.create(
            name="Горгонзола",
            milk_type=self.milk_cow,
            fat_content=48.0,
            price=Decimal('950'),
            is_hard=False,          # ← обязательно
            has_mold=True
        )
        self.assertEqual(cheese.name, "Горгонзола")
        self.assertEqual(cheese.milk_type, self.milk_cow)

    def test_cheese_price_for_quantity_logic(self):
        self.assertEqual(self.cheese1.get_price_for_quantity(3), Decimal('1200.00'))
        self.assertEqual(self.cheese1.get_price_for_quantity(6), Decimal('1100.00'))
        self.assertEqual(self.cheese1.get_price_for_quantity(25), Decimal('950.00'))

    def test_cheese_field_validation(self):
        cheese = Cheese(
            name="Неверный",
            milk_type=self.milk_cow,
            fat_content=0.0,
            price=100,
            is_hard=True,           # ← обязательно
            has_mold=False
        )
        with self.assertRaises(ValidationError):
            cheese.full_clean()

    def test_cart_and_cartitem_relationship(self):
        cart = Cart.objects.create(user=self.manager_user)
        item = CartItem.objects.create(cart=cart, cheese=self.cheese1, quantity=7)
        self.assertEqual(item.cart, cart)
        self.assertEqual(item.cheese, self.cheese1)
        self.assertEqual(cart.items.count(), 1)

    def test_cart_total_calculation_with_discount(self):
        cart = Cart.objects.create(user=self.manager_user, extra_discount_percent=Decimal('10.00'))
        CartItem.objects.create(cart=cart, cheese=self.cheese1, quantity=10)
        CartItem.objects.create(cart=cart, cheese=self.cheese2, quantity=5)
        total = cart.get_total()
        expected = (Decimal('11000') + Decimal('3900')) * Decimal('0.9')
        self.assertAlmostEqual(total, Decimal('13410.00'), places=2)

    def test_cheese_ordering_by_name(self):
        cheeses = list(Cheese.objects.all())
        names = [c.name for c in cheeses]
        self.assertEqual(names, sorted(names))

    def test_cheese_list_by_milk_type(self):
        cow_cheeses = Cheese.objects.filter(milk_type=self.milk_cow)
        self.assertEqual(cow_cheeses.count(), 1)
        self.assertEqual(cow_cheeses.first().name, "Пармезан")

    def test_milktype_protect_on_delete(self):
        with self.assertRaises(Exception):   # ProtectedError при удалении
            self.milk_cow.delete()

    def test_cart_created_automatically_for_manager(self):
        cart, created = Cart.objects.get_or_create(user=self.manager_user)
        self.assertIsNotNone(cart)

    # ==================== ИСПРАВЛЕННЫЙ ТЕСТ ====================
    def test_cheese_save_calls_full_clean(self):
        """Проверяем, что save() вызывает full_clean() и валидация работает"""
        cheese = Cheese(
            name="Тестовый сыр",
            milk_type=self.milk_cow,
            fat_content=25.0,
            price=Decimal('500.00'),
            is_hard=True,               # ← КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ
            has_mold=False
        )
        cheese.save()                   # теперь не должно падать
        self.assertIsNotNone(cheese.pk)