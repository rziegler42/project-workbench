# A bridge to a server reports the statuses 500, 502 and 503 as retryable

Status: Accepted by Robert Ziegler <25854477+rziegler42@users.noreply.github.com> on 2026-11-02
Date: 2026-11-02

## Context

Every server status outside 200 to 299 that no special row names is `vendor_error` with the detail `bad_exit` and `retryable` false
in the Ollama bridge (`docs/specs/ask-ollama.md`, "Errors" and "`embed`"; `models` has the same row). The contract says why that is
the default: `retryable` is "whether the same call might succeed later", it is `true` for `timeout`, `usage_limit` and a server
that did not answer, and `false` "for the other classes and codes defined here" (`docs/specs/model-bridge.md`, "The failure object").
`bad_exit` is one of those codes, defined for a program that "exited non-zero and its text matches no other class".

A status 500, 502 or 503 from a server is a different case from a program's exit code. The knowledge-base module, an external module
that calls the bridge by capability, reported (relayed by the owner on 2026-11-02) that on a server with one 12 GB card an embedding
call right after a chat call failed once with a 500, and that retrying recovered every time. Today the bridge labels that failure
not retryable, so a caller that obeys the label gives up on a failure that a wait would have cleared. The owner's direction of
2026-11-02: limit the change to the transient statuses 500, 502 and 503, keep 501 as the "cannot embed" row, and say whether it
applies to `ask` as well as `embed` and what it means for `ask-codex`.

Who reads the field, read on 2026-11-02 at commit `b5e38878a0f6ce16a7a38f40bf778c7f71d837df`:

- `review-engine` (`packages/workbench/review-engine/helper/review-engine`, about lines 663 to 675) and `action-review`
  (`packages/workbench/action-review/helper/action-review`, about lines 1150 to 1163) each check that the object has exactly the keys
  of the failure object and that `retryable` is a boolean, and then print "retryable" or "not retryable" in a message. Neither
  retries. `docs/specs/review-engine.md` says the engine "does not retry and does not try another bridge", a failure spends no
  round, and the flag is "reported as it is". `docs/specs/action-review.md` says a bridge failure of any class yields no approval.
  The tests state it: "a retryable failure is reported and not retried" (`review-engine/tests/test_review_findings.py`).
- The kit's `call` module (`workbench/wbkit/call.py`) runs a command once and has no retry. No other helper reads the field.
- `ask-codex` produces `bad_exit` for a program that exited non-zero. A program has no HTTP status.
- The knowledge-base module, outside this repository, decides its own retries from the field.

The plan is `docs/plans/2026-11-02-bridge-request-controls.md` (increment B). The request controls are a separate record
(`2026-11-02-temperature-and-keep-alive-in-model-sections`).

## Decision

1. **The rule.** In a bridge to a server, a response whose status is 500, 502 or 503 is `vendor_error` with the detail `bad_exit`, the
   message that the row has today ("the server answered with an error"), and `retryable` **true**. The class, the detail and the
   message are as before; only the flag differs. Every other status stays as it is, not retryable: 501 (the row for a chat model sent
   to `/api/embed` stays `model_unavailable`, and any other 501 is `bad_exit` with `retryable` false), 429, 504, every 4xx, every
   other 5xx, and a redirect. The owner's list of three is the whole list; a later record may add a status.
2. **The commands.** It applies to every request the bridge makes to the server: the chat request of `ask`, the embedding request of
   `embed` and the list of `models`. The embedding contract (version 1, which lives in `ask-ollama.md`) and the contract of `models`
   (version 1) use the same failure object and take the same rule.
3. **The status alone chooses the row, for a response that was read whole.** No word of the server's reply is matched or copied for
   this rule. The special rows are all chosen by a status together with the server's words (a 400, a 404 and a 501), so a 500, 502
   or 503 never meets one: a 500 whose text holds the words of an overflow, a thinking error or a schema error is still the
   retryable `bad_exit`. The rule applies only when the whole body was read within its bound. The two failures of the transport are
   judged before any status and keep their rows: a body over its bound is `reply_too_large` "whatever the status", and a connection
   cut after the status line was read is `unusable_reply`; both stay not retryable, even under a 500, 502 or 503.
4. **The bridge never retries.** It makes one request and keeps no count, as the contract's non-goals say. Whether to retry, how
   often and after how long is the caller's. The flag says only that the same call might succeed later. A 500 can also be permanent
   (a model that cannot load), so a caller must bound its retries; `ask-ollama.md` gives one sentence of guidance (increment C), and
   its figure comes from the knowledge-base module's report until increment F of the plan shows it.
5. **The versions and the contract text.** The bridge contract stays at version 2, the embedding contract and the contract of
   `models` at version 1: the shape of the object does not change, the field already exists, and both engines check only that it is
   a boolean. The sentence of `model-bridge.md` that says `retryable` is false for "the other classes and codes defined here" gains
   the exception for a bridge to a server and these three statuses, in increment C, where the contract text is edited in place. The
   change is to what the flag says of one existing code, for one kind of bridge. Item 6 of
   `2026-11-01-bridge-contract-version-2` (`retryable` false for a missing program and true for a server that did not answer or
   timed out) and every other item of that record are untouched.
