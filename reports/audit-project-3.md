================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   10 analyzed | ~1149 lines of code
Date:    2026-06-08

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded SECRET_KEY
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` is a literal string baked into source code.
Impact: Any repository leak (public GitHub, logs, CI artifacts) exposes the signing secret, allowing attackers to forge session cookies or tokens.
Recommendation: Move to `config/settings.py` and read from `os.environ.get("SECRET_KEY", "dev-only-insecure")`. Add to `.env.example` (see P2 playbook).

### [CRITICAL] Insecure Password Hashing — MD5
File: models/user.py:29, models/user.py:32
Description: `set_password` stores `hashlib.md5(pwd.encode()).hexdigest()` and `check_password` compares against the same MD5 digest. MD5 is cryptographically broken and has no salt.
Impact: A database dump instantly exposes all passwords via rainbow-table or brute-force attack in seconds.
Recommendation: Replace with `werkzeug.security.generate_password_hash(pwd, method="pbkdf2:sha256")` and `check_password_hash` (P4 playbook). Re-seed the database with new hashes.

### [CRITICAL] Password Hash Exposed in API Responses
File: models/user.py:21-25 (User.to_dict); user_routes.py:33-34 (/users/<id>), user_routes.py:85-86 (POST /users), user_routes.py:208-210 (/login)
Description: `User.to_dict()` includes the `'password'` key, and this dict is returned directly by `GET /users/<id>`, `POST /users`, and `POST /login`.
Impact: Every API client receives the password hash (or, under current MD5, a crackable digest), leaking credential data to all callers.
Recommendation: Remove `'password'` from `User.to_dict()`. Never serialize password fields to HTTP responses (AP-06 / P4 playbook).

### [HIGH] Hardcoded SMTP Credentials
File: services/notification_service.py:9-10
Description: `self.email_user = 'taskmanager@gmail.com'` and `self.email_password = 'senha123'` are literal strings inside the class constructor.
Impact: Credentials versioned in source code leak with any repository exposure, allowing unauthorized use of the email account.
Recommendation: Read from environment via `config/settings.py`: `SMTP_USER = os.environ.get("SMTP_USER", "")` and `SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")` (P2 playbook).

### [HIGH] Business Logic in Route Handlers (Fat Routes / No Controller Layer)
File: routes/task_routes.py:11-299, routes/user_routes.py:10-211, routes/report_routes.py:12-223
Description: All querying, validation, aggregation, serialization, and overdue computation is embedded directly inside route functions. There is no controller or service layer to own this logic. `report_routes.py` (~223 lines) performs summary aggregation, per-user loops, and overdue listing entirely inline.
Impact: Impossible to unit-test business logic in isolation; any change to a route risks breaking multiple concerns simultaneously; logic cannot be reused across endpoints.
Recommendation: Create `controllers/` (task_controller.py, user_controller.py, report_controller.py, category_controller.py) that own all business logic. Routes become thin: parse request → call controller → jsonify result (P3 + P6 playbook).

### [HIGH] Fake / Insecure Authentication Token
File: user_routes.py:210
Description: Login endpoint returns `'token': 'fake-jwt-token-' + str(user.id)` — a predictable, unverified string that provides no actual security.
Impact: Any client can fabricate a "token" for any user ID. This token is accepted nowhere currently but signals the auth layer is not implemented, creating a false sense of security.
Recommendation: Implement real JWT (e.g., `flask-jwt-extended`) or clearly mark as a stub pending implementation. Do not ship a predictable fake token.

### [MEDIUM] N+1 Queries
File: routes/task_routes.py:41-57, routes/report_routes.py:53-68
Description: `get_tasks()` loops over every task and issues `User.query.get(t.user_id)` and `Category.query.get(t.category_id)` per iteration. `summary_report()` loops over all users and issues `Task.query.filter_by(user_id=u.id).all()` per user — O(N) queries for N users.
Impact: With 100 tasks / 50 users, a single GET /tasks or GET /reports/summary issues 200–150 extra queries. Response time degrades linearly with data volume.
Recommendation: Use SQLAlchemy eager loading: `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`. For report aggregation, use a single SQL GROUP BY query (P7 playbook).

