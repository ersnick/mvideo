class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ProductNotFound(AppException):
    def __init__(self, product_id_or_url: str):
        super().__init__(f"Продукт с ID/URL {product_id_or_url} не найден", status_code=404)


class HistoryNotFound(AppException):
    def __init__(self, product_id_or_url: str):
        super().__init__(f"История цен для продукта с ID/URL {product_id_or_url} не найдена", status_code=404)


class DatabaseError(AppException):
    def __init__(self, message: str):
        super().__init__(f"Ошибка базы данных: {message}", status_code=500)


class RabbitMQError(AppException):
    def __init__(self, message: str):
        super().__init__(f"Ошибка RabbitMQ: {message}", status_code=500)
