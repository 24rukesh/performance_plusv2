# Deferred Items — Phase 05 FastAPI Service

## Pre-existing Test Failure (out of scope for 05-04)

**File:** `tests/test_deploy_config.py::test_dockerfile_uses_python_3_11_slim_bookworm_in_both_stages`

**Introduced by:** Plan 05-02 (Dockerfile multi-target rewrite added a 3rd stage `api` target)

**Failure reason:** The test asserts exactly 2 occurrences of `FROM python:3.11-slim-bookworm` (builder + runtime). The new Dockerfile has 3 occurrences (builder + streamlit + api targets).

**Impact:** Non-blocking for Phase 05 functionality. All API endpoint tests pass.

**Recommended fix:** Update `test_deploy_config.py` assertion to `count >= 2` or `count == 3`, or rename the test to reflect that multiple runtime stages are intentional.

**Deferred to:** Phase 05 verification (`/gsd:verify-phase`) or a dedicated fix plan.
