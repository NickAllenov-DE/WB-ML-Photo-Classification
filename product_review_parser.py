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
from datetime import datetime, timedelta
import random  # Для генерации случайных чисел
import csv  # Для работы с CSV-файлами
import logging  # Для ведения логов
from tqdm import tqdm
import pandas as pd


TIMEOUT = (0.25, 1.75)

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
        logging.FileHandler("logs/wb_images_parser.log"),  # Логирование в файл
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
        price_element = driver.find_element(By.XPATH, '//*[@id="b88bf175-c0d2-fec2-0220-3447970e41fa"]/div[3]/div[2]/div/div/div/div/p/span/ins')
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
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание открытия всплывающего окна
    except Exception as e:
        logging.error(f"Не удалось найти или нажать кнопку 'Все характеристики и описание': {e}")


def get_popup_data(driver):
    """Извлекает данные из всплывающего окна после его открытия."""
    try:
        # Подождем загрузку окна
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div')))
        
        # Находим каждый элемент внутри окна по его XPATH и извлекаем данные
        color = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[1]/tbody/tr/td/span').text
        product_type = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[3]/tbody/tr[1]/td/span').text
        number_units = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[2]/tbody/tr/td/span').text
        weight_category = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[3]/tbody/tr[2]/td/span').text
        producing_country = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[3]/tbody/tr[4]/td/span').text

        # Извлечение размеров упаковки
        length = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[4]/tbody/tr[1]/td/span').text.strip().replace(' см', '')
        height = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[4]/tbody/tr[2]/td/span').text.strip().replace(' см', '')
        width = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/table[4]/tbody/tr[3]/td/span').text.strip().replace(' см', '')
        
        # Форматируем габариты
        overall_size = f"{width}x{height}x{length}"

        description = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/section/p').text

        popup_data = {
            "color": color,
            "diapers_type": product_type,
            "number_of_units": number_units,
            "weight_category": weight_category,
            "producing_country": producing_country,
            "overall_size": overall_size,
            "description": description
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
        "product_article": product_id,
        "brand": brand,
        "name": name,
        "price": price
    }
    
    # Если данные из всплывающего окна успешно получены, добавляем их к product_data
    if popup_data:
        product_data.update(popup_data)
    
    return product_data


def extract_date_time(date_element):
    """
    Извлекает дату и время из HTML-элемента и приводит их к нормальному формату.
    
    Args: date_element: WebElement содержащий атрибут 'content' с датой и временем.
    Returns: tuple: (строка с датой, строка с временем в формате HH:MM:SS, строка с часовым поясом)
    """
    try:
        # Извлекаем ISO-строку
        date_time_iso = date_element.get_attribute("content").rstrip("Z")
        
        # Преобразуем ISO в объект datetime
        date_time_obj = datetime.strptime(date_time_iso, "%Y-%m-%dT%H:%M:%S")
        
        # Добавляем 3 часа (часовой пояс Москвы)
        date_time_obj_with_tz = date_time_obj + timedelta(hours=3)
        
        # Извлекаем дату и время в нужных форматах
        date_str = date_time_obj_with_tz.strftime("%Y-%m-%d")
        time_str = date_time_obj_with_tz.strftime("%H:%M:%S")
        timezone_str = "+03:00"
        
        return date_str, time_str, timezone_str
    except Exception as e:
        logging.warning(f"Ошибка при извлечении даты и времени: {e}")
        return None, None, None


