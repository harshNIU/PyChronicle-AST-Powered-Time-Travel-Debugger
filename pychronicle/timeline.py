"""Timeline navigation and filtering over captured execution frames."""

from __future__ import annotations

from dataclasses import dataclass

from .storage import Frame, TraceStore


@dataclass(frozen=True)
class TimelinePosition:
    """Current position within an execution timeline."""

    index: int
    total: int


class Timeline:
    """Provide navigation and filtering over recorded execution frames."""

    def __init__(
        self,
        store: TraceStore,
        scope: str | None = None,
        event: str | None = None,
    ) -> None:
        self.store = store
        self.scope = scope
        self.event = event
        self._frames = list(
            store.frames(
                scope=scope,
                event=event,
            )
        )
        self._index = 0

    @property
    def total(self) -> int:
        """Return the number of frames in the current timeline."""
        return len(self._frames)

    @property
    def position(self) -> TimelinePosition:
        """Return the current timeline position."""

        if not self._frames:
            return TimelinePosition(0, 0)

        return TimelinePosition(
            self._index + 1,
            self.total,
        )

    @property
    def current(self) -> Frame | None:
        """Return the current frame."""

        if not self._frames:
            return None

        return self._frames[self._index]

    def next(self) -> Frame | None:
        """Move to the next frame."""

        if self._index + 1 < self.total:
            self._index += 1

        return self.current

    def previous(self) -> Frame | None:
        """Move to the previous frame."""

        if self._index > 0:
            self._index -= 1

        return self.current

    def move_to(self, index: int) -> Frame | None:
        """Move to a 1-based timeline position."""

        if not 1 <= index <= self.total:
            raise IndexError(
                "Timeline index out of range"
            )

        self._index = index - 1

        return self.current

    def state(self) -> dict:
        """Return reconstructed state for the current frame."""

        frame = self.current

        if frame is None:
            return {}

        return self.store.state_at(
            frame.id,
            frame.scope,
        )

    def state_at(self, index: int) -> dict:
        """Return reconstructed state for a 1-based timeline position."""

        frame = self.move_to(index)

        if frame is None:
            return {}

        return self.store.state_at(
            frame.id,
            frame.scope,
        )