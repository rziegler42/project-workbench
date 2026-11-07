# Review of docs/specs/ask-ollama.md

This file is a rendering of state.json for people. It is never read back.

- Kind: spec
- Rounds in this window: 5 of 5 rounds (ceiling 5)
- Rounds in all: 5
- Decisions recorded: 9
- Closed: no

## Rounds

- Round 1, 2026-11-01T21:05:26Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 2, 2026-11-01T21:07:35Z: the reviewer said changes_needed, the engine read changes_needed, 3 findings, model gpt-5.6-terra
- Round 3, 2026-11-01T21:08:50Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 4, 2026-11-01T21:13:14Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 5, 2026-11-01T21:23:30Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra

## Decisions

- R1-F1: applied on 2026-11-01T21:06:08Z: Valid. The request bound was below what valid inputs need. It is now 2,100,000 bytes, with the arithmetic for the largest prompt and schema, and an oversize request is refused before any connection.
- R1-F2: applied on 2026-11-01T21:06:14Z: Valid. A model name is now validated by both the contract rule and the record rule, so the fallback in the object always fits and model is never null for a call that was sent.
- R1-F3: applied on 2026-11-01T21:06:14Z: Valid but minor. The request now names the literal User-Agent value and the exact content of each header.
- R2-F1: applied on 2026-11-01T21:07:48Z: Valid. The order of conditions is now scoped: a body over its bound is reply too large for any status, an error status follows the status rows and the matching rule and falls to bad exit when its b...
- R2-F2: applied on 2026-11-01T21:07:53Z: Valid. The embedding body is now model, input and truncate, plus options with num ctx only when the record has a context, and no other field.
- R2-F3: applied on 2026-11-01T21:07:54Z: Valid. The embedding request now names the same headers as ask, and says the transport, bounds and timeouts apply to it.
- R3-F1: applied on 2026-11-01T21:09:00Z: Valid. The order for a success status now includes done false, placed right after the body check and before context overflow and the cut reply, so every success reply has exactly one outcome.
- R4-F1: applied on 2026-11-01T21:13:42Z: Valid, and caused by my previous fix. The embedding command now has its own order of checks for a success status: the body, then the embeddings, then the size of the object, with the chat-only chec...
- R5-F1: applied on 2026-11-01T21:23:38Z: Valid. The embedding usage now follows the rule for ask: a whole number from 0 to 10^12 that is not a boolean is emitted, and anything else becomes null without making the reply unusable.