6. **`ask-codex` and the engines are unchanged.** `ask-codex` is a bridge to a program, has no status, and keeps `bad_exit` not
   retryable; its code, its tests and its behaviour do not change. `review-engine` and `action-review`, their tests and their specs
   do not change: neither retries, so for a 5xx they print "(retryable)" where they printed "not retryable".
7. **What the rule rests on.** That a 500, 502 or 503 from the owner's server is transient (memory pressure on a one-card server) is
   from the knowledge-base module's report, not from a reading made here. Increment F of the plan records a 5xx only if the server
   gives one, and otherwise "no 5xx seen"; the fake-server tests are the proof of the rule.

## Alternatives considered

- **A new detail with `retryable` true** (for example `server_busy`), leaving `bad_exit` as it is. This is the nearest alternative and
  the one with the cleaner contract: the sentence about "the codes defined here" would stand, and an engine already treats an unknown
  code as `vendor_error`. Rejected here because the plan's completion criterion 5, which the owner approved, keeps the class, the
  detail and the message as they were, a caller that matches `bad_exit` for a server error would meet a new code, and the flag
  alone carries what the caller needs. The owner may prefer it at acceptance, and then the plan's criterion 5 and increments C and E
  change with it.
- **Every 5xx retryable.** Rejected: a 501 is not transient, and the owner named three.
- **429 and 504 as well.** Rejected for now on the owner's list; each can be added by a later record.
- **Retrying inside the bridge.** Rejected: the contract says the bridge never retries, a hidden retry hides cost (a repeated
  embedding call repeats its work), and the caller knows its own budget.
- **Leaving it to each caller** (the status quo, with the caller reading the failure text). Rejected: a caller that obeys the flag
  cannot tell the transient case, and the message is for the owner to read and not for a caller to parse.
- **A new contract version.** Rejected: the shape is unchanged and a version change would reach both engines, which accept only the
  versions they know (1 and 2).

## Consequences

- Good: a caller that obeys the flag recovers from a transient server error, and the knowledge-base module needs no parsing of
  text.
- Good: no change to the shape, to `ask-codex` or to the engines, and the bridge stays free of state.
- Bad: the flag is weaker evidence for a 5xx than for a timeout. A 500 that is permanent is labelled retryable too, so a caller
  that retries without a bound loops. The budget is the caller's and the specification says so.
- Bad: a hostile or broken server can choose the label by choosing the status, and so invite a retry. The label is advisory, nothing
  in the bridge acts on it, and the caller's bound limits the cost.
- Bad: a retried embedding call repeats its cost, and a retried chat call may differ in its reply.
- Bad: the contract's sentence about `bad_exit` is no longer true for every bridge, and a reader of the contract must know the
  exception. The text says it, and a new code is the alternative that avoids it.
- Bad: a caller that treats `bad_exit` as never retryable meets a different flag for these three statuses. The only readers found
  in this repository print it and do not branch on it.

## Open questions

- Whether 429 and 504 should join the list.
- Whether a retry loop belongs in a caller library, and not in each module.

## Evidence

- Read on 2026-11-02 at commit `b5e38878a0f6ce16a7a38f40bf778c7f71d837df`: `docs/specs/model-bridge.md` ("The failure object",
  non-goals), `docs/decisions/2026-11-01-bridge-contract-version-2.md` (item 6), `docs/specs/ask-ollama.md` ("Errors", "`embed`",
  "`models`"), `docs/specs/review-engine.md` and `docs/specs/action-review.md` (the bridge failure rules), the two engines' helpers
  and their tests of the field, `workbench/wbkit/call.py`, and `packages/workbench/ask-ollama/helper/ask-ollama`
  (`error_for`, `embed_error_for`, `models_outcome`, `transport_failure`: every status row is not retryable and the helper never
  retries). A search for `retryable` and `retry` through `workbench/` and `packages/` outside the two bridges found the two
  engines only.
- The knowledge-base module's report, relayed by the owner on 2026-11-02: a 500 on an embedding call after a chat call, and
  recovery by retrying. It was not repeated here. No run of this decision's rule has been made.
- The owner's direction on the three statuses and on 501 is in notes the owner pasted into the session on 2026-11-02, and the
  owner then approved the plan that records it (`docs/plans/2026-11-02-bridge-request-controls.md`).
- The server's address is in no tracked file and is not recorded here.

## Related files and decisions

- `docs/plans/2026-11-02-bridge-request-controls.md`
- `docs/specs/model-bridge.md`, `docs/specs/ask-ollama.md`, `docs/specs/review-engine.md`, `docs/specs/action-review.md`
- [2026-11-01-bridge-contract-version-2](2026-11-01-bridge-contract-version-2.md)
- [2026-11-02-temperature-and-keep-alive-in-model-sections](2026-11-02-temperature-and-keep-alive-in-model-sections.md)
