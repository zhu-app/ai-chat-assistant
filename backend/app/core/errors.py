"""应用层业务错误，路由层映射为 HTTP 状态码。"""


class AppError(Exception):
    """可映射为 HTTP 响应的业务异常。"""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class SessionNotFoundError(AppError):
    def __init__(self, detail: str = '会话不存在') -> None:
        super().__init__(404, detail)


class SessionForbiddenError(AppError):
    def __init__(self, detail: str = '无权访问该会话') -> None:
        super().__init__(403, detail)
