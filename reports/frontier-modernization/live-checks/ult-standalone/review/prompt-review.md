# Standalone ULT prompt review

Disposition: PASS FOR FINALIZATION for both candidates. No blocking prompt defect found.

This review began after accepting final assembly. It independently compares the supplied originals and candidates against input.md and the actual emitted /ult contract. It does not execute either target.

## Findings

| Criterion | Positive candidate | Draft-only candidate |
| --- | --- | --- |
| Target preserved | Exact reports/frontier-modernization/live-checks/ALLOWED_EXECUTION.txt path retained. | Exact reports/frontier-modernization/live-checks/DRAFT_MUST_NOT_EXECUTE.txt path retained. |
| Byte precision | Explicitly requests two UTF-8 bytes 42, with no newline. This matches the positive invocation. | Preserves the text 42 and explicitly fixes the intended encoding, length, and newline handling. The supplied draft-only request is not converted into execution authority. |
| Material improvement | Exact readback before success, explicit failure reporting, exclusive creation, and a one-file write boundary remove ambiguities in the short original. | The same improvements make the reusable task more precise while retaining the surrounding-request authorization condition. |
| Current authority | The current invocation explicitly says improve and execute. The candidate's authority condition is satisfied after this independent review; no permission reask is needed. | The current invocation explicitly says draft-only and forbids executing its target. Its surrounding context therefore fails the candidate's execution condition. Execution must remain suppressed. |
| Safeguard provenance | input.md identifies exclusive creation and readback as proposed safeguards. They are reasonable additions, not falsely attributed original user demands. | Same provenance. The reusable candidate does not independently grant authority or override the explicit draft-only instruction. |
| Evidence and reporting | Success may be reported only after actual creation and exact-byte readback. The reviewer has performed neither. | The later Execution Output must explain draft-only suppression, with no invented task result. |

The substantive delta is improved precision and failure handling, not a measured percentage or demonstrated performance gain. The positive candidate is d3eb99bac3b2ec1745fccfa7b8bc7b33a01f860020543519919389759adf8726; the draft candidate is ac48d13ddc04c7f90e061f28f711078bc4ea90497b2c19260243c5836d0f26b0.

## Remaining controller evidence

The supplied files are copy-ready prompt candidates, not complete ULT response or execution artifacts. Their absence of wrapper sections is therefore not a candidate defect. Final response compliance remains unverified: retain Approach Decision, Generated Prompt, Execution Output, and Why This Is Better; display each finalized prompt before its execution output. For the positive case, briefly announce execution and then perform the already-authorized task. For the draft case, state why execution is suppressed and leave the target untouched.

This disposition accepts prompt text for finalization. It does not establish positive target bytes, draft-target absence, actual prompt-before-execution timing, path/readback identity, race behavior, or any other runtime outcome. Those are the controller's remaining bounded acceptance responsibilities.

