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
        raise SystemExit(
            "The TUI requires Textual. Install it with: pip install -e .[tui]"
        ) from error

    frames = list(store.frames())
    total_frames = len(frames)

    class ChronicleApp(App[None]):
        CSS = """
        #code {
            width: 1fr;
            height: 1fr;
            border: solid $accent;
        }

        #state {
            width: 1fr;
            height: 1fr;
            border: solid $accent;
            padding: 1;
        }

        #timeline_bar {
            height: 3;
            align: center middle;
            content-align: center middle;
        }

        #frame_input {
            width: 12;
        }

        #frame_total {
            padding: 1 1;
        }
        """

        current_index: int = 1

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)

            with Horizontal():
                yield RichLog(
                    id="code",
                    wrap=True,
                    highlight=True,
                    markup=False,
                )
                yield Static(id="state")

            with Horizontal(id="timeline_bar"):
                yield Button("Prev", id="prev_frame")
                yield Input(value="1", id="frame_input")
                yield Label(f" / {total_frames}", id="frame_total")
                yield Button("Next", id="next_frame")

            yield Footer()

        def on_mount(self) -> None:
            code_widget = self.query_one("#code", RichLog)

            source_lines = source_path.read_text(
                encoding="utf-8"
            ).splitlines()

            for number, line in enumerate(source_lines, start=1):
                code_widget.write(f"{number:4} | {line}")

            self._render_frame(self.current_index)

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "prev_frame":
                if self.current_index > 1:
                    self.current_index -= 1
                    self._update_frame()

            elif event.button.id == "next_frame":
                if self.current_index < total_frames:
                    self.current_index += 1
                    self._update_frame()

        def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id != "frame_input":
                return

            try:
                value = int(event.value)
            except ValueError:
                return

            if 1 <= value <= total_frames:
                if value != self.current_index:
                    self.current_index = value
                    self._render_frame(value)

        def _update_frame(self) -> None:
            self.query_one("#frame_input", Input).value = str(
                self.current_index
            )
            self._render_frame(self.current_index)

        def _render_frame(self, index: int) -> None:
            state_widget = self.query_one("#state", Static)

            if not frames:
                state_widget.update("No execution frames captured.")
                return

            frame = frames[index - 1]

            state = store.state_at(
                frame.id,
                frame.scope,
            )

            source_lines = source_path.read_text(
                encoding="utf-8"
            ).splitlines()

            current_line = ""
            if 1 <= frame.line_number <= len(source_lines):
                current_line = source_lines[frame.line_number - 1]

            state_widget.update(
                f"Frame: {index} / {total_frames}\n"
                f"Line: {frame.line_number}\n"
                f"Code: {current_line}\n"
                f"Event: {frame.event}\n"
                f"Scope: {frame.scope}\n\n"
                f"Variables:\n"
                f"{json.dumps(state, indent=2, default=str)}"
            )

    ChronicleApp().run()