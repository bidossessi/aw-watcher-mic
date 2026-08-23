"""Access to the audio server through the ``pactl`` command line client.

Every call into the audio server is made here, so a future move to a different
client touches this module alone.
"""

import json
import subprocess
from typing import Any

PACTL = "pactl"

JsonObject = dict[str, Any]


class PactlError(RuntimeError):
    """Raised when pactl cannot be run, exits non-zero, or emits invalid JSON."""


def _list(what: str) -> list[JsonObject]:
    try:
        completed = subprocess.run(
            [PACTL, "-f", "json", "list", what],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PactlError(f"could not list {what}: {exc}") from exc

    try:
        payload = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise PactlError(f"could not parse {what} payload: {exc}") from exc

    if not isinstance(payload, list):
        raise PactlError(f"expected a list of {what}, got {type(payload).__name__}")
    return payload


def list_source_outputs() -> list[JsonObject]:
    """Return the audio server's capture streams, one object per stream.

    Raises:
        PactlError: The audio server could not be reached or answered unparseably.
    """
    return _list("source-outputs")


def list_sources() -> list[JsonObject]:
    """Return the audio server's sources, real inputs and monitors alike.

    Raises:
        PactlError: The audio server could not be reached or answered unparseably.
    """
    return _list("sources")


def open_subscription() -> subprocess.Popen[str]:
    """Start ``pactl subscribe`` and return the running process.

    The caller owns the process, reads change notifications as lines from its
    ``stdout``, and is responsible for terminating and restarting it.

    Raises:
        PactlError: The subscribe client could not be started.
    """
    try:
        return subprocess.Popen(
            [PACTL, "subscribe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    except OSError as exc:
        raise PactlError(f"could not subscribe: {exc}") from exc
