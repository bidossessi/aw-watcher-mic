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

```
make install
make run
```

## Development

```
make check
```
