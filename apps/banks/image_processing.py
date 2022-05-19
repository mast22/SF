from typing import Tuple
from PIL import Image


class ImageProcessing:
    """ Обработка изображения
    Подбирает определенный размер изображения и разрешения для банка
    """

    def __init__(self, image_path: str):
        """ Задаются ограничения банка и фото """
        # TODO узнать требования банков для удовлетворения фоток
        #   Однако сейчас достаточно захардкодить требования ОТП
        self.res = (640, 480)
        self.size = 1024 * 1024
        self.image = Image.open(image_path)
        # Копия изображения, которое будет подвергаться изменениям
        self.processed_image = None

    def get_image_size(self):
        """ Получить размер изображения """
        pass

    def meets_reqs(self):
        """ Проверяет соответствие картинки требуемым ограничениям """
        size = self.get_image_size()
        if size < self.size:
            pass

    def process_image(self):
        """ Триггер обработки изображения """
        # Всегда работаем с RGB (jpg)
        self.processed_image = self.image.convert('RGB')

        image_meets_requirements = self.meets_reqs()
        if image_meets_requirements:
            return self.processed_image

        # Продолжаем изменять картинку
