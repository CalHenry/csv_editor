import sys
from pathlib import Path

from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Input

from .data_model import CSVDataModel
from .helpers import (
    col_label_spreasheet_format,
)


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
        Binding("n", "insert_new_row_below_cursor", "new_row", show=True),
        Binding("b", "insert_new_col_right_cursor", "new_col", show=True),
        Binding("ctrl+n", "delete_row", "del_row", show=False),
        Binding("ctrl+b", "delete_column", "del_col", show=False),
    ]

    def __init__(self, csv_path: str):
        super().__init__()
        self.csv_path = csv_path
        self.data_model = CSVDataModel(csv_path)

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="main-container"):
            yield DataTable(cursor_type="cell", header_height=2, zebra_stripes=True)
            yield Input(
                placeholder="Edit cell value...",
                id="formula_bar",
                classes="formula_bar",
            )
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

    # ---edit data actions--- #
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

    # ---add data actions---#
    def action_insert_new_row_below_cursor(self) -> None:
        """
        Insert a new empty row below the current cursor position.
        Uses CSVDataModel (that uses polars) to create the new row (textual only reads - the file is the source of thruth)
        - insert the new row in the data model (polars)
        - reload the table (textual)
        - move the cursor back to the original position so it appears like it didn't move
        """
        table = self.query_one(DataTable)

        if table.cursor_coordinate is None:
            return

        row, col = table.cursor_coordinate

        try:
            self.data_model.insert_row(row + 1)
        except Exception as e:
            self.notify(f"Failed to insert row: {e}", severity="error")
            return

        self.load_data()  # reset cursor position to the first row (by default)

        # Restore cursor to its position
        new_row = min(row + 1, self.data_model.row_count() - 1)
        table.move_cursor(row=new_row, column=col)

    def action_insert_new_col_right_cursor(self) -> None:
        """
        Insert a new empty column to the right of the current cursor position.
        Uses CSVDataModel (that uses polars) to create the new column
        - insert the new column in the data model (polars)
        - reload the table (textual)
        - move the cursor back to the original position so it appears like it didn't move
        """
        table = self.query_one(DataTable)

        if table.cursor_coordinate is None:
            return

        row, col = table.cursor_coordinate

        try:
            self.data_model.insert_column(col + 1)
        except Exception as e:
            self.notify(f"Failed to insert column: {e}", severity="error")
            return

        self.load_data()  # reset cursor position to the first cell (by default)

        # Restore cursor to its position
        new_col = min(col + 1, self.data_model.column_count() - 1)
        table.move_cursor(row=row, column=new_col)

    # ---remove row or col--- #
    def action_delete_row(self) -> None:
        """
        Delete the row at the current cursor position.
        """
        table = self.query_one(DataTable)

        if table.cursor_coordinate is None:
            return

        row, col = table.cursor_coordinate

        try:
            self.data_model.delete_row(row)
        except ValueError as e:
            self.notify(str(e), severity="warning")
            return
        except Exception as e:
            self.notify(f"Failed to delete row: {e}", severity="error")
            return

        self.load_data()

        # Move cursor to the same row (or the last row if we deleted the last one)
        new_row = min(row, self.data_model.row_count() - 1)
        table.move_cursor(row=new_row, column=col)

    def action_delete_column(self) -> None:
        """
        Delete the column at the current cursor position.
        """
        table = self.query_one(DataTable)

        if table.cursor_coordinate is None:
            return

        row, col = table.cursor_coordinate

        try:
            self.data_model.delete_column(col)
        except ValueError as e:
            self.notify(str(e), severity="warning")
            return
        except Exception as e:
            self.notify(f"Failed to delete column: {e}", severity="error")
            return

        self.load_data()

        # Move cursor to the same column (or the last column if we deleted the last one)
        new_col = min(col, self.data_model.column_count() - 1)
        table.move_cursor(row=row, column=new_col)


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
