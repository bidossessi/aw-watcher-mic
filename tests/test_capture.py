"""Tests for the rules deciding what counts as capture."""

import json
import pathlib

import pytest

from aw_watcher_mic.capture import capturing_binaries, input_source_indices, is_monitor

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def load(name: str) -> list[dict]:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def with_binary(stream: dict, binary: str) -> dict:
    properties = {**stream["properties"], "application.process.binary": binary}
    return {**stream, "properties": properties}


def without_binary(stream: dict) -> dict:
    properties = {
        key: value
        for key, value in stream["properties"].items()
        if key != "application.process.binary"
    }
    return {**stream, "properties": properties}


@pytest.fixture
def sources() -> list[dict]:
    return load("sources")


def test_sources_split_into_monitors_and_real_inputs(sources):
    monitors = [s for s in sources if is_monitor(s)]
    inputs = [s for s in sources if not is_monitor(s)]
    assert len(monitors) == 5
    assert len(inputs) == 3
    assert input_source_indices(sources) == frozenset({57, 62, 63})


def test_monitor_detection_falls_back_to_name():
    assert is_monitor({"name": "alsa_output.something.monitor", "properties": {}})
    assert not is_monitor({"name": "bluez_input.AA_BB_CC", "properties": {}})


def test_bluetooth_input_is_not_a_monitor():
    source = {"name": "bluez_input.AA_BB_CC", "properties": {"device.class": "sound"}}
    assert not is_monitor(source)


def test_idle_yields_nothing(sources):
    assert capturing_binaries(load("idle"), sources) == ()


def test_two_streams_of_one_binary_yield_one_entry(sources):
    streams = load("two_streams_one_binary")
    assert len(streams) == 2
    assert capturing_binaries(streams, sources) == ("pacat",)


def test_corked_streams_do_not_count(sources):
    streams = load("corked")
    assert all(s["corked"] for s in streams)
    assert capturing_binaries(streams, sources) == ()


def test_unresolved_source_does_not_count(sources):
    streams = load("corked")
    assert all(s["source"] == 0xFFFFFFFF for s in streams)
    uncorked = [{**s, "corked": False} for s in streams]
    assert capturing_binaries(uncorked, sources) == ()


def test_monitor_capture_does_not_count(sources):
    streams = load("monitor_only")
    assert capturing_binaries(streams, sources) == ()


def test_stream_without_target_object_still_counts(sources):
    streams = load("no_target_object")
    assert "target.object" not in streams[0]["properties"]
    assert capturing_binaries(streams, sources) == ("slack",)


def test_result_is_sorted_and_deduplicated(sources):
    streams = load("two_streams_one_binary")
    renamed = [
        with_binary(streams[0], "zoom"),
        streams[1],
        {**streams[1], "index": 9999},
    ]
    assert capturing_binaries(renamed, sources) == ("pacat", "zoom")


def test_stream_without_a_binary_is_ignored(sources):
    streams = load("two_streams_one_binary")
    anonymous = [without_binary(stream) for stream in streams]
    assert capturing_binaries(anonymous, sources) == ()


def test_missing_corked_field_is_treated_as_corked(sources):
    streams = load("two_streams_one_binary")
    without = [{k: v for k, v in s.items() if k != "corked"} for s in streams]
    assert capturing_binaries(without, sources) == ()
