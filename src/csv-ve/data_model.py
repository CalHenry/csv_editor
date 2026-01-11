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

    # ---basic operations--- #
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

    # ---edit cells--- #
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

    # ---add new row or column--- #
    def row_count(self) -> int:
        return 0 if self.df is None else len(self.df)

    def column_count(self) -> int:
        return 0 if self.df is None else len(self.df.columns)

    def insert_row(self, row_idx: int, values: Optional[list[Any]] = None) -> None:
        """
        Insert a row at the given index (aka. below the cursor).

        Args:
            row_idx: Index where the row will be inserted

        Raises:
            RuntimeError: If no data is loaded
            IndexError: If index is out of bounds
        """
        if self.df is None:
            raise RuntimeError("No data loaded")

        if row_idx < 0 or row_idx > len(self.df):
            raise IndexError(f"Row index {row_idx} out of bounds")

        num_cols = len(self.df.columns)

        values = [None] * num_cols  # empty rows

        new_row = pl.DataFrame(
            [values],
            schema=self.df.schema,
        )

        top = self.df.slice(0, row_idx)
        bottom = self.df.slice(row_idx)

        self.df = pl.concat([top, new_row, bottom])
        self.modified = True

    def insert_column(
        self,
        col_idx: int,
        col_name: Optional[str] = None,
        # values: Optional[list[Any]] = None,
    ) -> None:
        """
        Insert a column at the given index (to the right of the cursor).

        Args:
            col_idx: Index where the column will be inserted
            col_name: Optional name for the new column

        Raises:
            RuntimeError: If no data is loaded
            IndexError: If index is out of bounds
        """
        if self.df is None:
            raise RuntimeError("No data loaded")

        if col_idx < 0 or col_idx > len(self.df.columns):
            raise IndexError(f"Column index {col_idx} out of bounds")

        num_rows = len(self.df)

        # Generate a unique column name if not provided
        if col_name is None:
            existing_cols = set(self.df.columns)
            counter = 1
            col_name = f"Column_{counter}"
            while col_name in existing_cols:
                counter += 1
                col_name = f"Column_{counter}"

        values = [None] * num_rows  # empty cols

        # Create new column dataframe
        new_col_df = pl.DataFrame({col_name: values})

        # Split the dataframe and insert the new column
        if col_idx == 0:
            # Insert at the beginning
            self.df = pl.concat([new_col_df, self.df], how="horizontal")
        elif col_idx >= len(self.df.columns):
            # Insert at the end
            self.df = pl.concat([self.df, new_col_df], how="horizontal")
        else:
            # Insert in the middle
            left_cols = self.df.columns[:col_idx]
            right_cols = self.df.columns[col_idx:]

            left_df = self.df.select(left_cols)
            right_df = self.df.select(right_cols)

            self.df = pl.concat([left_df, new_col_df, right_df], how="horizontal")

        self.modified = True

    # ---remove row or col--- #
    def delete_row(self, row_idx: int) -> None:
        """
        Delete a row at the given index.

        Args:
            row_idx: Index of the row to delete

        Raises:
            RuntimeError: If no data is loaded
            IndexError: If index is out of bounds
            ValueError: If trying to delete the last remaining row
        """
        if self.df is None:
            raise RuntimeError("No data loaded")

        if row_idx < 0 or row_idx >= len(self.df):
            raise IndexError(f"Row index {row_idx} out of bounds")

        if len(self.df) == 1:
            raise ValueError("Cannot delete the last remaining row")

        # Create a boolean mask for all rows except the one to delete
        mask = pl.int_range(pl.len()) != row_idx
        self.df = self.df.filter(mask)

        self.modified = True

    def delete_column(self, col_idx: int) -> None:
        """
        Delete a column at the given index.

        Args:
            col_idx: Index of the column to delete

        Raises:
            RuntimeError: If no data is loaded
            IndexError: If index is out of bounds
            ValueError: If trying to delete the last remaining column
        """
        if self.df is None:
            raise RuntimeError("No data loaded")

        if col_idx < 0 or col_idx >= len(self.df.columns):
            raise IndexError(f"Column index {col_idx} out of bounds")

        if len(self.df.columns) == 1:
            raise ValueError("Cannot delete the last remaining column")

        col_name = self.df.columns[col_idx]
        self.df = self.df.drop(col_name)

        self.modified = True
