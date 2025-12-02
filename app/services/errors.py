class AppError(Exception):
    def __init__(self, message, code='APP_ERROR', http_status=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status