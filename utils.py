
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
import logging  # Для ведения логов
import time  # Для работы с временем
import random  # Для генерации случайных чисел
TIMEOUT = (0.5, 2.0)


def scroll_page_to_bottom(driver, increment=0.1, step=300, max_retries=5):
    """
    Плавно прокручивает страницу, дожидаясь полной загрузки всех элементов.
    
    :param driver: WebDriver для взаимодействия с браузером.
    :param increment: Доля высоты страницы, на которую нужно прокрутить за один цикл.
    :param step: Шаг прокрутки в пикселях, чтобы обеспечить плавное движение.
    :param max_retries: Максимальное количество попыток для загрузки всех элементов.
    """
    logging.info("Начинаем плавную прокрутку страницы.")

    last_height = driver.execute_script("return document.body.scrollHeight")  # Текущая высота страницы
    retries = 0  # Счётчик попыток
    while retries < max_retries:
        current_scroll_position = 0
        while current_scroll_position < last_height:
            # Прокручиваем страницу на шаг `step`
            driver.execute_script(f"window.scrollTo(0, {current_scroll_position});")
            current_scroll_position += step
            time.sleep(0.01)  # Короткая пауза для плавности

        time.sleep(random.uniform(*TIMEOUT))  # Делаем паузу, чтобы подгрузились элементы

        # Проверяем, изменилась ли высота страницы
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            logging.info("Высота страницы не изменилась. Проверяем количество загруженных элементов.")
            products = driver.find_elements(By.XPATH, '//article/div/a')
            if len(products) >= 100 or retries >= max_retries:
                logging.info(f"Достигнуто {len(products)} элементов. Прокрутка завершена.")
                break
            else:
                logging.warning(f"Элементов загружено {len(products)}, требуется повторная прокрутка.")
                retries += 1
                continue  # Повторяем цикл
        else:
            last_height = new_height
            retries = 0  # Сброс счётчика при изменении высоты страницы

    # Прокручиваем до самого конца
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    logging.info("Плавная прокрутка страницы завершена.")



def scroll_page_incrementally(driver, increment: float):
    """Прокручивает страницу на заданное количество пикселей, основанное на проценте от высоты страницы."""
    start_height = driver.execute_script("return document.body.scrollHeight")  # Получаем начальную высоту страницы
    scroll_increment = int(start_height * increment)  # Вычисляем количество пикселей для прокрутки
    new_scroll_position = 0  # Начальная позиция прокрутки

    logging.info(f"Прокручиваем страницу на {scroll_increment} пикселей.")
    while new_scroll_position < scroll_increment:
        driver.execute_script(f"window.scrollTo(0, {new_scroll_position});")  # Прокручиваем на заданное количество пикселей
        new_scroll_position += 2  # Увеличиваем позицию прокрутки на 2 пикселя


def scroll_popup_to_bottom(driver, popup_element):
    """Прокручивает всплывающее окно до самого низа."""
    logging.info("Начинаем прокрутку всплывающего окна.")
    last_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)  # Получаем высоту всплывающего окна
    
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup_element)  # Прокрутка вниз
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание перед следующей прокруткой
        new_height = driver.execute_script("return arguments[0].scrollHeight", popup_element)  # Получаем новую высоту
        if new_height == last_height:  # Если высота не изменилась, значит, достигли конца
            logging.info("Достигнут конец всплывающего окна.")
            break
        last_height = new_height  # Обновляем высоту для следующей итерации


def get_next_page_button(driver):
    """Возвращает кнопку 'Следующая страница', если она доступна, иначе None."""
    try:
        next_button = driver.find_element(By.XPATH, '//*[@class="pagination-next pagination__next j-next-page"]')
        logging.info("Найдена кнопка 'Следующая страница'.")
        return next_button
    except Exception as e:
        logging.warning("Кнопка 'Следующая страница' не найдена: %s", e)
        return None
