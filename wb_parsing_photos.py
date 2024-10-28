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
        logging.FileHandler("wb-parser.log"),  # Логирование в файл
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
        time.sleep(random.uniform(1.5, 3.5))  # Ожидание перед следующей прокруткой
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
        time.sleep(random.uniform(1.5, 3.5))  # Ожидание загрузки страницы
        scroll_page_to_bottom(driver)  # Прокрутка страницы до конца
        
        products = driver.find_elements(By.XPATH, '//article/div/a')  # Поиск элементов с товарами
        for product in products:
            link = product.get_attribute("href")  # Получение ссылки на товар
            if link:
                product_links.append(link)  # Добавление ссылки в список

        next_button = get_next_page_button(driver)  # Получение кнопки "Следующая страница"
        if next_button:
            next_button.click()  # Переход на следующую страницу
            time.sleep(random.uniform(1.5, 3.5))  # Ожидание загрузки следующей страницы
            page_number += 1  # Увеличение номера страницы
        else:
            logging.info("Последняя страница достигнута.")
            break

    logging.info(f"Всего собрано {len(product_links)} ссылок на товары.")
    return product_links  # Возврат списка ссылок на товары


def download_image(img_url, save_directory, img_name):
    """Скачивает изображение по заданному URL и сохраняет его в указанной директории."""

    if not is_url_accessible(img_url):      # Проверка доступности img_url перед загрузкой изображения.
        logging.error(f"Изображение недоступно: {img_url}")
        return None  # Возврат None, если изображение недоступно

    try:
        img_data = requests.get(img_url).content  # Получение содержимого изображения
        img_path = os.path.join(save_directory, img_name)  # Полный путь для сохранения изображения
        with open(img_path, 'wb') as img_file:
            img_file.write(img_data)  # Запись данных изображения в файл
        logging.info(f"Изображение сохранено: {img_path}")
        return img_path  # Возврат пути к сохраненному изображению
    except Exception as e:
        logging.error(f"Ошибка при сохранении изображения: {e}")
        return None  # Возврат None в случае ошибки


def get_feedback_images(driver, product_card_url, save_directory, csv_writer, index, existing_images):
    """Скачивает изображения отзывов для заданной карточки товара."""
    
    logging.info(f"Обрабатываем карточку товара: {product_card_url}")

    if not is_url_accessible(product_card_url):     # Проверка доступности URL перед переходом на страницу товара
        logging.error(f"Карточка товара недоступна: {product_card_url}")
        return  # Выход из функции, если URL недоступен
    
    driver.get(product_card_url)  # Переход на страницу товара
    time.sleep(random.uniform(1.5, 3.5))  # Ожидание загрузки страницы

    scroll_page_incrementally(driver, 0.1)  # Инкрементальная прокрутка страницы
    time.sleep(1)  # Дополнительное ожидание

    try:
        show_all_photos_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="comments__user-opinion-right hide-mobile"]/button'))
        )
        show_all_photos_button.click()  # Клик по кнопке "Смотреть все фото"
        time.sleep(random.uniform(1.5, 3.5))  # Ожидание загрузки изображений
    except Exception as e:
        logging.warning(f"Кнопка 'Смотреть все фото' не найдена для {product_card_url}: {e}")
        return  # Выход из функции, если кнопка не найдена

    try:
        popup_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div'))
        )
        
        images = popup_element.find_elements(By.XPATH, './/li/img')  # Поиск изображений в всплывающем окне
        logging.info(f"Найдено {len(images)} изображений для товара: {product_card_url}")

        if not os.path.exists(save_directory):
            os.makedirs(save_directory)  # Создание директории для сохранения изображений, если она не существует

        for img_index, img in enumerate(images):
            img_url = img.get_attribute('src')  # Получение URL изображения

            if img_url not in existing_images:  # Проверка на дубликат
                existing_images.add(img_url)  # Добавление URL в множество существующих изображений
                img_name = f"product_{index + 1}_{img_index + 1}.jpg"  # Формирование имени файла
                img_path = download_image(img_url, save_directory, img_name)  # Скачивание изображения

                if img_path:
                    csv_writer.writerow([f"{index + 1}_{img_index + 1}", product_card_url, img_url, img_path])  # Запись данных в CSV
            else:
                logging.info(f"Дубликат изображения пропущен: {img_url}")  # Логирование дубликатов

    except Exception as e:
        logging.error(f"Ошибка при загрузке изображений для {product_card_url}: {e}")


def main():
    """Основная функция для запуска процесса парсинга."""
    logging.info("Запуск основного процесса.")
    driver = setup_driver()  # Настройка веб-драйвера
    csv_file = "feedback_images.csv"  # Имя CSV-файла для сохранения данных
    dir_to_save = os.path.join(os.getcwd(), "wb-diapers-photos")  # Директория для сохранения изображений

    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file, delimiter=',')  # Создание CSV-писателя
        csv_writer.writerow(['index', 'product_url', 'photo_url', 'local_path'])  # Заголовки столбцов
        existing_images = set()  # Множество для хранения существующих изображений

        try:
            product_cards_list = get_product_links(driver, start_page_url)  # Получение ссылок на карточки товаров
            for index, product_card in enumerate(product_cards_list):
                get_feedback_images(driver, product_card, dir_to_save, csv_writer, index, existing_images)  # Скачивание изображений для каждого товара
        except Exception as e:
            logging.error(f"Ошибка в основном процессе: {e}")
        finally:
            driver.quit()  # Закрытие драйвера
            logging.info("Процесс завершен.")


if __name__ == "__main__":
    main()  # Запуск основной функции
