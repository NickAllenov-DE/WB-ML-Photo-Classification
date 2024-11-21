
import os  # Для работы с операционной системой
from urllib.parse import urljoin  # Для объединения URL
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
from selenium.webdriver.support.ui import WebDriverWait  # Для ожидания загрузки элементов
from selenium.webdriver.support import expected_conditions as EC  # Для условий ожидания
import time  # Для работы с временем
import random  # Для генерации случайных чисел
import logging  # Для ведения логов
import pandas as pd

from utils import scroll_page_to_bottom, get_next_page_button
TIMEOUT = (0.5, 2.0)

def get_product_links(driver, start_page):
    """Собирает ссылки на карточки товаров со страниц, начиная с заданного URL."""
    product_links = []  # Список для хранения ссылок на товары
    page_number = 1  # Номер текущей страницы

    while page_number < 4:
        current_page_url = f"{start_page}?page={page_number}"
        
        logging.info(f"Собираем ссылки со страницы {page_number} ({current_page_url}).")
        driver.get(current_page_url)  # Переход на страницу
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки страницы
        scroll_page_to_bottom(driver)  # Прокрутка страницы до конца

        # Поиск элементов с товарами
        products = driver.find_elements(By.XPATH, '//article/div/a')
        if not products:
            logging.warning(f"На странице {page_number} не найдено товаров. Прерывание.")
            break

        # Получение ссылок
        page_links = [product.get_attribute("href") for product in products if product.get_attribute("href")]
        logging.info(f"На странице {page_number} найдено {len(page_links)} ссылок.")

        product_links.extend(page_links)  # Добавление ссылок в общий список

        # Проверяем наличие кнопки "Следующая страница"
        next_button = get_next_page_button(driver)
        if next_button:
            logging.info("Переход на следующую страницу.")
            next_button.click()  # Переход на следующую страницу
            time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки следующей страницы
            page_number += 1  # Увеличение номера страницы
        else:
            logging.info("Последняя страница достигнута. Завершаем сбор ссылок.")
            break

    logging.info(f"Сбор завершён. Всего собрано {len(product_links)} ссылок.")
    return product_links  # Возврат списка ссылок на товары


def get_price(driver):
    """Извлекает и форматирует цену товара."""
    try:
        # Находим элемент цены с использованием точного XPath
        price_element = driver.find_element(By.XPATH, '//*[@class="product-page__price-block product-page__price-block--common hide-mobile"]/div/div/div/div/p/span/ins')
        price_text = price_element.text  # Получаем текст, например, "2 437 ₽"

        # Проверяем, что текст цены не пуст
        if not price_text.strip():
            logging.error("Текст цены пустой. Проверьте XPath или структуру страницы.")
            return None

        # Убираем пробелы и символ рубля, затем преобразуем в число
        price = int(price_text.replace("\u00A0", "").replace("₽", "").strip())
        return price
    except ValueError as ve:
        # Логируем ошибку преобразования текста в число
        logging.error(f"Ошибка преобразования текста цены: '{price_text}' в число: {ve}")
        return None
    except Exception as e:
        # Общий обработчик ошибок
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


def close_description_window(driver):
    """Закрывает всплывающее окно 'Все характеристики и описание', если оно открыто."""
    try:
        # Проверяем, существует ли кнопка закрытия всплывающего окна
        close_button = driver.find_element(By.XPATH, '/html/body/div[1]/a')
        close_button.click()
        logging.info("Всплывающее окно успешно закрыто.")
    except Exception as e:
        logging.error(f"Не удалось закрыть всплывающее окно: {e}")


