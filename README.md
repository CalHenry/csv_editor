Trying to create a csv viewer and editor for the terminal with Python and Textual

WORK IN PROGRESS


Components:

- **data_model.py**: Handles the data work with Polars in a custom Class
- **ui.py**: Textual app, can read and edit cells (for now)
  - **csveditorapp.tss**: textual css for ui.py

## Installation
(With uv)

```shell

```

### TODO

### Features
- [X] being able to add new rows (used the data model and not textual to acheive this)
- [x] being able to add new cols
- [ ] jump to a cell or row or col using coordinates (like A:25, or :25, or A: (synthax to define))
- [X] delete rows
- [X] delete cols 

#### Theme
- [X] highlight col clicking on col header
- [X] highlight row when clicking on row indice
- [ ] fix indice row (first row) background to be clear that it's not part of the data
