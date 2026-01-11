from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class CoordInputScreen(ModalScreen[tuple[int, int] | None]):
    """Modal screen for navigating to a specific cell."""

    CSS_PATH = "screen.tcss"
    BINDINGS = [
        Binding("escape", "dismiss(None)", "Cancel", show=False),
    ]

    def __init__(self, max_row: int, max_col: int):
        super().__init__()
        self.max_row = max_row
        self.max_col = max_col

    def compose(self) -> ComposeResult:
        """only Input widget and its border"""
        yield Input(placeholder="row:col", id="coord_input", classes="input_rowcol")
        yield Static("", id="error_message")

    def compose2(self) -> ComposeResult:
        """only Input widget and its border"""
        with Container(id="nav_dialog"):
            yield Input(placeholder="row:col", id="coord_input", classes="input_rowcol")
            yield Static("", id="error_message")

    def on_mount(self) -> None:
        """Focus the coordinate input when mounted."""
        input = self.query_one("#coord_input", Input).focus()
        input.border_subtitle = f"(1-{self.max_row}:1-{self.max_col})"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key - validate and navigate."""
        self.validate_and_navigate()

    def validate_and_navigate(self) -> None:
        """Validate input and navigate if valid."""
        coord_input = self.query_one("#coord_input", Input)
        error_msg = self.query_one("#error_message", Static)

        value = coord_input.value.strip()

        if not value:  # do nothing - return to table screen
            self.app.pop_screen()
            return

        # Parse the input
        if ":" not in value:
            error_msg.update("Format must be ROW:COL")
            return

        parts = value.split(":")
        if len(parts) != 2:
            error_msg.update("Format must be ROW:COL")
            return

        try:
            row_str, col_str = parts
            row = int(row_str.strip()) - 1 if row_str.strip() else None
            col = int(col_str.strip()) - 1 if col_str.strip() else None
            # DataTable indexes starts at 0 so we have to substract by 1 to be consistent with the rows index (start at 1)

            # Validate that at least one is provided
            if row is None and col is None:
                error_msg.update("Please enter at least row or column")
                return

            # Validate ranges
            if row is not None and (row < 0 or row > self.max_row):
                error_msg.update(f"Row must be between 1 and {self.max_row}")
                return

            if col is not None and (col < 0 or col > self.max_col):
                error_msg.update(f"Column must be between 1 and {self.max_col}")
                return

            # Valid input - dismiss with coordinates
            self.dismiss((row, col))

        except ValueError:
            error_msg.update("Please enter valid numbers (e.g., 12:3)")
