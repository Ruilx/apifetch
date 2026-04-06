# -*- coding:utf-8 -*-
import abc
import dataclasses
import random
import time
from typing import Any


@dataclasses.dataclass(frozen=True)
class RetryPolicy:
    """Generic retry policy for all API types (file/network/etc.)."""

    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    jitter_seconds: float = 0.0
    retry_window_seconds: float | None = None

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds must be >= 0")
        if self.max_delay_seconds < 0:
            raise ValueError("max_delay_seconds must be >= 0")
        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier must be >= 1")
        if self.jitter_seconds < 0:
            raise ValueError("jitter_seconds must be >= 0")
        if self.retry_window_seconds is not None and self.retry_window_seconds < 0:
            raise ValueError("retry_window_seconds must be >= 0")


class ApiBase(metaclass=abc.ABCMeta):
    def __init__(self, arguments: list[str], retry_policy: RetryPolicy | None = None):
        self.arguments = arguments
        self.retry_policy = retry_policy or RetryPolicy()

    @abc.abstractmethod
    def setup(self):
        """Create and initialize all required resources."""
        ...

    def _pri_exec(self):
        """Pre-processing before the main API call."""
        ...

    def _parse_response(self, raw_response: Any):
        """Parse/transform data returned by _exec."""
        return raw_response

    def _post_exec(self):
        """Post-processing, usually cleanup or connection teardown."""
        ...

    @abc.abstractmethod
    def _exec(self):
        """Main API execution process (file IO/network IO/etc.)."""
        ...

    def _recover(self, exc: BaseException):
        """Recovery hook called after a failed attempt."""
        ...

    def _is_retryable(self, exc: BaseException) -> bool:
        """Whether the given exception is retryable."""
        return True

    def _next_wait_seconds(self, attempt_index: int) -> float:
        """Compute exponential backoff wait with optional jitter."""
        policy = self.retry_policy
        delay = min(
            policy.initial_delay_seconds * (policy.backoff_multiplier ** attempt_index),
            policy.max_delay_seconds,
        )
        if policy.jitter_seconds > 0:
            delay += random.uniform(0.0, policy.jitter_seconds)
        return max(0.0, delay)

    def _can_retry_by_time_window(self, started_at: float, wait_seconds: float) -> bool:
        window = self.retry_policy.retry_window_seconds
        if window is None:
            return True
        return (time.monotonic() - started_at + wait_seconds) <= window

    def _before_retry(self, exc: BaseException, next_wait_seconds: float, next_attempt_no: int):
        """Optional hook before sleeping and entering next retry attempt."""
        ...

    def exec(self):
        self.setup()

        attempts = self.retry_policy.max_attempts
        started_at = time.monotonic()
        last_exception: BaseException | None = None

        for attempt in range(attempts):
            try:
                self._pri_exec()
                raw_response = self._exec()
                self._post_exec()
                return self._parse_response(raw_response)
            except Exception as exc:  # noqa: BLE001
                last_exception = exc
                self._recover(exc)

                if not self._is_retryable(exc):
                    raise

                is_last_attempt = attempt >= attempts - 1
                if is_last_attempt:
                    raise

                wait_seconds = self._next_wait_seconds(attempt)
                if not self._can_retry_by_time_window(started_at, wait_seconds):
                    raise

                self._before_retry(exc, wait_seconds, attempt + 2)
                time.sleep(wait_seconds)

        if last_exception is not None:
            raise last_exception

        raise RuntimeError("Unreachable API execution state")
