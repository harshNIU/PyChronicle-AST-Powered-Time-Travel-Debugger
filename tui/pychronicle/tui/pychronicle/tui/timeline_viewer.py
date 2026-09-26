import sqlite3
import os


class TimelineViewer:
    """
    A simple text-based interface for browsing a program's
    recorded execution timeline (produced by the tracer/storage modules).

    Day 2:
    - Reads execution steps from timeline.db (SQLite)
    - Lets the user step forward/backward through the timeline
      one line at a time, like a basic time-travel debugger UI
    """

    def __init__(self, db_path="timeline.db"):
        self.db_path = db_path
        self.steps = []
        self.current_index = 0

    def load(self):
        if not os.path.exists(self.db_path):
            print(f"No timeline found at '{self.db_path}'. Run the tracer first.")
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT step_index, line_number, changed_vars FROM execution_steps ORDER BY step_index"
        )
        self.steps = cursor.fetchall()
        conn.close()

        if not self.steps:
            print("Timeline is empty.")
            return False

        return True

    def show_current_step(self):
        step_index, line_number, changed_vars = self.steps[self.current_index]
        print(f"\nStep {self.current_index + 1}/{len(self.steps)}")
        print(f"Line: {line_number}")
        print(f"Changed variables: {changed_vars}")

    def run(self):
        if not self.load():
            return

        print("PyChronicle Timeline Viewer")
        print("Commands: [n]ext, [p]revious, [q]uit\n")

        self.show_current_step()

        while True:
            command = input("\n> ").strip().lower()

            if command == "n":
                if self.current_index < len(self.steps) - 1:
                    self.current_index += 1
                    self.show_current_step()
                else:
                    print("Already at the last step.")

            elif command == "p":
                if self.current_index > 0:
                    self.current_index -= 1
                    self.show_current_step()
                else:
                    print("Already at the first step.")

            elif command == "q":
                print("Exiting timeline viewer.")
                break

            else:
                print("Unknown command. Use n, p, or q.")


    def show_position(self):
        """Display the current position in the execution timeline."""
        total = len(self.steps)

        if total == 0:
            print("Timeline is empty.")
            return

        print(f"Timeline position: {self.current_index + 1} / {total}")
    def reset(self):
        """Reset timeline browsing to the first execution step."""
        self.current_index = 0

if __name__ == "__main__":
    viewer = TimelineViewer()
    viewer.run()
  
