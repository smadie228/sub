# QA execution report — Service Checker (KAN-6)

**Date:** 2026-11-09 (Europe/Moscow)  
**Environment:** Windows NT 10.0.26300.0; Python 3.14.3  
**Baseline:** `40b3cd28b193c8397f5210131e0b709966cb1e3f` (`main` at test checkout)  
**Scope:** local copy of `smadie228/sub`, `127.0.0.1` only; no external endpoints or real Jira API requests  
**Jira:** [KAN-6](https://voldan65.atlassian.net/browse/KAN-6)

## Verified automated test runs

| Revision | Command | Actual result | Comment |
| --- | --- | --- | --- |
| Baseline `40b3cd2` | `python -B -m unittest discover -s tests -v` | **7/7 passed**, exit 0 | A Python `ResourceWarning` appeared when handling an expected HTTP 503 |
| Proposed fix in this PR | Same command | **8/8 passed**, exit 0 | Added regression test for closing the HTTPError response; the previous warning did not appear |

The three Jira reader tests use mocks, **not** live Atlassian credentials or API requests. The HTTP tests bind an ephemeral port on `127.0.0.1`.

## Manual CLI QA scenarios

The scenarios below were run by an isolated local Python harness that started the existing `DemoHandler` on an ephemeral localhost TCP port, invoked `service_check.py` in subprocesses, checked status and process exit codes, and shut down the server. The harness was temporary and is **not** part of the repository.

| ID | Test | Observed result | Status |
| --- | --- | --- | --- |
| TC-01 | GET `/health` | HTTP 200; `ok=True`; exit 0 | PASS |
| TC-02 | GET unknown `/missing` | HTTP 404; `ok=False`; exit 2 | PASS |
| TC-03 | GET `/fail`, default expectation 200 | HTTP 503; `ok=False`; exit 2 | PASS |
| TC-04 | GET `/fail`, explicitly expect 503 | HTTP 503; `ok=True`; exit 0 | PASS |
| TC-05 | URL without scheme | Argument validation error; exit 2 | PASS |
| TC-06 | Connect to running local TCP server | `OK`; exit 0 | PASS |
| TC-07 | Connect to a just-released ephemeral local TCP port | `FAIL`; exit 2 | PASS |
| TC-08 | `--json --log` GET `/health` | HTTP 200; exit 0; JSON and JSONL parsed with expected fields | PASS |
| TC-09 | HTTP expected code `999` | Validation error for code range; exit 2 | PASS |
| TC-10 | HTTP 500 | No HTTP 500 route in current demo server | NOT APPLICABLE |
| TC-11 | Simulated timeout | Demo server has no delay/timeout route | NOT APPLICABLE |

**Summary: 9/9 executed CLI scenarios passed; 2 additional scenarios are not applicable to this demonstration server.** The same 9/9 scenarios passed after the HTTPError close fix.

The JSONL test wrote its temporary log only to a temporary directory; the harness removed it afterward. This report records verified observations, but does not pretend that a raw log file was committed.

## Finding and fix

**Observation on baseline:** while testing the deliberately returned HTTP 503, Python 3.14.3 emitted `ResourceWarning: Implicitly cleaning up <HTTPError 503: 'Service Unavailable'>`. This is a resource-management warning, not a failure of the HTTP status assertion and not a production incident.

**Root cause from code review:** the `HTTPError` object was not explicitly closed. Proposed change: call `exc.close()` after reading `exc.code` in `check_http`. The new `test_http_error_closes_response` checks that the underlying stream is closed.

**Verification:** 8/8 unit tests passed, with no recurrence of that warning in the follow-up run. The 9/9 CLI scenarios still pass.

## QA conclusion

- **No functional defect was confirmed** in the nine executed CLI scenarios.
- The resource-warning issue is addressed in this pull request, **not yet merged** into `main`.
- A returned HTTP 503 is intentional on `/fail`; `--expected 503` means the measured response matched the expectation, not that the service is healthy.
- 500 and timeout coverage remain future work and must not be reported as passed.
- This local validation does not prove Linux behavior, continuous monitoring, full Jira REST integration, or production readiness.

For independent reproduction, start `python demo_app.py` and run the individual cases documented in [QA_CHECKLIST.md](QA_CHECKLIST.md), then run `python -B -m unittest discover -s tests -v`.
