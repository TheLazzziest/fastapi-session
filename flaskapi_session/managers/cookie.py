import typing
from base64 import b64decode, b64encode
from dataclasses import dataclass, field
from functools import cached_property

from fastapi import Request, Response
from itsdangerous import TimestampSigner

from .mixins import CookieSecuredMixin


@dataclass(eq=False, order=False, repr=False, frozen=False)
class CookieManager(CookieSecuredMixin):
    """A HTTP cookie manager."""

    session_cookie: str = field(default="FAPISESSID")
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
        return self.signer.unsign(signed_id, max_age=self.max_age).decode("utf-8")

    def set_cookie(self, response: Response, session_id: str) -> Response:
        """Set a cookie to the response."""
        signed_id = self.signer.sign(session_id)
        response.set_cookie(
            self.session_cookie,
            b64encode(signed_id).decode("utf-8"),
            max_age=self.max_age,
            expires=self.expires,
            path=self.path,
            domain=self.domain,
            secure=self.secure,
            httponly=self.http_only,
            samesite=self.same_site,
        )
        return response

    def remove_cookie(self, response: Response) -> Response:
        response.delete_cookie(self.session_cookie, path=self.path, domain=self.domain)
        return response
