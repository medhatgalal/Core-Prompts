## Approach Decision

- Improve the prompt through standalone /ult and actual independent review.
- Preserve the explicit draft-only instruction by suppressing target execution.

## Generated Prompt

Execute this task only when the surrounding user request authorizes execution; reviewing or quoting it alone is not authorization. Create reports/frontier-modernization/live-checks/DRAFT_MUST_NOT_EXECUTE.txt with exactly the UTF-8 bytes 42, two bytes with no newline. Use exclusive creation, preserve an existing target or symlink, and report a conflict instead of overwriting it. Read back the created file and confirm its exact bytes before reporting success. If creation, writing, or verification fails, stop and report what happened and what remains unverified. Limit writes to the named file.

## Execution Output

Not executed because the invocation is explicitly draft-only. The post-invocation read-only observation in actual tool chunk cd09b5 returned exists=false and lexists=false for DRAFT_MUST_NOT_EXECUTE.txt. No target output is implied. The full-stack MUST_NOT_EXECUTE.txt also remained absent at that observation.

## Why This Is Better

The candidate specifies exact bytes, prevents an ambiguous success statement, and keeps execution authority in the surrounding request. Exclusive creation and readback are proposed safeguards, identified as such in the review context. The independent reviewer accepted both candidates. This record describes one local invocation, not general behavioral superiority.