def get_description_data(driver):
    """Извлекает данные из всплывающего окна после его открытия."""
    try:
        # Подождем загрузку окна
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div')))
        logging.info("Всплывающее окно успешно загружено.")

        # Находим родительский элемент
        char_desc_elem = driver.find_element(By.XPATH, '/html/body/div[1]/div[@class="popup__content"]')

        popup_data = {}

        # Извлечение данных по каждому элементу
        try:
            color = char_desc_elem.find_element(By.XPATH, './/table[1]//td/span').text
            popup_data["color"] = color
            logging.info(f"Цвет товара: {color}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь цвет товара: {e}")
        
        try:
            number_units = char_desc_elem.find_element(By.XPATH, './/table[2]//td/span').text
            popup_data["number_of_units"] = number_units
            logging.info(f"Количество единиц в упаковке: {number_units}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь количество единиц: {e}")

        try:
            product_type = char_desc_elem.find_element(By.XPATH, './/table[3]//tbody/tr[1]/td/span').text
            popup_data["diapers_type"] = product_type
            logging.info(f"Тип товара: {product_type}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь тип товара: {e}")

        try:
            weight_category = char_desc_elem.find_element(By.XPATH, './/table[3]//tbody/tr[2]/td/span').text
            popup_data["weight_category"] = weight_category
            logging.info(f"Весовая категория: {weight_category}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь весовую категорию: {e}")

        try:
            shipping_weight = char_desc_elem.find_element(By.XPATH, './/table[3]//tbody/tr[3]/td/span').text
            popup_data["shipping_weight"] = shipping_weight
            logging.info(f"Вестовара с упаковкой: {shipping_weight}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь вестовара с упаковкой: {e}")

        try:
            producing_country = char_desc_elem.find_element(By.XPATH, './/table[3]//tbody/tr[4]/td/span').text
            popup_data["producing_country"] = producing_country
            logging.info(f"Страна производства: {producing_country}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь страну производства: {e}")

        try:
            equipment = char_desc_elem.find_element(By.XPATH, './/table[3]//tbody/tr[5]/td/span').text
            popup_data["equipment"] = equipment
            logging.info(f"Комплектация: {equipment}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь комплектацию: {e}")

        # Извлечение размеров упаковки
        try:
            length = char_desc_elem.find_element(By.XPATH, './/table[4]//tbody/tr[1]/td/span').text.strip().replace(' см', '')
            height = char_desc_elem.find_element(By.XPATH, './/table[4]//tbody/tr[2]/td/span').text.strip().replace(' см', '')
            width = char_desc_elem.find_element(By.XPATH, './/table[4]//tbody/tr[3]/td/span').text.strip().replace(' см', '')
            overall_size = f"{length}x{height}x{width}"
            popup_data["overall_size"] = overall_size
            logging.info(f"Габариты товара, см (ДхВхШ): {overall_size}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь размеры упаковки: {e}")

        try:
            description = char_desc_elem.find_element(By.XPATH, './/section/p').text
            popup_data["description"] = description
            logging.info(f"Описание товара: {description}")
        except Exception as e:
            logging.warning(f"Не удалось извлечь описание товара: {e}")

        return popup_data

    except Exception as e:
        logging.error(f"Ошибка при извлечении данных из всплывающего окна: {e}")
        return None



def get_product_data(driver, product_url):
    """Извлекает всю информацию о товаре, включая данные из всплывающего окна."""
    logging.info(f"Открываем страницу товара: {product_url}")
    driver.get(product_url)
    time.sleep(random.uniform(*TIMEOUT))
    
    # Извлекаем основные данные на странице товара
    try:
        product_id = driver.find_element(By.XPATH, '//*[@id="productNmId"]').text
        logging.info(f"Артикул товара: {product_id}")
    except Exception as e:
        logging.error(f"Не удалось извлечь артикул товара: {e}")
        product_id = None
    
    try:
        brand = driver.find_element(By.XPATH, '//*[@class="product-page__header"]/a').text
        logging.info(f"Бренд товара: {brand}")
    except Exception as e:
        logging.error(f"Не удалось извлечь бренд товара: {e}")
        brand = None
    
    try:
        name = driver.find_element(By.XPATH, '//*[@class="product-page__header"]/h1').text
        logging.info(f"Название товара: {name}")
    except Exception as e:
        logging.error(f"Не удалось извлечь название товара: {e}")
        name = None
    
    try:
        price = get_price(driver)  # Используем отдельную функцию для цены
        logging.info(f"Цена товара: {price}")
    except Exception as e:
        logging.error(f"Не удалось извлечь цену товара: {e}")
        price = None

    # Открываем всплывающее окно и извлекаем данные
    try:
        get_full_description_button(driver)
        popup_data = get_description_data(driver)
        logging.info("Данные из всплывающего окна успешно извлечены.")
        close_description_window(driver)    # Закрываем всплывающее окно
    except Exception as e:
        logging.error(f"Не удалось извлечь данные из всплывающего окна: {e}")
        popup_data = {}

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
    
    logging.info(f"Собраны данные о товаре: {product_data}")
    return product_data


def save_product_data_to_parquet(product_data, parquet_file):
    """Сохраняет данные о товаре в файл products.parquet."""
    try:
        # Создаем DataFrame для добавления данных о товаре
        df_product = pd.DataFrame([product_data])
        
        # Если файл существует, то добавляем новые данные, иначе создаем новый
        if os.path.exists(parquet_file):
            # Загружаем существующие данные
            existing_data = pd.read_parquet(parquet_file)
            # Добавляем новые данные с помощью concat
            updated_data = pd.concat([existing_data, df_product], ignore_index=True)
            # Сохраняем обновленные данные обратно в файл
            updated_data.to_parquet(parquet_file, index=False)
        else:
            # Если файл не существует, создаем новый
            df_product.to_parquet(parquet_file, index=False)
        
        logging.info(f"Данные о товаре сохранены в {parquet_file}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных о товаре: {e}")
        