### [MEDIUM] Duplicated Overdue Logic (DRY Violation)
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-43, routes/report_routes.py:132-135
Description: The `if t.due_date: if t.due_date < datetime.utcnow(): if t.status not in ('done','cancelled')` block is copy-pasted in at least 6 places instead of calling the existing `Task.is_overdue()` method.
Impact: Any change to overdue semantics (e.g., time zone, grace period) must be applied in 6 places; divergence has already occurred (some places set `task_data['overdue']`, others just count).
Recommendation: Replace all copies with `t.is_overdue()`. Remove duplicate code (P12 / AP-15 playbook).

### [MEDIUM] Bare `except:` Swallowing All Errors
File: routes/task_routes.py:62, routes/task_routes.py:138, routes/task_routes.py:236, routes/user_routes.py:130, routes/user_routes.py:149, routes/report_routes.py:188, routes/report_routes.py:207, routes/report_routes.py:221, utils/helpers.py:47-48
Description: Multiple `except:` (no exception type) or `except Exception` blocks silently return a generic 500 without logging the original error. `utils/helpers.py:47-48` has a double bare `except` in `parse_date`.
Impact: Masks real bugs — a typo or logic error returns "Erro interno" with no traceable cause; crashes are invisible in production logs.
Recommendation: Create `middlewares/error_handler.py` with a global Flask error handler. Remove per-handler try/except; let errors propagate and be caught centrally with proper logging (P9 playbook).

### [MEDIUM] db.create_all() at Module Import Time
File: app.py:30-31
Description: `with app.app_context(): db.create_all()` runs at module import level (outside `if __name__ == '__main__'` and outside a factory function).
Impact: Any test or tool that imports `app` triggers schema creation against the database immediately; prevents proper use of application factory pattern; complicates testing with isolated DBs.
Recommendation: Move `db.create_all()` inside a `create_app()` factory function or restrict to the `if __name__ == '__main__'` block. Consider Alembic for migrations (AP deprecated table).

### [LOW] Unused Imports
File: app.py:7 (os, sys, json, datetime — only datetime is used), routes/task_routes.py:7 (json, os, sys, time — none used), utils/helpers.py:3-7 (os, json, sys, math, hashlib — none used in public interface)
Description: Multiple files import standard-library modules that are never referenced in the file's code.
Impact: Cognitive noise; misleads readers about what the module depends on; slight import overhead.
Recommendation: Remove all unused imports (P12 / AP-19 playbook).

### [LOW] Magic Boolean Returns (`if x: return True else: return False`)
File: models/task.py:38-43 (validate_status), models/task.py:45-48 (validate_priority), models/task.py:50-60 (is_overdue), models/user.py:34-38 (is_admin), utils/helpers.py:21-23 (validate_email), utils/helpers.py:52-54 (is_valid_color)
Description: Multiple methods use verbose `if cond: return True else: return False` patterns instead of `return cond`. `is_overdue` has a 10-line chain of nested if/else that reduces to a single expression.
Impact: Readability noise; higher chance of introducing logic bugs when modifying the condition.
Recommendation: Replace with `return <boolean expression>` (P12 / AP-19 playbook).

### [LOW] Deprecated `datetime.utcnow()` (Python 3.12+)
File: models/user.py:14, models/task.py:15-16, models/category.py:11, routes/task_routes.py:31, routes/task_routes.py:72, routes/task_routes.py:215, routes/task_routes.py:285, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:71, services/notification_service.py:36, utils/helpers.py:38, seed.py:66-76
Description: `datetime.utcnow()` is deprecated since Python 3.12 and emits `DeprecationWarning`. It returns a naive datetime with no timezone info.
Impact: Will break in future Python versions; naive datetimes cause ambiguous comparisons across DST boundaries.
Recommendation: Replace with `datetime.now(timezone.utc)` (or `datetime.now(datetime.UTC)` on 3.11+) where feasible. For SQLAlchemy `default=`, use `lambda: datetime.now(timezone.utc)` (AP deprecated table).

================================
Total: 13 findings
================================
