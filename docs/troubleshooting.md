## Known Issues & Fixes
TODO: Sanjeev add ur own stuff

---  

Issue/Error: Metrics endpoint returns 500 / "psutil not available"  
File: app/routes/metrics.py  
Line: route handler (lines ~9-21)  
Solution: Install `psutil` (add to `pyproject.toml` and `pip install` / rebuild image) or modify the handler to degrade gracefully (catch ImportError and return placeholder metrics).  

---

Issue/Error: `/metrics` not reachable (blueprint not registered)
File: app/routes/__init__.py
Line: blueprint registration block
Solution: Import and register `metrics_bp` in `app/routes/__init__.py` (optionally guard the import if the module may be missing).

---

Issue/Error message: Coverage gaps reported (app startup branches untested)
File: app/__init__.py
Line: 40-41, 50, 54, 58, 72 (per coverage report)
Solution: Add unit tests exercising app startup, error handlers, and redirect flow; or refactor to make behavior testable.

---

Issue/Error message: Untested except branch in events POST (user lookup missing)
File: app/routes/events.py
Line: 59-60 (except `User.DoesNotExist` branch)
Solution: In tests POST `/events` include `user_id` and `monkeypatch.setattr(User, "get_by_id", staticmethod(lambda *_: (_ for _ in ()).throw(User.DoesNotExist())))` or use `monkeypatch`/`unittest.mock.patch` to raise `User.DoesNotExist`, then assert 404 response.

---
