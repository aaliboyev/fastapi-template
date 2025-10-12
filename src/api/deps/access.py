from src.api.deps.auth import SessionUser


async def with_access_to(permission: str | list[str], _async=True):
    def has_permission(user: SessionUser):
        if isinstance(permission, list):
            for p in permission:
                user.can(p)
        else:
            user.can(permission)
        return user.can(permission)

    return has_permission
