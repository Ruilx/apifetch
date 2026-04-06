# -*- coding: utf-8 -*-

"""HTTP API base component built on top of ApiBase + requests.Session."""

import abc
from typing import Any, Callable, Mapping

import requests
from requests import Response, Session
from requests.exceptions import HTTPError, RequestException, Timeout

from src.base.api_base import ApiBase, RetryPolicy


class HttpApi(ApiBase, metaclass=abc.ABCMeta):
    """Reusable HTTP API abstraction with session management and retry integration."""

    RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}

    def __init__(
        self,
        arguments: list[str],
        retry_policy: RetryPolicy | None = None,
        base_url: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        timeout_seconds: float = 10.0,
        verify_ssl: bool = True,
        auto_raise_for_status: bool = True,
        session_factory: Callable[[], Session] | None = None,
    ):
        super().__init__(arguments=arguments, retry_policy=retry_policy)
        self.base_url = (base_url or "").rstrip("/")
        self.default_headers = dict(default_headers or {})
        self.timeout_seconds = timeout_seconds
        self.verify_ssl = verify_ssl
        self.auto_raise_for_status = auto_raise_for_status
        self._session_factory = session_factory or requests.Session
        self._session: Session | None = None

    def setup(self):
        if self._session is None:
            self._session = self._session_factory()
            self._session.headers.update(self.default_headers)

    def _pri_exec(self):
        self.setup()

    def _post_exec(self):
        # Keep session alive for connection pooling between calls.
        return None

    @abc.abstractmethod
    def build_request(self) -> dict[str, Any]:
        """Return request options, e.g. {'method': 'GET', 'url': '/health', 'params': {...}}."""

    def _exec(self):
        options = dict(self.build_request())
        method = str(options.pop("method", "GET")).upper()
        path_or_url = options.pop("url", options.pop("path", None))
        if not path_or_url:
            raise ValueError("build_request must provide 'url' (or 'path').")

        return self.fetch(method=method, url=str(path_or_url), **options)

    def fetch(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        data: Any | None = None,
        json: Any | None = None,
        timeout: float | None = None,
        allow_redirects: bool = True,
        raise_for_status: bool | None = None,
        **kwargs,
    ) -> Response:
        session = self._ensure_session()
        merged_headers = dict(self.default_headers)
        if headers:
            merged_headers.update(headers)

        response = session.request(
            method=method,
            url=self._build_url(url),
            headers=merged_headers or None,
            params=params,
            data=data,
            json=json,
            timeout=self.timeout_seconds if timeout is None else timeout,
            verify=self.verify_ssl,
            allow_redirects=allow_redirects,
            **kwargs,
        )

        should_raise = self.auto_raise_for_status if raise_for_status is None else raise_for_status
        if should_raise:
            response.raise_for_status()
        return response

    def _recover(self, exc: BaseException):
        # Recreate session to recover from stale/broken connection state.
        self._close_session()
        self.setup()

    def _is_retryable(self, exc: BaseException) -> bool:
        if isinstance(exc, (Timeout, requests.ConnectionError)):
            return True
        if isinstance(exc, HTTPError):
            response = exc.response
            if response is None:
                return True
            return response.status_code in self.RETRYABLE_STATUS_CODES
        if isinstance(exc, RequestException):
            return True
        return False

    def close(self):
        self._close_session()

    def _close_session(self):
        if self._session is not None:
            self._session.close()
            self._session = None

    def _ensure_session(self) -> Session:
        self.setup()
        assert self._session is not None
        return self._session

    def _build_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if not self.base_url:
            return path_or_url
        if path_or_url.startswith("/"):
            return f"{self.base_url}{path_or_url}"
        return f"{self.base_url}/{path_or_url}"
