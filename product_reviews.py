
import requests  # Для выполнения HTTP-запросов
import os  # Для работы с операционной системой
from urllib.parse import urljoin  # Для объединения URL
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
from datetime import datetime, timedelta
import random  # Для генерации случайных чисел
import logging  # Для ведения логов
import pandas as pd

from utils import scroll_page_incrementally
TIMEOUT = (0.5, 2.0)

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


def get_author_name(review):
    try:
        return review.find_element(By.XPATH, './/div/div[2]/div/p').text
    except Exception as e:
        logging.warning(f"Ошибка при извлечении имени пользователя: {e}")
        return None


def get_review_date_and_rating(review):
    try:
        date_element = review.find_element(By.XPATH, './/div[@class="feedback__date"]')
        date, time, timezone = extract_date_time(date_element)

        rating_element = review.find_element(By.XPATH, './/span[contains(@class, "stars-line")]')
        rating_class = rating_element.get_attribute("class")
        rating = int(rating_class.split("star")[-1]) if "star" in rating_class else None

        return date, time, timezone, rating
    except Exception as e:
        logging.warning(f"Ошибка при извлечении данных о дате и рейтинге: {e}")
        return None, None, None, None


def get_review_text(review):
    try:
        full_text = ""
        pros_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item feedback__text--item-pro"]')
        if pros_element:
            full_text += f"Достоинства: {pros_element[0].text}\n"

        cons_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item feedback__text--item-con"]')
        if cons_element:
            full_text += f"Недостатки: {cons_element[0].text}\n"

        comments_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item"]')
        if comments_element:
            full_text += f"Комментарии: {comments_element[0].text}"
        
        return full_text.strip()
    except Exception as e:
        logging.warning(f"Ошибка при сборе текста отзыва: {e}")
        return None


def get_reviews_with_photos(driver, max_reviews=100):
    """Собирает только отзывы с фотографиями."""
    try:
        # Прокрутка страницы
        scroll_page_incrementally(driver, 0.2)
        time.sleep(random.uniform(*TIMEOUT))
    except Exception as e:
        logging.error(f"Ошибка при прокрутке страницы: {e}")
    
    # Переход к разделу отзывов
    try:
        reviews_button = driver.find_element(By.XPATH, '//a[contains(@class, "comments__btn-all") and @data-see-all="true"]')
        reviews_button.click()
        time.sleep(random.uniform(*TIMEOUT))
    except Exception as e:
        logging.warning(f"Не удалось открыть раздел отзывов: {e}")
        return []
    
    reviews_with_photos = []
    try:
        reviews = driver.find_elements(By.XPATH, '//ul[@class="comments__list"]/li')

        for index, review in enumerate(reviews):
            if len(reviews_with_photos) >= max_reviews:
                break

            # Логируем начало обработки отзыва
            logging.info(f"Обработка отзыва {index + 1} из {len(reviews)}")

            try:
                photo_elements = review.find_elements(By.XPATH, './/ul[@class="feedback__photos j-feedback-photos-scroll"]/li')
                if not photo_elements:
                    continue

                # Собираем данные отзыва
                review_data = {}
                photo_urls = [
                    photo.get_attribute("src").replace("ms.webp", "fs.webp") 
                    if "ms.webp" in photo.get_attribute("src") else photo.get_attribute("src")
                    for photo in photo_elements
                ]
                review_data["photo_urls"] = photo_urls

                # Получение имени автора
                try:
                    author_name = review.find_element(By.XPATH, './/div/div[2]/div/p').text
                    review_data["author_name"] = author_name
                except Exception as e:
                    logging.warning(f"Ошибка при извлечении имени пользователя для отзыва {index + 1}: {e}")
                    review_data["author_name"] = None

                # Дата и рейтинг
                try:
                    date_element = review.find_element(By.XPATH, './/div[@class="feedback__date"]')
                    date, time, timezone = extract_date_time(date_element)
                    review_data["date"] = date
                    review_data["time"] = time
                    review_data["timezone"] = timezone
                    
                    rating_element = review.find_element(By.XPATH, './/span[contains(@class, "stars-line")]')
                    rating_class = rating_element.get_attribute("class")
                    rating = int(rating_class.split("star")[-1]) if "star" in rating_class else None
                    review_data["rating"] = rating
                except Exception as e:
                    logging.warning(f"Ошибка при извлечении даты, времени или рейтинга отзыва {index + 1}: {e}")
                    review_data["date"] = None
                    review_data["time"] = None
                    review_data["timezone"] = None
                    review_data["rating"] = None

                # Текст отзыва
                try:
                    full_text = ""
                    pros_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item feedback__text--item-pro"]')
                    if pros_element:
                        full_text += f"Достоинства: {pros_element[0].text}\n"

                    cons_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item feedback__text--item-con"]')
                    if cons_element:
                        full_text += f"Недостатки: {cons_element[0].text}\n"

                    comments_element = review.find_elements(By.XPATH, './/p/span[@class="feedback__text--item"]')
                    if comments_element:
                        full_text += f"Комментарии: {comments_element[0].text}"
                    
                    review_data["review_text"] = full_text.strip()
                except Exception as e:
                    logging.warning(f"Ошибка при сборе текста отзыва {index + 1}: {e}")
                    review_data["review_text"] = None

                reviews_with_photos.append(review_data)
            except Exception as e:
                logging.error(f"Ошибка при обработке отзыва {index + 1}: {e}")

    except Exception as e:
        logging.error(f"Ошибка при извлечении отзывов: {e}")
    
    logging.info(f"Собрано {len(reviews_with_photos)} отзывов с фотографиями.")
    return reviews_with_photos


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


def download_images_from_reviews(reviews_parquet_file, save_directory):
    """Скачивает изображения из photo_urls, хранящихся в reviews.parquet, и сохраняет их в указанной директории."""
    try:
        # Загружаем DataFrame с отзывами
        reviews_df = pd.read_parquet(reviews_parquet_file)
        
        # Обрабатываем каждый отзыв
        for index, row in reviews_df.iterrows():
            photo_urls = row.get("photo_urls", [])
            if photo_urls:
                for url in photo_urls:
                    try:
                        img_data = requests.get(url).content  # Получаем содержимое изображения
                        img_name = f"review_{index + 1}_{photo_urls.index(url) + 1}.jpg"  # Генерация имени
                        img_path = os.path.join(save_directory, img_name)  # Путь для сохранения изображения
                        
                        # Записываем данные изображения в файл
                        with open(img_path, 'wb') as img_file:
                            img_file.write(img_data)
                        
                        logging.info(f"Изображение сохранено: {img_path}")
                    except Exception as e:
                        logging.error(f"Ошибка при сохранении изображения {url}: {e}")
    except Exception as e:
        logging.error(f"Ошибка при скачивании изображений: {e}")
