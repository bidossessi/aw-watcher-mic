"""The rules deciding which capture streams count as a microphone being held open."""

from typing import Any

JsonObject = dict[str, Any]

MONITOR_DEVICE_CLASS = "monitor"
MONITOR_NAME_SUFFIX = ".monitor"
BINARY_PROPERTY = "application.process.binary"
DEVICE_CLASS_PROPERTY = "device.class"


def is_monitor(source: JsonObject) -> bool:
    """Report whether a source is a loopback of an output rather than a real input.

    Args:
        source: One entry of the audio server's source list.
    """
    properties = source.get("properties") or {}
    device_class = properties.get(DEVICE_CLASS_PROPERTY)
    if device_class is not None:
        return bool(device_class == MONITOR_DEVICE_CLASS)
    return str(source.get("name", "")).endswith(MONITOR_NAME_SUFFIX)


def input_source_indices(sources: list[JsonObject]) -> frozenset[int]:
    """Return the indices of the sources that are real inputs.

    Args:
        sources: The audio server's source list, monitors included.
    """
    return frozenset(
        source["index"]
        for source in sources
        if "index" in source and not is_monitor(source)
    )


def capturing_binaries(
    source_outputs: list[JsonObject], sources: list[JsonObject]
) -> tuple[str, ...]:
    """Return the process binaries currently holding an audio input open.

    The result is deduplicated and sorted, so a binary holding several streams at
    once appears once and an unchanged set of applications compares equal between
    calls. An empty result means nothing is capturing.

    Args:
        source_outputs: The audio server's capture stream list.
        sources: The audio server's source list, used to reject monitor loopbacks.
    """
    inputs = input_source_indices(sources)
    binaries = set()
    for stream in source_outputs:
        if stream.get("corked", True):
            continue
        if stream.get("source") not in inputs:
            continue
        binary = (stream.get("properties") or {}).get(BINARY_PROPERTY)
        if binary:
            binaries.add(str(binary))
    return tuple(sorted(binaries))
