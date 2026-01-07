from pathlib import Path
from typing import Any, Optional

import polars as pl


class CSVDataModel:
    """
    Data model for managing CSV files with Polars
    Handles loading, editing, and saving CSV data
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.df: Optional[pl.DataFrame] = (
            None  # Lazyframes ?? (maybe later when prototype works with df)
        )
        self.modified = False
        self.has_header = True

        self.load()

    def load(self) -> None:
        """
        Load csv with polars
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        try:
            # Try loading with header first
            self.df = pl.read_csv(
                self.file_path,
                has_header=True,
                infer_schema_length=1000,
            )
        except Exception as e:
            raise Exception(f"Failed to load CSV: {e}")

        self.modified = False

    def reload(self) -> None:
        self.load()

    def save(self) -> None:
        """
        Save the data back to the original file

        Raises:
            RuntimeError: If no data is loaded
        """
        if self.df is None:
            raise RuntimeError("No data to save")

        self.df.write_csv(self.file_path)
        self.modified = False

    def set_cell(self, row_idx: int, col_idx: int, value: Any) -> None:
        """
        Set the value at a specific cell.

        Args:
            row_idx: Row index (0-based)
            col_idx: Column index (0-based)
            value: New value for the cell

        Raises:
            IndexError: If indices are out of bounds
        """
        if self.df is None:
            raise RuntimeError("No data loaded")

        if row_idx < 0 or row_idx >= len(self.df):
            raise IndexError(f"Row index {row_idx} out of bounds")

        if col_idx < 0 or col_idx >= len(self.df.columns):
            raise IndexError(f"Column index {col_idx} out of bounds")

        col_name = self.df.columns[col_idx]

        # Create a new dataframe with the updated value
        # We use a workaround: update the column with a when-then-otherwise expression
        self.df = self.df.with_columns(
            pl.when(pl.int_range(pl.len()) == row_idx)
            .then(pl.lit(value))
            .otherwise(pl.col(col_name))
            .alias(col_name)
        )

        self.modified = True
