"""Entry point registered as the ``aw-watcher-mic`` script."""

import logging

from aw_core.log import setup_logging

from .config import parse_args
from .watcher import MicWatcher


def main() -> None:
    """Parse the command line, set up logging, and run the watcher."""
    args = parse_args()

    setup_logging(
        "aw-watcher-mic",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    logging.getLogger(__name__).info(f"Started aw-watcher-mic with args {args}")
    MicWatcher(args, testing=args.testing).run()


if __name__ == "__main__":
    main()
