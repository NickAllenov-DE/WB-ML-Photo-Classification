# Импорт библиотек и модулей
import requests  # Для выполнения HTTP-запросов
import os  # Для работы с операционной системой
import sys  # Для доступа к параметрам и функциям интерпретатора Python
import codecs  # Для работы с кодировками
from urllib.parse import urljoin  # Для объединения URL
from selenium import webdriver  # Для работы с браузером через Selenium
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
from selenium.webdriver.chrome.service import Service  # Для управления службой ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager  # Для автоматической установки ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait  # Для ожидания загрузки элементов
from selenium.webdriver.support import expected_conditions as EC  # Для условий ожидания
import time  # Для работы с временем
import random  # Для генерации случайных чисел
import csv  # Для работы с CSV-файлами
import logging  # Для ведения логов


TIMEOUT = (0.5, 2.0)

# Обработка кодировки для вывода в консоль
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Пользовательский агент для имитации браузера
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
# URL начальной страницы для парсинга
start_page_url = "https://www.wildberries.ru/catalog/detyam/tovary-dlya-malysha/podguzniki/podguzniki-detskie"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат сообщений
    handlers=[
        logging.FileHandler("logs/wb_data_parser.log"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ],
    encoding="utf-8"  # Кодировка логов
)


def setup_driver():
    """Настраивает и возвращает экземпляр Selenium WebDriver с заданными параметрами."""
    logging.info("Настройка веб-драйвера.")
    options = webdriver.ChromeOptions()  # Создание объекта с опциями для Chrome
    options.add_argument("--start-maximized")  # Запуск браузера в максимизированном режиме
    options.add_argument("--disable-blink-features=AutomationControlled")  # Отключение автоматического управления
    options.add_argument(f"user-agent={USER_AGENT}")  # Установка пользовательского агента
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)  # Инициализация драйвера
    return driver  # Возврат настроенного драйвера


def is_url_accessible(url, timeout=5):
    """Проверяет доступность указанного URL.
    Args:       url (str): URL, который нужно проверить.
                timeout (int): Таймаут для запроса в секундах.
    Returns:    bool: True, если URL доступен (статусы 200, 301, 302), иначе False.
    """
    try:
        response = requests.head(url, timeout=timeout)  # Выполнение HEAD-запроса с заданным таймаутом
        return response.status_code in (200, 301, 302)  # Проверка на доступные статусы
    except requests.RequestException as e:
        logging.error(f"Ошибка доступа к URL: {url}, ошибка: {e}")  # Логирование ошибки
        return False  # Возвращает False в случае ошибки


def scroll_page_to_bottom(driver):
    """Прокручивает страницу до самого низа."""
    logging.info("Начинаем прокрутку страницы до конца.")
    last_height = driver.execute_script("return document.body.scrollHeight")  # Получаем высоту страницы
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Прокрутка вниз
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание перед следующей прокруткой
        new_height = driver.execute_script("return document.body.scrollHeight")  # Получаем новую высоту
        if new_height == last_height:  # Если высота не изменилась, значит, достигли конца
            logging.info("Достигнут конец страницы.")
            break
        last_height = new_height  # Обновляем высоту для следующей итерации


def scroll_popup_to_bottom(driver, popup_element, scroll_pause_time=1):
    """Прокручивает всплывающее окно до самого низа."""
    logging.info("Начинаем прокрутку всплывающего окна.")
    last_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)  # Получаем высоту всплывающего окна
    
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup_element)  # Прокрутка вниз
        time.sleep(scroll_pause_time)  # Ожидание перед следующей прокруткой
        new_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)  # Получаем новую высоту
        if new_height == last_height:  # Если высота не изменилась, значит, достигли конца
            logging.info("Достигнут конец всплывающего окна.")
            break
        last_height = new_height  # Обновляем высоту для следующей итерации


def scroll_page_incrementally(driver, increment: float):
    """Прокручивает страницу на заданное количество пикселей, основанное на проценте от высоты страницы."""
    start_height = driver.execute_script("return document.body.scrollHeight")  # Получаем начальную высоту страницы
    scroll_increment = int(start_height * increment)  # Вычисляем количество пикселей для прокрутки
    new_scroll_position = 0  # Начальная позиция прокрутки

    logging.info(f"Прокручиваем страницу на {scroll_increment} пикселей.")
    while new_scroll_position < scroll_increment:
        driver.execute_script(f"window.scrollTo(0, {new_scroll_position});")  # Прокручиваем на заданное количество пикселей
        new_scroll_position += 2  # Увеличиваем позицию прокрутки на 2 пикселя


def get_next_page_button(driver):
    """Возвращает кнопку 'Следующая страница', если она доступна, иначе None."""
    try:
        next_button = driver.find_element(By.XPATH, '//*[@class="pagination-next pagination__next j-next-page"]')
        logging.info("Найдена кнопка 'Следующая страница'.")
        return next_button
    except Exception as e:
        logging.warning("Кнопка 'Следующая страница' не найдена: %s", e)
        return None


