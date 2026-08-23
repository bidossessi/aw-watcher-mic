# aw-watcher-mic

An [ActivityWatch](https://activitywatch.net/) watcher that records when an application
holds an audio input open.

It is a sensor. It records the fact of capture and the application responsible, and makes
no judgement about what the capture was for.

```
bucket    aw-watcher-mic_<hostname>
type      micstatus
data      {"status": "capturing",     "app": ["chrome"]}
          {"status": "not-capturing", "app": []}
```

Both states are emitted continuously, as `aw-watcher-afk` does, so a gap in the bucket
means the watcher was not running.

State changes arrive as audio server change notifications rather than being polled for,
so a capture session shorter than the heartbeat interval is still recorded with both
edges.

## Requirements

`pactl`, speaking to PulseAudio or to PipeWire through its PulseAudio compatibility layer.

## Usage

Run from a development checkout:

```
make install
make run
```

Install as a systemd user service, built as a self-contained bundle so it does not
depend on the checkout:

```
make install
make package
make install-bundle
```

That deploys to `~/.local/lib/aw-watcher-mic` and links `~/.local/bin/aw-watcher-mic`,
which is enough for `aw-qt` to discover it on `PATH`. Override the location with
`PREFIX`. `make uninstall-service` removes the service and the deployed bundle.

## Development

```
make check
```
