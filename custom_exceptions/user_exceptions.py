class UserNotFoundError(BaseException):
    pass


class IncorrectCredentials(BaseException):
    pass


class UserAlreadyExists(BaseException):
    pass
