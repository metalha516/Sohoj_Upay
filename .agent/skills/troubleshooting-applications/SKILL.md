---
name: troubleshooting-applications
description: >-
  Troubleshoots application bugs, crashes, test failures, race conditions, and
  production issues while enforcing resilient error-handling patterns across
  languages. Use when debugging errors, fixing bugs, investigating unexpected
  behavior, implementing error handling, designing fault-tolerant APIs, or
  improving application reliability.
---

# Troubleshooting & Error Handling

Diagnose and fix any application issue systematically by finding the true root
cause first, then applying resilient error-handling and defense-in-depth
patterns so the failure cannot recur.

## The Iron Law of Troubleshooting

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.
```

Symptom fixes are failures. If you have not completed Phase 1, do not propose or
apply a code fix.

## When to Use This Skill

- Debugging any bug, crash, stack trace, build failure, or test failure
- Investigating flaky tests, race conditions, memory leaks, or performance drops
- Implementing error handling in new features or APIs
- Designing retry, timeout, fallback, and circuit-breaker strategies
- Handling async/concurrent errors and unhandled rejections
- Replacing vague or swallowed errors with structured, actionable diagnostics

---

## Troubleshooting Workflow Checklist

Copy and update this checklist to track state when troubleshooting:

- [ ] **Phase 1: Root Cause Investigation** — Read full error/stack trace, reproduce consistently, check recent diffs (`git diff` / `git log -n 5`), trace data flow backward to source
- [ ] **Phase 2: Pattern & Error Category Analysis** — Classify error (recoverable vs. unrecoverable), compare against working code
- [ ] **Phase 3: Hypothesis & Minimal Test** — State a single hypothesis ("X fails because Y") and verify with minimal diagnostic check
- [ ] **Phase 4: TDD Fix & Defense-in-Depth** — Write failing reproduction test → implement root-cause fix + proper error handling → verify full suite passes

---

## The Four Troubleshooting Phases

### Phase 1: Root Cause Investigation

1. **Read Error Messages & Stack Traces Completely**
   - Note exact file paths, line numbers, error codes, and cause chains.
   - Never guess from a summary when the full trace is available.
2. **Reproduce Consistently**
   - Identify the exact command, request payload, or state that triggers the issue.
   - If intermittent/flaky, check for timing guesses (`sleep`/`setTimeout`) and use condition-based polling (see [`resources/defense-in-depth.md`](resources/defense-in-depth.md)).
3. **Check Recent Changes**
   - Run `git status` and `git diff` / `git log -n 5` to spot recent code, dependency, or config changes.
4. **Instrument Component Boundaries (Multi-Layer Systems)**
   - When failures cross boundaries (UI → API → Service → DB, or CI → Build → Runtime), log input, output, and environment state at each boundary before guessing.
5. **Trace Backward to the Original Trigger**
   - Do not patch where the crash surfaces if bad data originated higher up the call chain.
   - Follow [`resources/root-cause-tracing.md`](resources/root-cause-tracing.md) to trace bad values back to their source.

### Phase 2: Pattern & Error Category Analysis

#### 1. Error Handling Philosophies

| Approach | Mechanism | Best Used For |
|:---------|:----------|:--------------|
| **Exceptions** | `try / catch / finally`, disrupts control flow | Unexpected errors, infrastructure failures, exceptional conditions |
| **Result Types** | `Result<T, E>`, `Either`, explicit return | Expected domain errors, validation failures, recoverable branches |
| **Option / Maybe** | `Option<T>`, `T \| null` | Nullable lookups where absence is not an error |
| **Panics / Crashes** | Fail-fast termination | Unrecoverable state corruption, invariant violations, programming bugs |

#### 2. Error Categories

- **Recoverable Errors** *(Handle gracefully, retry, or return structured error)*:
  - Network timeouts, transient 502/503/504 responses
  - Missing optional files or cache misses
  - Invalid user input / schema validation failures
  - Third-party API rate limits (`429 Too Many Requests`)
- **Unrecoverable Errors** *(Fail fast, log full context, alert/restart)*:
  - Out of memory (`OOM`) or disk full
  - Stack overflow
  - Programming bugs (`NullPointerException`, `TypeError`, broken invariants)
  - Missing required startup configuration or secrets

### Phase 3: Hypothesis and Testing

1. **Form a Single Hypothesis:** Write down *"I think `[root cause]` happens because `[mechanism]` at `[file:line]`."*
2. **Test Minimally:** Change or instrument one variable at a time. Never bundle multiple speculative fixes.
3. **Evaluate:**
   - Confirmed → Proceed to Phase 4.
   - Refuted → Revert the speculative change and form a new hypothesis from the new evidence.

### Phase 4: Implementation, Error Handling & Verification

1. **Write a Failing Test First:** Reproduce the bug in an automated test (or minimal reproduction script) and watch it fail for the expected reason.
2. **Fix at the Source & Add Defense-in-Depth:**
   - Fix the root cause where bad state originates.
   - Add multi-layer validation (Entry Point → Business Logic → Environment Guards → Debug Telemetry). See [`resources/defense-in-depth.md`](resources/defense-in-depth.md).
3. **Verify Fresh Evidence:**
   - Run the reproduction test and confirm it passes.
   - Run the broader test suite/build to prove zero regressions.
4. **The 3-Strike Architecture Rule:**
   - If **3 consecutive fix attempts fail** or each fix exposes a new bug elsewhere, **STOP**. Do not attempt Fix #4 blindly—question the underlying architecture with the user.

---

## Error Handling Best Practices

1. **Fail Fast:** Validate inputs at system boundaries immediately.
2. **Preserve Context:** Wrap errors with `from e` (Python), `cause` (JS/TS), or `%w` (Go) so original stack traces and metadata survive.
3. **Meaningful Messages:** State *what* failed, *why*, and *how to fix it* (include relevant IDs, never raw secrets).
4. **Log Once at the Handling Boundary:** Avoid log-and-rethrow duplication; log with structured fields at the boundary that handles or translates the error.
5. **Handle at the Right Level:** Catch errors only where you have enough context to recover, retry, or translate them for the caller.
6. **Clean Up Resources:** Always use `with` (Python), `using` / `try-finally` (TS/C#/Java), or `defer` (Go) for files, locks, and connections.
7. **Never Swallow Errors:** Empty `catch` blocks hide root causes. Either handle, re-raise with context, or explicitly document why ignoring is safe.
8. **Type-Safe Domain Errors:** Define custom error hierarchies with machine-readable error codes.

```python
# Good error handling example
def process_order(order_id: str) -> Order:
    """Process order with comprehensive error handling."""
    try:
        # 1. Fail fast: validate input at boundary
        if not order_id:
            raise ValidationError("Order ID is required")

        # 2. Fetch domain entity
        order = db.get_order(order_id)
        if not order:
            raise NotFoundError("Order", order_id)

        # 3. Isolate & wrap external service calls with context
        try:
            payment_result = payment_service.charge(order.total)
        except PaymentServiceError as e:
            logger.error(f"Payment failed for order {order_id}: {e}")
            raise ExternalServiceError(
                "Payment processing failed",
                service="payment_service",
                details={"order_id": order_id, "amount": order.total}
            ) from e

        # 4. Persist state transition
        order.status = "completed"
        order.payment_id = payment_result.id
        db.save(order)

        return order

    except ApplicationError:
        # Re-raise known domain/application errors untouched
        raise
    except Exception as e:
        # Catch-all at top boundary: log full traceback & wrap as internal error
        logger.exception(f"Unexpected error processing order {order_id}")
        raise ApplicationError(
            "Order processing failed",
            code="INTERNAL_ERROR"
        ) from e
