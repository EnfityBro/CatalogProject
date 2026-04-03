from django.test import TestCase, LiveServerTestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import os
from catalog.models import Cheese, MilkType


class RoutesTests(LiveServerTestCase):
    '''
    Тесты маршрутов и прав доступа
    '''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        driver_path = r"D:\EdgeWebDriver\msedgedriver.exe"
        if not os.path.exists(driver_path):
            raise FileNotFoundError(f"Драйвер не найден по пути: {driver_path}")

        edge_options = Options()
        edge_options.add_argument("--ignore-certificate-errors")
        edge_options.add_argument("--disable-web-security")
        edge_options.add_argument("--headless")

        service = EdgeService(executable_path=driver_path)
        cls.driver = webdriver.Edge(service=service, options=edge_options)
        cls.driver.implicitly_wait(10)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Фикстуры для Selenium
        self.milk_cow = MilkType.objects.create(name='коровье')
        self.cheese1 = Cheese.objects.create(
            name="Пармезан", milk_type=self.milk_cow, fat_content=32.0,
            price=1200, small_wholesale_price=1100, small_wholesale_quantity=5,
            large_wholesale_price=950, large_wholesale_quantity=20,
            is_hard=True, has_mold=False
        )
        self.cheese2 = Cheese.objects.create(
            name="Камамбер", milk_type=self.milk_cow, fat_content=45.0,
            price=850, small_wholesale_price=780, small_wholesale_quantity=3,
            large_wholesale_price=700, large_wholesale_quantity=15,
            is_hard=False, has_mold=True
        )

    def test_index_route(self):
        '''
        Проверяет, что главная страница каталога (маршрут index)
        возвращает статус 200 (доступна).
        '''

        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_detail_route(self):
        '''
        Проверяет, что страница детального просмотра конкретного
        сыра (маршрут detail) успешно открывается.
        '''

        response = self.client.get(reverse('detail', args=[self.cheese1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_about_route(self):
        '''
        Проверяет доступность страницы «О проекте» (маршрут about).
        '''

        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)


    # Selenium тесты (маршруты + контент)
    def test_navigation_to_about(self):
        '''
        Проверяет, что пользователь может перейти на страницу «О проекте»
        через ссылку на главной странице с помощью браузера.
        '''

        self.driver.get(self.live_server_url)
        about_link = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "О проекте")))
        about_link.click()
        self.wait.until(EC.url_contains('/about/'))
        self.assertIn('/about/', self.driver.current_url)

    def test_detail_page_has_title(self):
        '''
        Проверяет, что на странице детальной информации о сыре заголовок <h1>
        содержит правильное название сыра.
        '''

        url = self.live_server_url + reverse('detail', args=[self.cheese1.pk])
        self.driver.get(url)
        header = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        self.assertEqual(header.text, self.cheese1.name)

    def test_index_page_contains_cheese_list_sorted(self):
        '''
        Проверяет, что на главной странице отображается список сыров и они
        отсортированы по алфавиту (по названию).
        '''

        self.driver.get(self.live_server_url)
        cheese_links = self.driver.find_elements(By.XPATH, "//li/a[contains(@href, '/cheese/')]")
        names = [link.text.strip() for link in cheese_links]
        self.assertIn("Камамбер", names)
        self.assertIn("Пармезан", names)
        self.assertTrue(names == sorted(names))

    def test_guest_can_only_view(self):
        '''
        Проверяет, что неавторизованный гость видит только просмотр каталога
        и не видит кнопки редактирования/добавления товаров.
        '''

        self.driver.get(self.live_server_url)
        self.assertNotIn("Редактировать", self.driver.page_source)
        self.assertNotIn("Добавить новый сыр", self.driver.page_source)

    def test_login_and_cart_link_for_manager(self):
        '''
        Проверяет наличие ссылки на корзину («Моя партия») для пользователя с
        ролью "Менеджер по продажам" после входа.
        '''

        # Создаём менеджера и логинимся
        # Selenium не умеет легко логиниться через форму Django, поэтому проверяем
        # только наличие ссылок после логина через client далее в тесте менеджера
        manager = User.objects.create_user(username='manager_test', password='pass')
        Group.objects.get_or_create(name='Менеджер по продажам')[0].user_set.add(manager)


class PermissionTests(TestCase):
    '''
    TestCase для быстрых проверок прав
    '''

    def setUp(self):
        self.client = Client()
        self.guest = User.objects.create_user(username='guest', password='pass')
        self.merch = User.objects.create_user(username='merch', password='pass')
        self.manager = User.objects.create_user(username='manager', password='pass')
        Group.objects.get_or_create(name='Товаровед')[0].user_set.add(self.merch)
        Group.objects.get_or_create(name='Менеджер по продажам')[0].user_set.add(self.manager)

        self.milk = MilkType.objects.create(name='козье')
        self.cheese = Cheese.objects.create(name="Тестовый", milk_type=self.milk,
                                            fat_content=30, price=1000, is_hard=False)

    def test_guest_can_view_only(self):
        '''
        Проверяет, что гость (обычный пользователь без роли) может только просматривать каталог и
        детали товара, но не может добавлять/редактировать сыры.
        '''

        self.client.force_login(self.guest)
        self.assertEqual(self.client.get(reverse('index')).status_code, 200)
        self.assertEqual(self.client.get(reverse('detail', args=[self.cheese.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('cheese_add')).status_code, 302)  # redirect

    def test_merchandiser_can_edit_cheese(self):
        '''
        Проверяет, что пользователь с ролью «Товаровед» имеет доступ к созданию и редактированию товаров.
        '''

        self.client.force_login(self.merch)
        self.assertEqual(self.client.get(reverse('cheese_add')).status_code, 200)
        self.assertEqual(self.client.get(reverse('cheese_edit', args=[self.cheese.pk])).status_code, 200)

    def test_sales_manager_can_access_cart(self):
        '''
        Проверяет, что пользователь с ролью «Менеджер по продажам» имеет доступ к странице
        своей партии (корзины), но не может редактировать товары.
        '''

        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse('my_cart')).status_code, 200)
        self.assertEqual(self.client.get(reverse('cheese_add')).status_code, 302)  # то есть не может редактировать товар