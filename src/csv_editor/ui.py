import sys
from pathlib import Path

from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Input

from .data_model import CSVDataModel
from .helpers import col_label_spreasheet_format


##-----Textual app-----##
class CSVEditorApp(App):
    """A Textual app for editing CSV files"""

    CSS_PATH = "csveditorapp.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save", "Save"),
        Binding("r", "reload", "Reload"),
        Binding("e", "edit_cell", "Edit Cell", show=True),
        Binding("escape", "cancel_edit", "Cancel", show=True),
        Binding("n", "add_new_row", "new_row", show=True),
    ]

    def __init__(self, csv_path: str):
        super().__init__()
        self.csv_path = csv_path
        self.data_model = CSVDataModel(csv_path)

    '''
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        with Vertical(id="main-container"):
            yield IndexColumn(id="index_col", content=("tests"))
            yield DataTable(cursor_type="cell", header_height=2, zebra_stripes=True)
            yield Input(placeholder="Edit cell value...", id="formula_bar")
        yield Footer()
    '''

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="main-container"):
            yield DataTable(cursor_type="cell", header_height=2, zebra_stripes=True)
            yield Input(placeholder="Edit cell value...", id="formula_bar")

        yield Footer()

    def on_mount(self) -> None:
        """Load data when app starts"""
        self.theme = "catppuccin-mocha"
        self.load_data()

    # ---file/ table actions--- #
    def load_data(self) -> None:
        """Load CSV data into the DataTable"""
        table = self.query_one(DataTable)
        table.clear(columns=True)

        df = self.data_model.df

        # set header to receive loaded data info (file name, col and row count)
        header = self.query_one(Header)
        header.tall = False

        if df is None:
            self.sub_title = str("No data loaded")
            return

        # Add columns and rows
        for i, col_name in enumerate(df.columns):
            labeled_col_name = f"{col_label_spreasheet_format(i)}\n{col_name}"
            table.add_column(labeled_col_name, key=col_name, width=30)
        for i, row in enumerate(df.iter_rows()):
            table.add_row(*row, label=f"{i + 1}")

        # Update header with file info
        self.sub_title = f"{self.csv_path} | {len(df)} rows × {len(df.columns)} cols"

        # Set up table cursor
        table.cursor_type = "cell"

    def action_add_new_row(self) -> None:
        table = self.query_one(DataTable)

        table.add_row()  # add at the bottom and can't change that
        # get_row_key() or row_index() can help me sort the row
        # pop the new row and give him the

    def _update_row_indices(self) -> None:
        """Update the index column for all rows"""
        table = self.query_one(DataTable)

        for idx, row_key in enumerate(table.rows.keys(), start=1):
            label = Text(str(idx), style="bold")
            # Update just the index column
            table.update_cell(row_key, "__index__", label)

    def action_save(self) -> None:
        """Save the CSV file"""
        try:
            self.data_model.save()
            self.notify("Saved successfully", severity="information")
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def action_reload(self) -> None:
        """Reload the CSV file from disk"""
        try:
            self.data_model.reload()
            self.load_data()
            self.notify("Reloaded from disk", severity="information")
        except Exception as e:
            self.notify(f"Reload failed: {e}", severity="error")

    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:
        """Update formula bar when cursor moves to a new cell"""
        table = self.query_one(DataTable)
        formula_bar = self.query_one("#formula_bar", Input)

        # Get the value of the highlighted cell
        try:
            current_value = table.get_cell_at(event.coordinate)
            formula_bar.value = str(current_value)
        except Exception:
            # Handle case where cell might not exist
            formula_bar.value = ""

    # --- edit data actions--- #
    def action_edit_cell(self) -> None:
        """Start editing selected cell in formula bar"""
        table = self.query_one(DataTable)
        formula_bar = self.query_one("#formula_bar", Input)

        if table.cursor_coordinate is None:
            return

        row_key, col_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        current_value = table.get_cell(row_key, col_key)

        # Populate formula bar with current value
        self.editing_cell = (row_key, col_key, current_value)
        formula_bar.value = str(current_value)
        formula_bar.focus()

    # Handle the input submission:
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "formula_bar" and hasattr(self, "editing_cell"):
            row_key, col_key, _ = self.editing_cell
            table = self.query_one(DataTable)

            row_idx = table.get_row_index(row_key)
            col_idx = list(table.columns.keys()).index(col_key)

            self.data_model.set_cell(row_idx, col_idx, event.value)
            table.update_cell(row_key, col_key, event.value)

            self._clear_edit_state(table)

    def on_key(self, event: events.Key) -> None:
        """Cancel the edit with espace key"""
        formula_bar = self.query_one("#formula_bar", Input)
        if (
            event.key == "escape"
            and formula_bar.has_focus
            and hasattr(self, "editing_cell")
        ):
            table = self.query_one(DataTable)
            row_key, col_key, original_value = self.editing_cell
            # Restore original value if it was modified
            formula_bar.value = ""
            self._clear_edit_state(table)
            event.prevent_default()
            event.stop()

    def _clear_edit_state(self, table: DataTable) -> None:
        """Helper to clean up after edit completion or cancelation"""
        formula_bar = self.query_one("#formula_bar", Input)
        formula_bar.value = ""
        table.focus()
        if hasattr(self, "editing_cell"):
            delattr(self, "editing_cell")

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Show/ hide the 'escape' keybinding in the footer. Show only in edit mode"""
        if action == "cancel_edit":
            return hasattr(self, "editing_cell")
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python app.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]

    if not Path(csv_file).exists():
        print(f"Error: File '{csv_file}' not found")
        sys.exit(1)

    app = CSVEditorApp(csv_file)
    app.run()


if __name__ == "__main__":
    main()