```

---

## Common Pitfalls & Red Flags

| Pitfall / Excuse | Reality & Fix |
|:-----------------|:--------------|
| **Catching Too Broadly** (`except Exception:` deep in logic) | Masks programming bugs and `KeyboardInterrupt`. Catch specific error types. |
| **Empty Catch Blocks** (`catch (e) {}`) | Silently corrupts state. Log, fallback explicitly, or re-throw. |
| **Log-and-Rethrow Everywhere** | Spams logs with 5 copies of the same failure. Wrap and re-throw down the stack; log once at the top handler. |
| **Ignoring Async Errors** | Unhandled promise rejections or background task exceptions crash or hang apps. Always `await` or attach `.catch()`. |
| **"Let me just try changing X real quick"** | Guessing wastes time and introduces new bugs. Complete Phase 1 first. |
| **"Tests should pass now"** | "Should" is not evidence. Run the verification command and read the output. |

---

## Resources & Detailed References

Consult these files when you need language-specific implementations or advanced diagnostic techniques:

- **[`resources/error-handling-details.md`](resources/error-handling-details.md)** — Worked examples across Python, TypeScript/JavaScript, Rust, and Go, plus Retry with Exponential Backoff, Circuit Breaker, and Async Error Aggregation patterns.
- **[`resources/root-cause-tracing.md`](resources/root-cause-tracing.md)** — Step-by-step backward call-stack tracing and boundary instrumentation when errors surface deep in execution.
- **[`resources/defense-in-depth.md`](resources/defense-in-depth.md)** — 4-layer validation architecture and condition-based waiting patterns to eliminate flaky async tests.
- **[`scripts/find-polluter.sh`](scripts/find-polluter.sh)** — Bisection utility for isolating which test or file is polluting shared state. Run `bash scripts/find-polluter.sh --help` (or read its header) before use.
