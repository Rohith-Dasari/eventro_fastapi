class EventNotFound(Exception):
    def __init__(self, message: str = "event not found", status_code: int = 404):
        super().__init__(message)
        self.status_code = status_code