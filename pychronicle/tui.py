"""Optional Textual time-scrubbing interface."""

from __future__ import annotations

import json
from pathlib import Path

from .storage import TraceStore


def launch(store: TraceStore, source_path: Path) -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal
        from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Static
    except ImportError as error:
        raise SystemExit("The TUI requires Textual. Install it with: pip install -e .[tui]") from error

    frames = list(store.frames())
    total_frames = max(1, len(frames))

    class ChronicleApp(App[None]):
        CSS = """
        #code, #state { width: 1fr; height: 1fr; border: solid $accent; }
        #timeline_bar { height: 3; align: center middle; content-align: center middle; }
        #frame_input { width: 12; }
        #frame_total { padding: 1 1; }
        """

        current_index: int = total_frames

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Horizontal():
                yield RichLog(id="code", wrap=True, highlight=True)
                yield Static(id="state")
            with Horizontal(id="timeline_bar"):
                yield Button("◄ Prev", id="prev_frame")
                yield Input(value=str(self.current_index), id="frame_input")
                yield Label(f" / {total_frames}", id="frame_total")
                yield Button("Next ►", id="next_frame")
            yield Footer()

        def on_mount(self) -> None:
            log_widget = self.query_one("#code", RichLog)
            log_widget.write(source_path.read_text(encoding="utf-8"))
            self._render_frame(self.current_index)

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "prev_frame" and self.current_index > 1:
                self.current_index -= 1
                self.query_one("#frame_input", Input).value = str(self.current_index)
                self._render_frame(self.current_index)
            elif event.button.id == "next_frame" and self.current_index < total_frames:
                self.current_index += 1
                self.query_one("#frame_input", Input).value = str(self.current_index)
                self._render_frame(self.current_index)

        def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "frame_input":
                try:
                    val = int(event.value)
                    if 1 <= val <= total_frames and val != self.current_index:
                        self.current_index = val
                        self._render_frame(self.current_index)
                except ValueError:
                    pass

        def _render_frame(self, index: int) -> None:
            if not frames:
                self.query_one("#state", Static).update("No variable changes captured.")
                return
            frame = frames[index - 1]
            state = store.state_at(frame.id, frame.scope)
            self.query_one("#state", Static).update(
                f"Frame {frame.id} / {total_frames} · Line {frame.line_number} · Event: {frame.event} · Scope: {frame.scope}\n\n"
                + json.dumps(state, indent=2, default=str)
            )

    ChronicleApp().run()

