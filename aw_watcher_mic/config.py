"""Command line and configuration file handling."""

import argparse
import sys
from typing import Any

from aw_core.config import load_config_toml

default_config = """
[aw-watcher-mic]
poll_time = 10

[aw-watcher-mic-testing]
poll_time = 1
""".strip()


def load_config(testing: bool) -> Any:
    """Return the configuration section for the requested mode.

    Args:
        testing: Select the testing section rather than the normal one.
    """
    section = "aw-watcher-mic" + ("-testing" if testing else "")
    return load_config_toml("aw-watcher-mic", default_config)[section]


def parse_args() -> argparse.Namespace:
    """Return the parsed command line, with configuration values as defaults."""
    testing = "--testing" in sys.argv
    config = load_config(testing)

    parser = argparse.ArgumentParser(
        description="A watcher for applications holding an audio input open."
    )
    parser.add_argument("--host", dest="host")
    parser.add_argument("--port", dest="port")
    parser.add_argument(
        "--testing", dest="testing", action="store_true", help="run in testing mode"
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="run with verbose logging",
    )
    parser.add_argument(
        "--poll-time", dest="poll_time", type=float, default=config["poll_time"]
    )
    return parser.parse_args()
