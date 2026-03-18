from django.test import TestCase, LiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        edge_options.add_argument("--headless")  # Опционально: запуск в фоновом режиме

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
        # Создаем тестовый объект Cheese
        self.cheese = Cheese.objects.create(
            name="Пармезан",
            milk_type="cow",
            fat_content=32.0,
            weight=1.5,
            is_hard=True,
            has_mold=False
        )

        # Создаем дополнительный сыр для тестирования списка
        self.cheese2 = Cheese.objects.create(
            name="Камамбер",
            milk_type="cow",
            fat_content=45.0,
            weight=0.250,
            is_hard=False,
            has_mold=True
        )

    def test_navigation_to_about(self):
        """Тест навигации на страницу 'О проекте'"""
        # Переход на главную страницу
        self.driver.get(self.live_server_url)

        # Ждем загрузки страницы и находим ссылку
        about_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "О проекте"))
        )
        about_link.click()

        # Проверяем URL
        self.wait.until(
            EC.url_contains('/about/')
        )
        self.assertIn('/about/', self.driver.current_url)

        # Проверяем заголовок
        header = self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertEqual(header.text, "О проекте")

    def test_detail_page_has_title(self):
        """Тест наличия заголовка на детальной странице"""
        url = self.live_server_url + reverse('detail', args=[self.cheese.id])
        self.driver.get(url)

        # Ищем заголовок h1 с названием сыра
        header = self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertEqual(header.text, self.cheese.name)

    def test_index_page_contains_cheese_list(self):
        """Тест наличия списка сыров на главной странице"""
        self.driver.get(self.live_server_url)

        # Ищем ссылки на сыры
        cheese_links = self.driver.find_elements(By.XPATH, "//li/a[contains(@href, '/cheese/')]")

        # Проверяем, что оба сыра присутствуют в списке
        found_names = [link.text for link in cheese_links]
        self.assertIn(self.cheese.name, found_names)
        self.assertIn(self.cheese2.name, found_names)

    def test_filter_form_exists(self):
        """Тест наличия формы фильтрации на главной странице"""
        self.driver.get(self.live_server_url)

        # Проверяем наличие формы
        filter_form = self.driver.find_element(By.TAG_NAME, "form")
        self.assertIsNotNone(filter_form)

        # Проверяем наличие поля ввода названия
        name_input = self.driver.find_element(By.NAME, "name")
        self.assertIsNotNone(name_input)

    def test_add_cheese_link_exists(self):
        """Тест наличия ссылки на добавление сыра"""
        self.driver.get(self.live_server_url)

        # Проверяем наличие ссылки на добавление сыра
        add_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "Добавить")
        self.assertIsNotNone(add_link)
        self.assertIn(reverse('cheese_add'), add_link.get_attribute('href'))

    def test_cheese_detail_has_all_attributes(self):
        """Тест отображения всех атрибутов сыра на детальной странице"""
        url = self.live_server_url + reverse('detail', args=[self.cheese.id])
        self.driver.get(url)

        # Проверяем наличие названия
        header = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(header.text, self.cheese.name)

        # Проверяем наличие типа молока
        page_text = self.driver.page_source
        self.assertIn("коровье", page_text)  # milk_type="cow" отображается как "коровье"

        # Проверяем наличие жирности
        self.assertIn(str(self.cheese.fat_content), page_text)

        # Проверяем наличие информации о твердости
        self.assertIn("да", page_text)  # is_hard=True

        # Проверяем наличие обратной ссылки
        back_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "Назад")
        self.assertIsNotNone(back_link)

    def test_edit_link_on_index_page(self):
        """Тест наличия ссылки на редактирование на главной странице"""
        self.driver.get(self.live_server_url)

        # Ищем ссылку на редактирование для первого сыра
        edit_link = self.driver.find_element(By.XPATH, f"//a[contains(@href, '/{self.cheese.id}/edit/')]")
        self.assertIsNotNone(edit_link)
        self.assertEqual(edit_link.text.strip(), "Редактировать")

    def test_delete_link_on_index_page(self):
        """Тест наличия ссылки на удаление на главной странице"""
        self.driver.get(self.live_server_url)

        # Ищем ссылку на удаление для первого сыра
        delete_link = self.driver.find_element(By.XPATH, f"//a[contains(@href, '/{self.cheese.id}/delete/')]")
        self.assertIsNotNone(delete_link)
        self.assertEqual(delete_link.text.strip(), "Удалить")

    def test_create_new_cheese(self):
        """Тест создания нового сыра через форму"""
        self.driver.get(self.live_server_url + reverse('cheese_add'))

        # Заполняем форму
        name_input = self.driver.find_element(By.NAME, "name")
        name_input.send_keys("Тестовый сыр")

        milk_type_select = self.driver.find_element(By.NAME, "milk_type")
        milk_type_select.send_keys("козье")  # или можно выбрать по значению "goat"

        fat_input = self.driver.find_element(By.NAME, "fat_content")
        fat_input.send_keys("25.5")

        weight_input = self.driver.find_element(By.NAME, "weight")
        weight_input.send_keys("0.5")

        is_hard_checkbox = self.driver.find_element(By.NAME, "is_hard")
        if not is_hard_checkbox.is_selected():
            is_hard_checkbox.click()

        # Отправляем форму
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # Ждем перенаправления на главную страницу
        self.wait.until(
            EC.url_to_be(self.live_server_url + reverse('index'))
        )

        # Проверяем, что новый сыр появился в списке
        page_source = self.driver.page_source
        self.assertIn("Тестовый сыр", page_source)

    def test_filter_by_name(self):
        """Тест фильтрации по названию"""
        self.driver.get(self.live_server_url)

        # Находим поле поиска по имени и вводим значение
        name_input = self.driver.find_element(By.NAME, "name")
        name_input.send_keys("Пармезан")

        # Находим и нажимаем кнопку "Применить фильтр"
        submit_button = self.driver.find_element(By.XPATH, "//button[text()='Применить фильтр']")
        submit_button.click()

        # Проверяем, что в результатах есть Пармезан, но нет Камамбера
        page_source = self.driver.page_source
        self.assertIn("Пармезан", page_source)
        self.assertNotIn("Камамбер", page_source)

    def test_filter_by_milk_type(self):
        """Тест фильтрации по типу молока"""
        self.driver.get(self.live_server_url)

        # Выбираем тип молока (оба сыра - коровье)
        milk_type_select = self.driver.find_element(By.NAME, "milk_type")
        milk_type_select.send_keys("коровье")

        # Применяем фильтр
        submit_button = self.driver.find_element(By.XPATH, "//button[text()='Применить фильтр']")
        submit_button.click()

        # Проверяем, что оба сыра отображаются (оба коровьи)
        page_source = self.driver.page_source
        self.assertIn("Пармезан", page_source)
        self.assertIn("Камамбер", page_source)

    def test_filter_by_fat_range(self):
        """Тест фильтрации по диапазону жирности"""
        self.driver.get(self.live_server_url)

        # Задаем диапазон жирности от 30 до 40
        fat_min = self.driver.find_element(By.NAME, "fat_min")
        fat_min.send_keys("30")

        fat_max = self.driver.find_element(By.NAME, "fat_max")
        fat_max.send_keys("40")

        # Применяем фильтр
        submit_button = self.driver.find_element(By.XPATH, "//button[text()='Применить фильтр']")
        submit_button.click()

        # Пармезан (32%) должен быть, Камамбер (45%) - нет
        page_source = self.driver.page_source
        self.assertIn("Пармезан", page_source)
        self.assertNotIn("Камамбер", page_source)

    def test_filter_by_is_hard(self):
        """Тест фильтрации по твердости"""
        self.driver.get(self.live_server_url)

        # Выбираем "Твёрдый: Да" (Пармезан твердый, Камамбер - нет)
        is_hard_select = self.driver.find_element(By.NAME, "is_hard")
        is_hard_select.send_keys("Да")

        # Применяем фильтр
        submit_button = self.driver.find_element(By.XPATH, "//button[text()='Применить фильтр']")
        submit_button.click()

        # Должен быть только Пармезан
        page_source = self.driver.page_source
        self.assertIn("Пармезан", page_source)
        self.assertNotIn("Камамбер", page_source)