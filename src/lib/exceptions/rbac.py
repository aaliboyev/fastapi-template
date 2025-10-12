from fastapi import status

from src.lib.exceptions.general import GeneralException


class RequiresPermission(GeneralException):
    def __init__(self, permission: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Subject must have '{permission}' permission to perform this action.",
        )


class InvalidSession(GeneralException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid session"
        )


class ResourceNotFound(GeneralException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requested resource not found"
        )


class InvalidOAuthAccess(GeneralException):
    def __init__(self, provider):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "InvalidOAuthAccess",
                "provider": provider,
                "message": "Authentication with access token failed.",
            },
        )


class InvalidThirdPartyAPIAccess(GeneralException):
    def __init__(self, provider, action):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "InvalidThirdPartyAPIAccess",
                "provider": provider,
                "action": action,
                "message": f"Your access configuration for {provider} doesn't allow `{action}` action",
            },
        )


class ThirdPartyAPIAccessRequired(GeneralException):
    def __init__(self, provider: str, scopes: list | None = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "ThirdPartyAPIAccessRequired",
                "provider": provider,
                "scopes": scopes,
                "message": f"Access to your {provider} account required",
            },
        )
