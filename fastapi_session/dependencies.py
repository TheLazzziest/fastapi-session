from fastapi import Request, Depends

from .sessions import AsyncSession
from .managers import SessionManager


def get_session_manager(request: Request) -> SessionManager:
    """Get a session manager as a dependency."""
    return request.app.session


async def get_user_session(
    request: Request, manager: SessionManager = Depends(get_session_manager)
) -> AsyncSession:
    """Get a user session as a dependency."""
    return await manager(request=request)
