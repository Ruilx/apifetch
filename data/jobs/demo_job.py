# -*- coding: utf-8 -*-

"""Small demo job for main entry flow validation."""

from src.base.job_base import JobBase


class DemoJob(JobBase):
    def _setup(self):
        self.config["setup"] = True

    def _exec(self):
        options = self.arguments.get("options", {})
        positional = self.arguments.get("positional", [])
        return {
            "ok": True,
            "setup": self.config.get("setup", False),
            "options": options,
            "positional": positional,
        }

    def _submit(self, result):
        self.config["last_result"] = result

    def _recovery(self, exc: BaseException):
        self.config["last_error"] = repr(exc)
