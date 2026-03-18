from django.test import TestCase, LiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options
from .models import Cheese
import os

class CheeseModelTest(TestCase):
    def test_create_cheese_valid(self):
        cheese = Cheese.objects.create(
            name="Камамбер",
            milk_type="cow",
            fat_content=45.0,
            weight=0.250,
            is_hard=False,
            has_mold=True
        )
        self.assertEqual(cheese.name, "Камамбер")

    def test_fat_content_zero_should_raise(self):
        cheese = Cheese(
            name="Неверный",
            milk_type="cow",
            fat_content=0.0,
            is_hard=True
        )
        with self.assertRaises(Exception):
            cheese.save()

class SeleniumTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        driver_path = r"D:\EdgeWebDriver\msedgedriver.exe"
        if not os.path.exists(driver_path):
            raise FileNotFoundError(f"Драйвер не найден по пути: {driver_path}")

        edge_options = Options()
        edge_options.add_argument("--ignore-certificate-errors")
        edge_options.add_argument("--disable-web-security")

        service = EdgeService(executable_path=driver_path)
        cls.driver = webdriver.Edge(service=service, options=edge_options)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        super().tearDownClass()

        #cls.driver.quit()
        #super().tearDownClass()

    def setUp(self):
        # Создаем тестовый объект Cheese
        self.cheese = Cheese.objects.create(
            name="Пармезан",
            milk_type="cow",
            fat_content=32.0,
            weight=1.5,
            is_hard=True,
            has_mold=False
        )

    def test_navigation_to_about(self):
        # Переход на главную страницу
        self.driver.get(self.live_server_url)
        # Находим ссылку "О проекте" и кликаем
        about_link = self.driver.find_element(By.LINK_TEXT, "О проекте")
        about_link.click()
        # Проверяем, что URL содержит '/about/'
        self.assertIn('/about/', self.driver.current_url)
        # Проверяем наличие заголовка "О проекте"
        header = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(header.text, "О проекте")

    def test_detail_page_has_title(self):
        # Переход на детальную страницу созданного сыра
        url = self.live_server_url + reverse('detail', args=[self.cheese.id])
        self.driver.get(url)
        # Ищем заголовок h1 с названием сыра
        header = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(header.text, self.cheese.name)



# Тесты для Chrome
'''
from django.test import TestCase, LiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from .models import Cheese

class CheeseModelTest(TestCase):
    def test_create_cheese_valid(self):
        cheese = Cheese.objects.create(
            name="Камамбер",
            milk_type="cow",
            fat_content=45.0,
            weight=0.250,
            is_hard=False,
            has_mold=True
        )
        self.assertEqual(cheese.name, "Камамбер")

    def test_fat_content_zero_should_raise(self):
        cheese = Cheese(
            name="Неверный",
            milk_type="cow",
            fat_content=0.0,
            is_hard=True
        )
        with self.assertRaises(Exception):
            cheese.save()

class SeleniumTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Автоматическая загрузка драйвера Chrome
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Создаём тестовый объект Cheese
        self.cheese = Cheese.objects.create(
            name="Пармезан",
            milk_type="cow",
            fat_content=32.0,
            weight=1.5,
            is_hard=True,
            has_mold=False
        )

    def test_navigation_to_about(self):
        # Переход на главную страницу
        self.driver.get(self.live_server_url)
        # Находим ссылку "О проекте" и кликаем
        about_link = self.driver.find_element(By.LINK_TEXT, "О проекте")
        about_link.click()
        # Проверяем, что URL содержит '/about/'
        self.assertIn('/about/', self.driver.current_url)
        # Проверяем наличие заголовка "О проекте"
        header = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(header.text, "О проекте")

    def test_detail_page_has_title(self):
        # Переход на детальную страницу созданного сыра
        url = self.live_server_url + reverse('detail', args=[self.cheese.id])
        self.driver.get(url)
        # Ищем заголовок h1 с названием сыра
        header = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(header.text, self.cheese.name)
'''