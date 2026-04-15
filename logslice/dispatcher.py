"""Event dispatcher for routing log lines to registered handlers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional

from logslice.parser import LogLine

Handler = Callable[[LogLine], None]


@dataclass
class DispatchOptions:
    """Configuration for the event dispatcher."""
    stop_on_first_match: bool = False
    default_channel: str = "default"


@dataclass
class Dispatcher:
    """Routes LogLine events to named channel handlers."""
    options: DispatchOptions = field(default_factory=DispatchOptions)
    _channels: Dict[str, List[Handler]] = field(default_factory=dict, init=False)

    def register(self, channel: str, handler: Handler) -> None:
        """Register a handler for the given channel."""
        self._channels.setdefault(channel, []).append(handler)

    def unregister(self, channel: str) -> None:
        """Remove all handlers for the given channel."""
        self._channels.pop(channel, None)

    def channels(self) -> List[str]:
        """Return names of all registered channels."""
        return list(self._channels.keys())

    def dispatch(self, line: LogLine, channel: Optional[str] = None) -> int:
        """Send *line* to handlers on *channel* (default channel if None).

        Returns the number of handlers that were called.
        """
        target = channel or self.options.default_channel
        handlers = self._channels.get(target, [])
        called = 0
        for handler in handlers:
            handler(line)
            called += 1
            if self.options.stop_on_first_match:
                break
        return called

    def dispatch_all(
        self, lines: Iterable[LogLine], channel: Optional[str] = None
    ) -> Iterator[LogLine]:
        """Dispatch every line and yield it unchanged (pipeline-friendly)."""
        for line in lines:
            self.dispatch(line, channel)
            yield line
