"""Optional Textual time-scrubbing interface."""

from __future__ import annotations

import json
from pathlib import Path

from .storage import TraceStore
from .timeline import Timeline


def launch(store: TraceStore, source_path: Path) -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal
        from textual.widgets import (
            Button,
            Footer,
            Header,
            Input,
            Label,
            RichLog,
            Static,
        )
    except ImportError as error:
        raise SystemExit(
            "The TUI requires Textual. Install it with: pip install -e .[tui]"
        ) from error

    timeline = Timeline(store)
    total_frames = timeline.total

    # The source file may not be available when the TUI is tested
    # independently of the original execution environment.
    if source_path.exists():
        source_lines = source_path.read_text(
            encoding="utf-8"
        ).splitlines()
    else:
        source_lines = []

    class ChronicleApp(App[None]):
        """Interactive timeline viewer for a captured PyChronicle trace."""

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
                yield Input(
                    value="1" if total_frames else "0",
                    id="frame_input",
                )
                yield Label(
                    f" / {total_frames}",
                    id="frame_total",
                )
                yield Button("Next", id="next_frame")

            yield Footer()

        def on_mount(self) -> None:
            self._render_source()
            self._render_frame()

        def _render_source(self) -> None:
            """Render the source file with line numbers."""
            code_widget = self.query_one("#code", RichLog)

            if not source_lines:
                code_widget.write(
                    "Source file is unavailable."
                )
                return

            for number, line in enumerate(
                source_lines,
                start=1,
            ):
                code_widget.write(
                    f"{number:4} | {line}"
                )

        def on_button_pressed(
            self,
            event: Button.Pressed,
        ) -> None:
            """Handle timeline navigation buttons."""
            if total_frames == 0:
                return

            if event.button.id == "prev_frame":
                timeline.previous()
                self._sync_frame_input()
                self._render_frame()

            elif event.button.id == "next_frame":
                timeline.next()
                self._sync_frame_input()
                self._render_frame()

        def on_input_changed(
            self,
            event: Input.Changed,
        ) -> None:
            """Jump directly to a requested timeline position."""
            if event.input.id != "frame_input":
                return

            if total_frames == 0:
                return

            try:
                value = int(event.value)
            except ValueError:
                return

            if not 1 <= value <= total_frames:
                return

            if value != timeline.position.index:
                timeline.move_to(value)
                self._render_frame()

        def _sync_frame_input(self) -> None:
            """Keep the frame input synchronized with Timeline."""
            input_widget = self.query_one(
                "#frame_input",
                Input,
            )

            if total_frames == 0:
                input_widget.value = "0"
            else:
                input_widget.value = str(
                    timeline.position.index
                )

        def _render_frame(self) -> None:
            """Render the current frame and reconstructed state."""
            state_widget = self.query_one(
                "#state",
                Static,
            )

            frame = timeline.current

            if frame is None:
                state_widget.update(
                    "No execution frames captured."
                )
                return

            state = timeline.state()

            current_line = ""

            if (
                1 <= frame.line_number
                <= len(source_lines)
            ):
                current_line = source_lines[
                    frame.line_number - 1
                ]

            position = timeline.position

            state_widget.update(
                f"Frame: {position.index} / "
                f"{position.total}\n"
                f"Frame ID: {frame.id}\n"
                f"Line: {frame.line_number}\n"
                f"Event: {frame.event}\n"
                f"Scope: {frame.scope}\n\n"
                f"Source:\n"
                f"{frame.line_number:4} | "
                f"{current_line}\n\n"
                f"Variables:\n"
                f"{json.dumps(state, indent=2, default=str)}"
            )

    ChronicleApp().run()