from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from decimal import Decimal
from catalog.models import MilkType, Cheese, Cart, CartItem


class ContentTests(TestCase):
    '''
    Тесты контента, моделей, расчётов, валидации и связей
    '''

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
            is_hard=True,
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
            is_hard=False,
            has_mold=True
        )

        cls.manager_user = User.objects.create_user(username='manager_test', password='pass')
        Group.objects.get_or_create(name='Менеджер по продажам')[0].user_set.add(cls.manager_user)

    def test_milktype_creation_and_unique(self):
        '''
        Проверяет создание объекта MilkType и ограничение уникальности поля name
        (unique=True).
        '''

        milk = MilkType.objects.create(name='овечье')
        self.assertEqual(str(milk), 'овечье')
        with self.assertRaises(Exception):
            MilkType.objects.create(name='овечье')

    def test_cheese_creation_and_attributes(self):
        '''
        Проверяет успешное создание сыра и корректность присвоенных атрибутов
        (название, тип молока и т.д.).
        '''

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
        '''
        Проверяет логику метода get_price_for_quantity() — правильно ли выбирается
        цена в зависимости от количества (обычная, мелкий опт, крупный опт).
        '''

        self.assertEqual(self.cheese1.get_price_for_quantity(3), Decimal('1200.00'))
        self.assertEqual(self.cheese1.get_price_for_quantity(6), Decimal('1100.00'))
        self.assertEqual(self.cheese1.get_price_for_quantity(25), Decimal('950.00'))

    def test_cheese_field_validation(self):
        '''
        Проверяет валидацию полей модели Cheese (в частности, что
        жирность не может быть равна 0).
        '''

        cheese = Cheese(
            name="Неверный",
            milk_type=self.milk_cow,
            fat_content=0.0,
            price=100,
            is_hard=True,
            has_mold=False
        )
        with self.assertRaises(ValidationError):
            cheese.full_clean()

    def test_cart_and_cartitem_relationship(self):
        '''
        Проверяет связь «один-ко-многим» между Cart и CartItem, а также
        правильность создания позиций в партии.
        '''

        cart = Cart.objects.create(user=self.manager_user)
        item = CartItem.objects.create(cart=cart, cheese=self.cheese1, quantity=7)
        self.assertEqual(item.cart, cart)
        self.assertEqual(item.cheese, self.cheese1)
        self.assertEqual(cart.items.count(), 1)

    def test_cart_total_calculation_with_discount(self):
        '''
        Проверяет корректный расчёт итоговой суммы партии с учётом оптовых
        цен и дополнительной скидки на весь заказ.
        '''

        cart = Cart.objects.create(user=self.manager_user, extra_discount_percent=Decimal('10.00'))
        CartItem.objects.create(cart=cart, cheese=self.cheese1, quantity=10)
        CartItem.objects.create(cart=cart, cheese=self.cheese2, quantity=5)
        total = cart.get_total()
        expected = (Decimal('11000') + Decimal('3900')) * Decimal('0.9')
        self.assertAlmostEqual(total, Decimal('13410.00'), places=2)

    def test_cheese_ordering_by_name(self):
        '''
        Проверяет, что сыры всегда возвращаются отсортированными по
        названию (по алфавиту) благодаря Meta.ordering.
        '''

        cheeses = list(Cheese.objects.all())
        names = [c.name for c in cheeses]
        self.assertEqual(names, sorted(names))

    def test_cheese_list_by_milk_type(self):
        '''
        Проверяет фильтрацию списка сыров по типу молока (связь ForeignKey
        и «один-из»).
        '''

        cow_cheeses = Cheese.objects.filter(milk_type=self.milk_cow)
        self.assertEqual(cow_cheeses.count(), 1)
        self.assertEqual(cow_cheeses.first().name, "Пармезан")

    def test_milktype_protect_on_delete(self):
        '''
        Проверяет ограничение базы данных on_delete=models.PROTECT —
        нельзя удалить тип молока, если на него ссылаются сыры.
        '''

        with self.assertRaises(Exception):
            self.milk_cow.delete()

    def test_cart_created_automatically_for_manager(self):
        '''
        Проверяет, что для менеджера по продажам корзина (партия)
        создаётся автоматически при первом обращении.
        '''

        cart, created = Cart.objects.get_or_create(user=self.manager_user)
        self.assertIsNotNone(cart)

    def test_cheese_save_calls_full_clean(self):
        '''
        Проверяет, что метод save() в модели Cheese вызывает full_clean(), то
        есть проходит полную валидацию данных перед сохранением.
        '''

        cheese = Cheese(
            name="Тестовый сыр",
            milk_type=self.milk_cow,
            fat_content=25.0,
            price=Decimal('500.00'),
            is_hard=True,
            has_mold=False
        )
        cheese.save()
        self.assertIsNotNone(cheese.pk)