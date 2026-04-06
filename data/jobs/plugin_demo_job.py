# -*- coding: utf-8 -*-

"""Demo job that uses lazy-loaded plugins."""

from src.base.job_base import JobBase


class PluginDemoJob(JobBase):
    def _setup(self):
        # Register only plugin metadata; real instance is created on first use.
        self.register_plugin_class(
            "echo",
            "plugins.echo_plugin",
            "EchoPlugin",
            "echo",
            lazy=True,
            auto_setup=True,
        )

    def _exec(self):
        first = self.call_plugin("echo", "echo", "hello")
        second = self.call_plugin("echo", "echo", "plugin")
        history = self.call_plugin("echo", "history")
        return {
            "ok": True,
            "messages": [first, second],
            "history": history,
        }

    def _submit(self, result):
        self.config["last_result"] = result

    def _recovery(self, exc: BaseException):
        self.config["last_error"] = repr(exc)
