import typing
from base64 import b64decode, b64encode
from dataclasses import dataclass, field
from functools import cached_property

from fastapi import Request, Response
from itsdangerous import TimestampSigner

from ..settings import get_session_settings, SessionSettings

settings = get_session_settings()


@dataclass(eq=False, order=False, repr=False, frozen=False)
class CookieManager:
    """A HTTP cookie manager."""

    session_cookie: str = field(default=settings.SESSION_ID_KEY)
    secret_key: str = field(default="secret")

    @cached_property
    def signer(self) -> TimestampSigner:
        "Cookie security signer"
        return TimestampSigner(str(self.secret_key))

    def has_cookie(self, request: Request) -> bool:
        """Check whether the session cookie exist in cookies sent in the request."""
        return self.session_cookie in request.cookies

    def get_cookie(self, request: Request) -> str:
        """Get a cookie by the cookie_name from the request."""
        signed_id = b64decode(request.cookies[self.session_cookie].encode("utf-8"))
        return self.signer.unsign(signed_id, max_age=settings.MAX_AGE).decode("utf-8")

    def set_cookie(self, response: Response, session_id: str) -> Response:
        """Set a cookie to the response."""
        signed_id = self.signer.sign(session_id)
        response.set_cookie(
            self.session_cookie,
            b64encode(signed_id).decode("utf-8"),
            max_age=settings.MAX_AGE,
            expires=settings.EXPIRES,
            path=settings.PATH,
            domain=settings.DOMAIN,
            secure=settings.SECURE,
            httponly=settings.HTTP_ONLY,
            samesite=settings.SAME_SITE,
        )
        return response

    def remove_cookie(self, response: Response) -> Response:
        response.delete_cookie(
            self.session_cookie, path=settings.PATH, domain=settings.DOMAIN
        )
        return response
