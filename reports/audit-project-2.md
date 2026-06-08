================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy (Frankenstein LMS)
Stack:   Node.js + Express ^4.18.2 + sqlite3 ^5.1.6
Files:   3 analyzed | ~155 lines of code
Date:    2026-06-08

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded secrets/credentials
File: src/utils.js:1-6
Description: The config object hardcodes production credentials directly in source
             code: dbPass "senha_super_secreta_prod_123", paymentGatewayKey
             "pk_live_1234567890abcdef", and smtpUser. These values are committed
             to the repository.
Impact: Any repository leak exposes production credentials, payment gateway keys,
        and SMTP credentials. Attackers can make fraudulent payments or access
        production infrastructure.
Recommendation: Move all secrets to process.env. Create config/settings.js reading
             from environment variables with empty/safe defaults. Add .env.example
             documenting the required variables (P2 from playbook).

### [CRITICAL] Credit card number and payment gateway key logged to console
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`
             logs the full card number (PAN) and the live payment gateway key on
             every checkout call.
Impact: Violates PCI-DSS. Card numbers and live API keys are written to stdout/logs,
        which may be stored, indexed, or accessed by log aggregation systems. Direct
        data breach vector.
Recommendation: Remove this log entirely. Never log card numbers or gateway keys.
             Log only a masked representation (e.g., last 4 digits) at debug level
             if needed (P2, P12 from playbook).

### [CRITICAL] God Class — AppManager handles DB init, routing, payment, and business logic
File: src/AppManager.js:1-141
Description: AppManager is a single class that performs: database initialization
             and schema creation (initDb), HTTP route registration (setupRoutes),
             payment processing logic (cc.startsWith("4")), user creation, enrollment,
             audit logging, and financial report generation. All concerns in one file.
Impact: Impossible to test any concern in isolation. Any change risks breaking
        unrelated functionality. Violates SRP completely.
Recommendation: Break into MVC layers — models for DB access, services for payment
             logic, controllers for orchestration, routes for HTTP binding (P3 from playbook).

### [HIGH] Insecure homemade password hashing (badCrypto)
File: src/utils.js:17-23
Description: The badCrypto function hashes passwords by iterating 10,000 times
             concatenating base64 substrings and truncating to 10 characters. This
             produces a deterministic, saltless, effectively constant output of
             "c2VuaGFjMm Vua" for any input, making it trivially reversible.
Impact: All passwords in the database can be reversed or brute-forced trivially.
        A database leak exposes all user passwords.
Recommendation: Replace with Node's built-in crypto.scryptSync(pwd, salt, 64)
             using a random salt stored as "salt:hash". No new npm dependency required
             (P4 from playbook).

### [HIGH] Callback hell / pyramid of doom in checkout (no transaction)
File: src/AppManager.js:37-78
Description: The checkout handler nests 4 levels of callbacks:
             courses.get → users.get → users.run (create) → enrollments.run →
             payments.run → audit.run. The multi-step writes (enrollment → payment →
             audit_log) have no database transaction. A failure at step 2 or 3 leaves
             partial data written.
Impact: Ilegible code and race-condition prone. A payment insert failure after a
        successful enrollment insert leaves an orphaned enrollment with no payment
        record — corrupted data state.
Recommendation: Promisify db calls and use async/await with BEGIN/COMMIT/ROLLBACK
             wrapping all three inserts as a single atomic operation (P10 from playbook).

### [HIGH] Global mutable state (globalCache, totalRevenue)
File: src/utils.js:9-10
Description: globalCache and totalRevenue are module-level mutable variables exported
             and modified at runtime. globalCache is written in every checkout via
             logAndCache. totalRevenue is exported but never updated, suggesting dead
             code left from an incomplete feature.
Impact: Module-level state persists across requests; causes race conditions under
        concurrent load; makes the module untestable in isolation; totalRevenue is
        stale dead code.
Recommendation: Encapsulate cache state in a CacheService class instance injected
             where needed. Remove or properly implement totalRevenue (P11 from playbook).

### [HIGH] Deprecated sqlite3 callback API throughout
File: src/AppManager.js:37, 50, 54, 57, 83, 92, 104, 106, 133
Description: All database access uses the sqlite3 callback API (db.get, db.run,
             db.all with callbacks). This API is the source of the callback hell
             anti-pattern and makes async coordination error-prone. sqlite3.verbose()
             is also used in production (AppManager.js:1).
Impact: Outdated API that prevents clean async/await usage; verbose() adds
        unnecessary overhead and debug output in production.
Recommendation: Wrap db methods with promisify or implement Promise-based helpers
             (run/get/all returning Promises). Remove verbose() from production code
             (deprecated API section from reference 02).

### [MEDIUM] N+1 queries in financial-report + manual counter coordination
File: src/AppManager.js:80-129
Description: The financial report fetches all courses, then for each course fetches
             enrollments, and for each enrollment makes TWO separate queries (user +
             payment). For N courses with M enrollments each, this results in
             1 + N + 2*N*M database calls. Manual counters (coursesPending, enrPending)
             coordinate the async callbacks — a race-condition-prone pattern.
Impact: Performance degrades quadratically with data volume. The counter coordination
        is fragile and can produce double responses or hang if any callback errors.
Recommendation: Replace with a single JOIN query across enrollments, users, and
             payments. Use async/await to eliminate counter coordination (P7, P10).

### [MEDIUM] DELETE /users/:id leaves orphaned enrollments and payments
File: src/AppManager.js:131-137
Description: The DELETE handler removes only the user record. Enrollments and payments
             referencing that user_id remain in the database. The response message
             even admits this: "as matrículas e pagamentos ficaram sujos no banco."
             No referential integrity or cascade delete is configured.
Impact: Orphaned enrollment and payment records cause data integrity issues.
        Financial reports may show incorrect revenue for deleted users.
Recommendation: Delete dependent enrollments and payments in the same transaction
             before deleting the user, or enable FOREIGN KEY ... ON DELETE CASCADE (P10).

### [MEDIUM] No transaction on checkout multi-step writes
File: src/AppManager.js:50-63
Description: The three INSERT operations (enrollments, payments, audit_logs) inside
             checkout are executed sequentially without a database transaction. Each
             runs independently.
Impact: If payments INSERT fails after enrollments INSERT succeeds, the student has
        an enrollment record but no payment — inconsistent state that is hard to detect
        and recover from.
Recommendation: Wrap all three INSERTs in BEGIN/COMMIT/ROLLBACK (P10 from playbook).

### [MEDIUM] In-memory SQLite with fake payment validation
File: src/AppManager.js:7, 46
Description: The database uses ':memory:' — all data is lost on every server restart.
             Payment validation is fake: any card starting with "4" is approved,
             regardless of any real gateway integration.
Impact: Not suitable for production. Data loss on every restart. Payment logic
        provides false security assurance.
Recommendation: Use a file-backed SQLite path from config for persistence. Document
             the fake payment validation clearly. Integrate a real payment gateway
             behind the paymentService abstraction.

### [LOW] Cryptic variable names throughout checkout
File: src/AppManager.js:29-34
Description: Request body fields and local variables use single-letter or abbreviated
             names: u (name), e (email), p (password), cid (course_id), cc (card).
             Body fields are also cryptic: usr, eml, pwd, c_id, card.
Impact: Reduces readability and makes the code harder to onboard new developers.
        Inconsistent naming (some abbreviated, some not) adds cognitive overhead.
Recommendation: Use descriptive names internally (name, email, password, courseId,
             cardNumber). Keep body field names for backward compatibility in the
             controller's input parsing layer (P12 from playbook).

### [LOW] Inconsistent response format (strings vs JSON)
File: src/AppManager.js:38, 41, 48, 51, 55, 84, 135
Description: Most error responses use res.send("string") while the success checkout
             response uses res.json({...}). The DELETE response uses res.send() for
             both success and error messages.
Impact: API consumers must handle two different response content types. Makes
        client-side error handling inconsistent.
Recommendation: Standardize all responses to JSON format. Use a centralized error
             handler middleware to ensure consistent error response shapes (P9).

### [LOW] console.log used for application logging
File: src/utils.js:13, src/AppManager.js:45, src/app.js:13
Description: Application logging uses console.log without levels (info/warn/error)
             or structured output. The logAndCache function prints to stdout on every
             checkout.
Impact: No way to filter by severity; logs mix debug noise with important events;
        no structured output for log aggregation.
Recommendation: Replace with a logger that supports levels. At minimum, remove
             the cache-hit log from the hot checkout path (P12 from playbook).

================================
Total: 14 findings
================================
