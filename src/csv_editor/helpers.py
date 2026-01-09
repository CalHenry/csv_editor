def col_label_spreasheet_format(index):
    """Convert col index to spreadsheet column label (A, B, C, ... Z, AA, AB, ...)"""
    label = ""
    index += 1
    while index > 0:
        index -= 1
        label = chr(65 + (index % 26)) + label
        index //= 26
    return label
