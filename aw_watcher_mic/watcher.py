"""The watcher loop: change notifications in, heartbeats out."""

import argparse
import logging
import os
import signal
import subprocess
import threading
from datetime import UTC, datetime, timedelta
from types import FrameType

from aw_client import ActivityWatchClient
from aw_core.models import Event

from . import pactl
from .capture import capturing_binaries
from .config import load_config

logger = logging.getLogger(__name__)

td1ms = timedelta(milliseconds=1)

EVENT_TYPE = "micstatus"
SUBSCRIBE_KEYWORD = "source-output"
DEBOUNCE = 0.1
RECONNECT_DELAY = 1.0


def status_data(apps: tuple[str, ...]) -> dict[str, object]:
    """Return the event payload describing a set of capturing applications.

    Args:
        apps: Deduplicated, sorted process binaries holding an input open.
    """
    return {
        "status": "capturing" if apps else "not-capturing",
        "app": list(apps),
    }


class Settings:
    """Resolved watcher settings, command line overriding configuration file."""

    def __init__(
        self, config_section: dict[str, float], poll_time: float | None = None
    ):
        # Seconds between heartbeats that keep the current state's event growing
        self.poll_time = poll_time or config_section["poll_time"]


class MicWatcher:
    """Records whether any application is holding an audio input open."""

    def __init__(self, args: argparse.Namespace, testing: bool = False):
        self.settings = Settings(load_config(testing), poll_time=args.poll_time)
        self.client = ActivityWatchClient(
            "aw-watcher-mic", host=args.host, port=args.port, testing=testing
        )
        self.bucketname = f"{self.client.client_name}_{self.client.client_hostname}"
        self._wake = threading.Event()
        self._stop = threading.Event()
        # The running subscribe client, held so it can be reaped from any thread
        self._subscription: subprocess.Popen[str] | None = None

    def ping(
        self, apps: tuple[str, ...], timestamp: datetime, duration: float = 0
    ) -> None:
        """Send a heartbeat describing the given state.

        Args:
            apps: Deduplicated, sorted process binaries holding an input open.
            timestamp: When the state held.
            duration: Length of the state at this timestamp.
        """
        event = Event(timestamp=timestamp, duration=duration, data=status_data(apps))
        pulsetime = self.settings.poll_time * 2
        self.client.heartbeat(self.bucketname, event, pulsetime=pulsetime, queued=True)

    def read_state(self) -> tuple[str, ...]:
        """Return the process binaries currently holding an audio input open.

        Returns an empty result when the audio server cannot be reached, so a
        restarting server reads as silence rather than crashing the watcher.
        """
        try:
            return capturing_binaries(pactl.list_source_outputs(), pactl.list_sources())
        except pactl.PactlError as exc:
            logger.warning(f"could not read capture state: {exc}")
            return ()

    def shutdown(self) -> None:
        """Stop the loop and terminate the subscribe client.

        Safe to call more than once, and from a signal handler.
        """
        self._stop.set()
        self._wake.set()
        subscription, self._subscription = self._subscription, None
        if subscription is not None and subscription.poll() is None:
            subscription.terminate()

    def run(self) -> None:
        """Create the bucket and record capture state until the process is stopped."""
        logger.info("aw-watcher-mic started")

        signal.signal(signal.SIGTERM, self._on_signal)

        self.client.wait_for_start()
        self.client.create_bucket(self.bucketname, EVENT_TYPE, queued=True)

        notifier = threading.Thread(target=self._subscribe_loop, daemon=True)
        notifier.start()

        try:
            with self.client:
                self._heartbeat_loop()
        finally:
            self.shutdown()
            notifier.join(timeout=RECONNECT_DELAY)

    def _on_signal(self, signum: int, frame: FrameType | None) -> None:
        logger.info(f"aw-watcher-mic stopped by signal {signum}")
        self.shutdown()

    def _subscribe_loop(self) -> None:
        while not self._stop.is_set():
            try:
                subscription = pactl.open_subscription()
            except pactl.PactlError as exc:
                logger.warning(f"could not subscribe, retrying: {exc}")
                self._stop.wait(RECONNECT_DELAY)
                continue

            self._subscription = subscription
            try:
                assert subscription.stdout is not None
                for line in subscription.stdout:
                    if self._stop.is_set():
                        break
                    if SUBSCRIBE_KEYWORD in line:
                        self._wake.set()
            finally:
                if subscription.poll() is None:
                    subscription.terminate()

            if not self._stop.is_set():
                logger.warning("subscription ended, reconnecting")
                self._wake.set()
                self._stop.wait(RECONNECT_DELAY)

    def _heartbeat_loop(self) -> None:
        apps = self.read_state()
        self.ping(apps, timestamp=datetime.now(UTC))

        while not self._stop.is_set():
            try:
                if os.getppid() == 1:
                    logger.info("aw-watcher-mic stopped because parent process died")
                    break

                notified = self._wake.wait(timeout=self.settings.poll_time)
                self._wake.clear()
                if self._stop.is_set():
                    break
                if notified:
                    self._stop.wait(DEBOUNCE)

                now = datetime.now(UTC)
                current = self.read_state()

                if current != apps:
                    logger.info(f"capture state changed: {apps} -> {current}")
                    self.ping(apps, timestamp=now)
                    apps = current
                    self.ping(apps, timestamp=now + td1ms)
                else:
                    self.ping(apps, timestamp=now)

            except KeyboardInterrupt:
                logger.info("aw-watcher-mic stopped by keyboard interrupt")
                break
