"""The owner's ``review-profiles.json`` as the action-review tests need it (plan `2026-11-04-review-profiles`, increment F): one profile,
`p`, that is the whole ladder ``action-review``, written in the guarded store under a given home directory."""

import json
import os

FILE = "review-profiles.json"


def document(bridge="ask-codex", model=None, effort=None, options=None, ladders=None):
    profile = {"bridge": bridge}
    if model is not None:
        profile["model"] = model
    if effort is not None:
        profile["effort"] = effort
    if options is not None:
        profile["options"] = options
    return {"format": 1, "profiles": {"p": profile}, "ladders": ladders if ladders is not None else {"action-review": ["p"]}}


def store(home):
    return os.path.join(home, ".config", "project-workbench")


def write(home, body):
    """Write `body` (a dict, text or bytes) as the owner's file under `home`; return its path."""
    folder = store(home)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    data = body if isinstance(body, (str, bytes)) else json.dumps(body)
    path = os.path.join(folder, FILE)
    with open(path, "wb" if isinstance(data, bytes) else "w") as handle:
        handle.write(data)
    return path
