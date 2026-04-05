## Known Issues & Fixes

---  

Issue/Error: Metrics endpoint returns 500 / "psutil not available"  
File: app/routes/metrics.py  
Status: ✅ Fixed — `psutil>=5.9` added to `pyproject.toml`

---

Issue/Error: `/metrics` not reachable (blueprint not registered)
File: app/routes/__init__.py
Status: ✅ Fixed — `metrics_bp` imported and registered in `app/routes/__init__.py`

---

Issue/Error: Coverage gaps reported (app startup branches untested)
File: app/__init__.py
Status: ✅ Fixed — 97 tests now cover startup, error handlers, and redirect flow

---

Issue/Error: Untested except branch in events POST (user lookup missing)
File: app/routes/events.py
Status: ✅ Fixed — `test_create_event_user_not_found_exception` covers the `User.DoesNotExist` branch

---

Issue/Error: Grafana Error Rate panel shows 0% during high-VU load test even though k6 reports errors
File: grafana/dashboards/app.json
Status: ℹ️ Expected behavior — the error rate panel queries `flask_http_request_total`, which only records requests that reached Flask. At very high VU counts (~1150+), Nginx drops connections before they reach the app (EOF / connection reset). These failures are invisible to Flask metrics. Use k6 output or Nginx access logs to observe infrastructure-layer errors.

---
You can also refer to [failure manual](failure_manual.md) and the [runbooks folder](runbooks/)
