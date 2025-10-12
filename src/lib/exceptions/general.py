from fastapi import HTTPException


# Keep HTTPException compatibility for now. Reimplement in future to make it useful for internal exceptions too.
class GeneralException(HTTPException):
    pass
