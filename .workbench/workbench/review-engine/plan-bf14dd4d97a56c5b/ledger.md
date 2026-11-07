# Review of docs/plans/2026-11-01-ask-ollama-bridge.md

This file is a rendering of state.json for people. It is never read back.

- Kind: plan
- Rounds in this window: 5 of 5 rounds (ceiling 5)
- Rounds in all: 5
- Decisions recorded: 10
- Closed: no

## Rounds

- Round 1, 2026-11-01T20:06:03Z: the reviewer said changes_needed, the engine read changes_needed, 4 findings, model gpt-5.6-terra
- Round 2, 2026-11-01T20:08:46Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 3, 2026-11-01T20:10:45Z: the reviewer said changes_needed, the engine read changes_needed, 2 findings, model gpt-5.6-terra
- Round 4, 2026-11-01T20:13:58Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra
- Round 5, 2026-11-01T20:21:08Z: the reviewer said changes_needed, the engine read changes_needed, 1 findings, model gpt-5.6-terra

## Decisions

- R1-F1: rejected on 2026-11-01T20:07:12Z: The plan does end with the Result heading and its empty body, and the plan check passes. The only other occurrence of that text is an inline mention inside a step, not a heading. The reviewer may h...
- R1-F2: applied on 2026-11-01T20:07:18Z: Valid. Increment B now amends the declaration rule of the bridge spec so a bridge module may provide a further capability through a further command and a read-only check argument, and the plan name...
- R1-F3: applied on 2026-11-01T20:07:18Z: Valid. The plan now has a read-only check command that prints a warning for an unauthenticated plain http record away from loopback and never prints a host or port, with a spec step, tests, an impl...
- R1-F4: applied on 2026-11-01T20:07:18Z: Valid. The close-out increment now has one commit, and recording the upgrade is a separate increment H with its own verification and commit.
- R2-F1: applied on 2026-11-01T20:09:24Z: Valid. Increment B now amends the bridge spec as a whole: its purpose, the guarantees scoped to a program or named for a server, the endpoint and authentication rules including a bridge that declin...
- R2-F2: applied on 2026-11-01T20:09:24Z: Valid. The plan now specifies verified HTTPS in the spec step, with a context function and the error mapping, and adds tests with throwaway certificates for an untrusted one, one for another host a...
- R3-F1: applied on 2026-11-01T20:11:12Z: Valid. A request necessarily carries the host and the connection destination. The test now requires that only the selected validated record decides them, that nothing else of the record is sent, an...
- R3-F2: applied on 2026-11-01T20:11:12Z: Valid. A cut reply cannot be caused reliably on a real server, so the deterministic fake-server tests are the required proof and the real run records it only if the owner has a model with a small o...
- R4-F1: applied on 2026-11-01T20:14:32Z: Valid. The decision, the spec and the tests now fix the grammar of the host field: the accepted forms, the length limits, loopback as an IP literal only, and a long list of malformed hosts that mus...
- R5-F1: applied on 2026-11-01T20:21:23Z: Valid. The plan now has a trusted but expired certificate fixture, with a fallback that raises the verification error for expiry if the system openssl cannot make one, and the test requires the fix...