def get_reviews_with_photos(driver, max_reviews=100):
    """Собирает только отзывы с фотографиями, включая имя автора, дату, оценку, текст и ссылки на фото."""
    
    # Прокрутка страницы немного вниз для появления кнопки "Смотреть все отзывы"
    scroll_page_incrementally(driver, 0.2)
    time.sleep(random.uniform(*TIMEOUT))

    # Переход к разделу отзывов
    try:
        # Кнопка для открытия раздела отзывов
        reviews_button = driver.find_element(By.XPATH, '//a[contains(@class, "comments__btn-all") and @data-see-all="true"]')
        reviews_button.click()
        time.sleep(random.uniform(*TIMEOUT))
    except Exception as e:
        logging.warning(f"Не удалось открыть раздел отзывов: {e}")
        return []
    
    # Прокрутка раздела отзывов до конца для загрузки всех данных
    scroll_page_to_bottom(driver)

    # Сбор данных по отзывам
    reviews_with_photos = []
    try:
        reviews = driver.find_elements(By.XPATH, '//ul[@class="comments__list"]/li')

        for review in reviews:
            # Проверка, достигнуто ли максимальное количество отзывов
            if len(reviews_with_photos) >= max_reviews:
                break
            
            # Проверяем, есть ли фотографии в отзыве
            try:
                photo_elements = review.find_elements(By.XPATH, '//ul[@class = "feedback__photos j-feedback-photos-scroll"]/li')
                if not photo_elements:
                    continue  # Пропускаем отзывы без фотографий

                # Инициализируем данные для отзыва
                review_data = {}

                # Сохраняем ссылки на фотографии
                photo_urls = [
                    photo.get_attribute("src").replace("ms.webp", "fs.webp") 
                    if "ms.webp" in photo.get_attribute("src") else photo.get_attribute("src")
                    for photo in photo_elements
                ]
                review_data["photo_urls"] = photo_urls

                # Получение имени пользователя
                try:
                    try:
                        author_name = review.find_element(By.XPATH, './/div/div[2]/div/p').text  # Обычный пользователь
                    except:
                        author_name = review.find_element(By.XPATH, './/div/div[2]/div/div/p').text  # Премиум пользователь
                    review_data["author_name"] = author_name
                except Exception as e:
                    logging.warning(f"Ошибка при извлечении имени пользователя: {e}")
                    review_data["author_name"] = None

                # Получение даты и рейтинга
                try:
                    # Извлечение элемента даты
                    date_element = review.find_element(By.XPATH, './/div[@class="feedback__date"]')
                    
                    # Используем функцию для получения даты, времени и часового пояса
                    date, time, timezone = extract_date_time(date_element)
                    
                    # Сохраняем в словарь отзыва
                    review_data["date"] = date
                    review_data["time"] = time
                    review_data["timezone"] = timezone
                    
                    # Извлечение рейтинга
                    rating_element = review.find_element(By.XPATH, './/span[contains(@class, "stars-line")]')
                    rating_class = rating_element.get_attribute("class")
                    rating = int(rating_class.split("star")[-1]) if "star" in rating_class else None
                    review_data["rating"] = rating
                except Exception as e:
                    logging.warning(f"Ошибка при извлечении даты, времени или рейтинга: {e}")
                    review_data["date"] = None
                    review_data["time"] = None
                    review_data["timezone"] = None
                    review_data["rating"] = None

                # Сбор текста отзыва
                try:
                    full_text = ""

                    # Достоинства
                    pros_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item feedback__text--item-pro"]')
                    if pros_element:
                        pros_text = pros_element[0].text
                        full_text += f"Достоинства: {pros_text}\n"

                    # Недостатки
                    cons_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item feedback__text--item-con"]')
                    if cons_element:
                        cons_text = cons_element[0].text
                        full_text += f"Недостатки: {cons_text}\n"

                    # Комментарии
                    comments_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item"]')
                    if comments_element:
                        comments_text = comments_element[0].text
                        full_text += f"Комментарии: {comments_text}"

                    review_data["review_text"] = full_text.strip()

                except Exception as e:
                    logging.warning(f"Ошибка при сборе текста отзыва: {e}")
                    review_data["review_text"] = None

                # Добавляем собранный отзыв с фото в список
                reviews_with_photos.append(review_data)

            except Exception as e:
                logging.error(f"Ошибка при обработке отзыва: {e}")

    except Exception as e:
        logging.error(f"Ошибка при извлечении отзывов: {e}")
    
    logging.info(f"Собрано {len(reviews_with_photos)} отзывов с фотографиями.")
    return reviews_with_photos