def get_product_links(driver, start_page):
    """Собирает ссылки на карточки товаров со страниц, начиная с заданного URL."""
    product_links = []  # Список для хранения ссылок на товары
    page_number = 1  # Номер текущей страницы

    while True:
        current_page_url = f"{start_page}?page={page_number}"
        
        # Проверка доступности текущей страницы
        if not is_url_accessible(current_page_url):
            logging.error(f"Страница недоступна: {current_page_url}")
            break  # Выход из цикла, если страница недоступна

        logging.info(f"Собираем ссылки на карточки товаров с страницы {page_number}.")
        driver.get(current_page_url)  # Переход на страницу
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки страницы
        scroll_page_to_bottom(driver)  # Прокрутка страницы до конца
        
        products = driver.find_elements(By.XPATH, '//article/div/a')  # Поиск элементов с товарами
        for product in products:
            link = product.get_attribute("href")  # Получение ссылки на товар
            if link:
                product_links.append(link)  # Добавление ссылки в список

        next_button = get_next_page_button(driver)  # Получение кнопки "Следующая страница"
        if next_button:
            next_button.click()  # Переход на следующую страницу
            time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки следующей страницы
            page_number += 1  # Увеличение номера страницы
        else:
            logging.info("Последняя страница достигнута.")
            break

    logging.info(f"Всего собрано {len(product_links)} ссылок на товары.")
    return product_links  # Возврат списка ссылок на товары


def get_price(driver):
    """Извлекает и форматирует цену товара."""
    try:
        price_element = driver.find_element(By.XPATH, '//ins[@class="price-block__final-price wallet"]')
        price_text = price_element.text  # Например, "1 234 ₽"
        price = int(price_text.replace("\u00A0", "").replace("₽", "").strip())  # Убираем пробелы и знак рубля
        return price
    except Exception as e:
        logging.error(f"Не удалось извлечь цену: {e}")
        return None


def get_full_description_button(driver):
    """Нажимает на кнопку 'Все характеристики и описание', чтобы открыть всплывающее окно с полными характеристиками."""
    try:
        button = driver.find_element(By.XPATH, '//button[contains(text(), "Все характеристики и описание")]')
        button.click()
        logging.info("Кнопка 'Все характеристики и описание' найдена и нажата.")
        time.sleep(random.uniform(1.5, 3.5))  # Ожидание открытия всплывающего окна
    except Exception as e:
        logging.error(f"Не удалось найти или нажать кнопку 'Все характеристики и описание': {e}")


def get_popup_data(driver):
    """Извлекает данные из всплывающего окна после его открытия."""
    try:
        # Подождем загрузку окна
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="popup-class"]')))
        
        # Здесь находим каждый элемент внутри окна по его XPATH и извлекаем данные
        color = driver.find_element(By.XPATH, '//*[@data-test="color"]').text
        product_type = driver.find_element(By.XPATH, '//*[@data-test="product-type"]').text
        number_units = driver.find_element(By.XPATH, '//*[@data-test="number-units"]').text
        weight_category = driver.find_element(By.XPATH, '//*[@data-test="weight-category"]').text
        producing_country = driver.find_element(By.XPATH, '//*[@data-test="producing-country"]').text
        overall_size = driver.find_element(By.XPATH, '//*[@data-test="overall-size"]').text
        description = driver.find_element(By.XPATH, '//*[@data-test="description"]').text

        popup_data = {
            "Цвет": color,
            "Тип подгузников": product_type,
            "Количество предметов": number_units,
            "Весовая группа": weight_category,
            "Страна производства": producing_country,
            "Габариты": overall_size,
            "Описание": description
        }
        return popup_data
    except Exception as e:
        logging.error(f"Ошибка при извлечении данных из всплывающего окна: {e}")
        return None

def get_product_data(driver, product_url):
    """Извлекает всю информацию о товаре, включая данные из всплывающего окна."""
    driver.get(product_url)
    time.sleep(random.uniform(*TIMEOUT))
    
    # Основные данные на странице товара
    product_id = driver.find_element(By.XPATH, '//*[@id="productNmId"]').text
    brand = driver.find_element(By.XPATH, '//*[@class="product-page__header"]/a').text
    name = driver.find_element(By.XPATH, '//*[@class="product-page__header"]/h1').text
    price = get_price(driver)  # Используем отдельную функцию для цены

    # Открываем всплывающее окно и извлекаем данные
    get_full_description_button(driver)
    popup_data = get_popup_data(driver)
    
    # Объединяем данные
    product_data = {
        "Артикул продукта": product_id,
        "Бренд": brand,
        "Название продукта": name,
        "Цена": price
    }
    
    # Если данные из всплывающего окна успешно получены, добавляем их к product_data
    if popup_data:
        product_data.update(popup_data)
    
    return product_data








def main():
    pass


if __name__ == "__main__":
    main()  # Запуск основной функции