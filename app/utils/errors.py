import logging

logger = logging.getLogger('campus_hub')


class AppError(Exception):
    """Application-specific exception with an error code and message.

    Optionally accepts an original_exception for debugging. On construction
    it will log the error so unexpected failures are visible in logs.
    """
    def __init__(self, code, message, original_exception=None, log=True):
        self.code = code
        self.message = message
        self.original_exception = original_exception
        if log:
            try:
                if original_exception:
                    logger.exception(f"{code}: {message}")
                else:
                    logger.error(f"{code}: {message}")
            except Exception:
                # never raise from the error class
                pass
        super().__init__(self.message)
