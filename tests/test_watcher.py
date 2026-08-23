"""Tests for the event payload the watcher writes."""

from aw_watcher_mic.watcher import status_data


def test_idle_state_is_not_capturing():
    assert status_data(()) == {"status": "not-capturing", "app": []}


def test_capturing_state_names_the_applications():
    assert status_data(("chrome",)) == {"status": "capturing", "app": ["chrome"]}


def test_app_key_is_always_present():
    assert "app" in status_data(())
    assert "app" in status_data(("slack",))


def test_equal_states_compare_equal_so_heartbeats_merge():
    assert status_data(("chrome", "slack")) == status_data(("chrome", "slack"))


def test_different_states_compare_unequal_so_heartbeats_split():
    assert status_data(("chrome",)) != status_data(("slack",))
    assert status_data(("chrome",)) != status_data(())
