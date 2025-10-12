import uuid
from http.cookies import SimpleCookie
from typing import Any

from authx._internal import SignatureSerializer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.config import settings


class SessionIntegration:
    def __init__(self, memory, session_id):
        self.memory = memory
        self.id = session_id
        self.store: dict[str, Any] = {"store": {}}

    def __setitem__(self, key, value):
        self.store["store"][key] = value

    def __getitem__(self, key):
        return self.store["store"].get(key)

    def __contains__(self, key):
        return key in self.store["store"]

    def __delitem__(self, key):
        del self.store["store"][key]

    async def load(self):
        self.store = await self.memory.get_store(self.id)

    async def clear(self):
        """Clear the session store."""
        await self.memory.clear(self.id)
        self.store = None

    async def save(self):
        """Save the session store."""
        await self.memory.save_store(
            self.id, self.store, ttl=15 * 60
        )


class SessionMiddleware(BaseHTTPMiddleware):
    """
    A FastAPI middleware for managing user sessions.
    """

    def __init__(
        self,
        app,
        secret_key,
        store,
        http_only=True,
        secure=True,
        max_age=0,
        session_cookie="sid",
        session_object="session",
        skip_session_header=None,
        logger=None,
        cookie_path="/",  # Added cookie_path parameter
    ):
        super().__init__(app)
        self.cookie_path = cookie_path  # Store cookie_path
        self.skip_session_header = skip_session_header
        self.http_only = http_only
        self.max_age = max_age
        self.secure = secure
        self.secret_key = secret_key
        self.session_cookie_name = session_cookie
        self.memory = store
        self.serializer = SignatureSerializer(self.secret_key, expired_in=self.max_age)
        self.session_object = session_object
        self.logger = logger

        if not self.logger:
            import logging

            self.logger = logging.getLogger("SessionMiddleware")
            self.logger.setLevel(logging.ERROR)

        self.logger.debug(
            f"Session Middleware initialized http_only:{http_only} secure:{secure} "
            f"session_key:'{session_object}' session_cookie_name:{session_cookie} "
            f"store:{store} cookie_path:{cookie_path}"
        )

    def create_session_cookie(self, session_id):
        """
        Create and sign a session cookie.

        Args:
            session_id (str): The session ID.

        Returns:
            SimpleCookie: The signed session cookie.
        """
        session_id_dict_obj = {self.session_cookie_name: session_id}
        signed_session_id = self.serializer.encode(session_id_dict_obj)

        cookie = SimpleCookie()
        cookie[self.session_cookie_name] = signed_session_id

        self.logger.debug(
            f"[session_id:'{session_id}'] Creating new Cookie object... cookie[{self.session_cookie_name}]"
        )

        # Set cookie path
        cookie[self.session_cookie_name]["path"] = self.cookie_path
        self.logger.debug(
            f"[session_id:'{session_id}'] cookie[{self.session_cookie_name}]['path']={self.cookie_path}"
        )

        if self.http_only:
            self.logger.debug(
                f"[session_id:'{session_id}'] cookie[{self.session_cookie_name}]['httponly'] enabled"
            )
            cookie[self.session_cookie_name]["httponly"] = True

        if self.secure:
            self.logger.debug(
                f"[session_id:'{session_id}'] cookie[{self.session_cookie_name}]['secure'] enabled"
            )
            cookie[self.session_cookie_name]["secure"] = True

        if self.max_age > 0:
            self.logger.debug(
                f"[session_id:'{session_id}'] cookie[{self.session_cookie_name}]['maxage']={self.max_age} enabled"
            )
            cookie[self.session_cookie_name]["max-age"] = self.max_age

        return cookie

    def skip_session_header_check(self, request: Request) -> bool:
        """
        Check if session management should be skipped based on the request header.

        Args:
            request (Request): The incoming request.

        Returns:
            bool: True if session management should be skipped, False otherwise.
        """
        skip_header = self.skip_session_header

        if skip_header is None:
            self.logger.debug("Do not use skip_header option.")
            return False

        if isinstance(skip_header, dict):
            skip_header = [skip_header]

        header_names = []

        for header in skip_header:
            header_name = header.get("header_name")
            header_value = header.get("header_value")
            header_names.append(header_name)

            self.logger.debug(
                f"Use skip_header option. skip_header:'{header_name}':'{header_value}'"
            )
            request_header_value = request.headers.get(header_name)
            self.logger.debug(
                f"Use skip_header option. Checking request header: '{header_name}':'{request_header_value}'"
            )
            if (
                header_value == "*" and request_header_value is not None
            ) or request_header_value == header_value:
                self.logger.debug("Use skip_header option. skip_header matched!")
                return True

        self.logger.debug(
            f"Use skip_header option. skip_headers:{header_names} not matched in request headers."
        )
        return False

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Dispatch the request, handling session management.

        Args:
            request (Request): The incoming request.
            call_next (RequestResponseEndpoint): The next request handler.

        Returns:
            Response: The response from the request handler.
        """
        if self.skip_session_header_check(request):
            self.logger.debug("Skip session management.")
            return await call_next(request)

        signed_session_id = request.cookies.get(self.session_cookie_name)
        cookie = None

        if signed_session_id is None:
            self.logger.info("Completely new access with no session cookies")
            session = self.create_session(request, cause="new")
            cookie = self.create_session_cookie(session.id)
        else:
            decoded_dict, err = self.serializer.decode(signed_session_id)

            if decoded_dict is not None:
                self.logger.debug("Cookie signature validation success")
                session_id = decoded_dict.get(self.session_cookie_name)
                has_session = await self.memory.has(session_id)

                if not has_session:
                    self.logger.info(
                        f"[session_id:'{session_id}'] Session cookie available. But no store for this sessionId found. Maybe store had cleaned."
                    )
                    session = self.create_session(
                        request, cause="valid_cookie_but_no_store"
                    )
                    cookie = self.create_session_cookie(session.id)
                else:
                    self.logger.info(
                        f"[session_id:'{session_id}'] Session cookie and Store is available! set session_mgr to request.state.{self.session_object}"
                    )

                    session = SessionIntegration(
                        memory=self.memory, session_id=session_id
                    )
                    await session.load()
                    session["__cause__"] = "success"
                    setattr(request.state, self.session_object, session)
            else:
                self.logger.info(
                    f"Session cookies available but verification failed! err:{err}"
                )
                session = self.create_session(request, cause=f"renew after {err}")
                cookie = self.create_session_cookie(session.id)

        response = await call_next(request)

        if session is not None and session.store is not None:
            await session.save()

        if cookie is not None and session.store is not None:
            cookie_val = cookie.output(header="").strip()
            self.logger.info("Set response header 'Set-Cookie' to signed cookie value")
            response.headers["Set-Cookie"] = cookie_val

        if session.store is None:
            response.delete_cookie(self.session_cookie_name)

        return response

    def create_session(self, request, cause=None) -> SessionIntegration:
        """
        Create a new session ID and its corresponding store.

        Args:
            request: The incoming request.
            cause (str): The cause of creating a new session ID.

        Returns:
            SimpleCookie: The signed session cookie.
        """
        session_id = str(uuid.uuid4())
        session = SessionIntegration(self.memory, session_id=session_id)

        self.logger.debug(
            f"[session_id:'{session_id}'(NEW)] New session_id and store for session_id created."
        )

        if cause is not None:
            session["__cause__"] = cause

        self.logger.info(
            f"[session_id:'{session_id}'(NEW)] Set session_mgr to request.state.{self.session_object} "
        )
        setattr(request.state, self.session_object, session)
        return session
