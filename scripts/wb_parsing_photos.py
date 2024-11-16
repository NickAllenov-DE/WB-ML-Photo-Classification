

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
    time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки страницы

    scroll_page_incrementally(driver, 0.1)  # Инкрементальная прокрутка страницы
    time.sleep(1)  # Дополнительное ожидание

    try:
        show_all_photos_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="comments__user-opinion-right hide-mobile"]/button'))
        )
        show_all_photos_button.click()  # Клик по кнопке "Смотреть все фото"
        time.sleep(random.uniform(*TIMEOUT))  # Ожидание загрузки изображений
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


if __name__ == "__main__":
    main()  # Запуск основной функции