def save_product_data_to_parquet(product_data, parquet_file):
    """Сохраняет данные о товаре в файл products.parquet."""
    try:
        # Создаем DataFrame для добавления данных о товаре
        df_product = pd.DataFrame([product_data])
        
        # Если файл существует, то добавляем новые данные, иначе создаем новый
        if os.path.exists(parquet_file):
            df_product.to_parquet(parquet_file, append=True, index=False)
        else:
            df_product.to_parquet(parquet_file, index=False)
        
        logging.info(f"Данные о товаре сохранены в {parquet_file}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных о товаре: {e}")


def save_review_data_to_parquet(review_data, parquet_file):
    """Сохраняет данные о отзыве в файл reviews.parquet."""
    try:
        # Создаем DataFrame для добавления данных отзыва
        df_review = pd.DataFrame([review_data])
        
        # Если файл существует, то добавляем новые данные, иначе создаем новый
        if os.path.exists(parquet_file):
            df_review.to_parquet(parquet_file, append=True, index=False)
        else:
            df_review.to_parquet(parquet_file, index=False)
        
        logging.info(f"Данные отзыва сохранены в {parquet_file}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных отзыва: {e}")


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


def download_images_from_reviews(reviews_parquet_file, save_directory):
    """Скачивает изображения из photo_urls, хранящихся в reviews.parquet."""
    try:
        # Загружаем DataFrame с отзывами
        reviews_df = pd.read_parquet(reviews_parquet_file)
        
        # Обрабатываем каждый отзыв
        for index, row in reviews_df.iterrows():
            photo_urls = row.get("photo_urls", [])
            if photo_urls:
                for url in photo_urls:
                    # Генерируем имя для изображения (например, индекс отзыва)
                    img_name = f"review_{index + 1}_{photo_urls.index(url) + 1}.jpg"
                    # Скачиваем изображение
                    img_path = download_image(url, save_directory, img_name)
                    if img_path:
                        logging.info(f"Изображение сохранено: {img_path}")
    except Exception as e:
        logging.error(f"Ошибка при скачивании изображений: {e}")



def main():
    """Основная функция для запуска процесса парсинга и сохранения данных."""
    logging.info("Запуск основного процесса.")
    driver = setup_driver()  # Настройка веб-драйвера
    product_parquet_file = r"d:\Projects\CurrentProjects\WB-ML-Photo-Classification\products.parquet"  # Путь для сохранения данных о товарах
    review_parquet_file = r"d:\Projects\CurrentProjects\WB-ML-Photo-Classification\reviews.parquet"  # Путь для сохранения данных о отзывах
    dir_to_save = r"d:\Projects\CurrentProjects\WB-ML-Photo-Classification\wb-diapers-photos"  # Директория для сохранения изображений

    try:
        product_cards_list = get_product_links(driver, start_page_url)  # Получение ссылок на карточки товаров
        for product_card in product_cards_list:
            # Сбор данных о товаре и сохранение в products.parquet
            product_data = get_product_data(driver, product_card)
            save_product_data_to_parquet(product_data, product_parquet_file)
            
            # Сбор данных о отзывах и сохранение в reviews.parquet
            reviews_with_photos = get_reviews_with_photos(driver)
            for review_data in reviews_with_photos:
                save_review_data_to_parquet(review_data, review_parquet_file)

        # Скачивание изображений, используя URLs из reviews.parquet
        download_images_from_reviews(review_parquet_file, dir_to_save)

    except Exception as e:
        logging.error(f"Ошибка в основном процессе: {e}")
    finally:
        driver.quit()  # Закрытие драйвера
        logging.info("Процесс завершен.")



if __name__ == "__main__":
    main()