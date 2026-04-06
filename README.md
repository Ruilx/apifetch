# apifetch

## HTTP API Base

- `data/apis/http_api.py` provides `HttpApi`, an abstract HTTP API base built on `requests.Session`.
- It integrates with `ApiBase` lifecycle and retry flow (`setup -> pre -> exec -> post -> parse`).
- Subclasses only need to implement `build_request()` and optionally `_parse_response()`.

## Quick Demo

The demo uses an in-memory fake session and does not require external network access.

```cmd
python -u data/apis/http_api_demo.py
```

## Run Job By Name

- Job name format: `module_path.class_name`
- `main` adds `data/` into `PYTHONPATH` via `Loader`, then loads and runs the target job.

```cmd
set "PYTHONPATH=E:\project\apifetch"
python -u src/main.py jobs.demo_job.DemoJob -- --env=dev region=cn taskA
```

```bash
export PYTHONPATH=/path/to/apifetch
python -u src/main.py jobs.demo_job.DemoJob -- --env=dev region=cn taskA
```

## Plugin Skeleton

- `src/base/plugin_base.py`: plugin lifecycle abstraction (`setup`, `teardown`, `recover`, `healthcheck`).
- `src/core/plugin_manager.py`: lazy plugin registry/loader (`register_*`, `get`, `call`, `teardown_all`).
- `src/base/job_base.py`: plugin helpers for jobs (`register_plugin_*`, `get_plugin`, `call_plugin`).

Lazy-loading behavior:

- Registering a plugin class/factory does not instantiate it when `lazy=True`.
- First `get_plugin` / `call_plugin` triggers instantiation and setup.
- `JobBase.exec()` always calls `plugins.teardown_all()` in `finally` to release resources.

### Plugin Demo

```cmd
set "PYTHONPATH=E:\project\apifetch"
python -u src/main.py jobs.plugin_demo_job.PluginDemoJob
```
