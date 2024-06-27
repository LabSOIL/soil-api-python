from fastapi import HTTPException


class ValidationError(HTTPException):
    def __init__(self, loc: list, msg: str, error_type: str = "value_error"):
        super().__init__(
            status_code=400,
            detail=[{"loc": loc, "msg": msg, "type": error_type}],
        )
