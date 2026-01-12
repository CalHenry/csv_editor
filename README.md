# CSV-VE

**csv-ve** is a simple CSV viewer and editor for the terminal, built with Textual in Python.  
You can quickly open and edit your CSV file. 
Navigate using the arrow keys or the mouse. Edit, add or remove row and columns using simple key bindings.  

> Many similar tui tools exist for CSV and also written in Go or Rust so likely with better performances that Python. But I wanted to make my own and Textual is an awesome library to create simple and visually appealing apps with minimal overhead.

Screenshots:

![snapshot](screenshots/basic_snapshot.png)
 
 ## Requirements
 - Python >= 3.12
 - Textual >=7.0.0
 - Polars>=1.36.1
 
 
Components:

- **data_model.py**: Handles the data and the data manipulations with Polars in a custom Class
- **ui.py**: Textual app with all the added features
  - **csveditorapp.tss**: textual CSS for ui.py 
- **screens/screen.py**: Pop up screen to navigate to a specific cell/ row/ col
  - **screens/screen.tss**: textual CSS for screen.py
- **helpers.py**: helper function not directly related to the app itself

Textual has many built-in themes that you can select using the command palette


## Installation (with uv)  
Install uv:
Homebrew:
```sh
brew install uv
```
Unix:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```shell
uv tool install https://github.com/CalHenry/csv-ve.git
```


### Features
- [X] being able to add new rows (used the data model and not textual to achieve this)
- [x] being able to add new cols
- [X] jump to a specific cell or row or col using coordinates (format: **row:col** e.g. 12:3 - only support numeric coordinates)
- [X] delete rows
- [X] delete cols 
- [X] enter edit mode by pressing 'enter' instead of 'e' keymap
- [ ] copy cell content directly from the table (content of highlighted cell)
- [ ] resize columns
- [ ] cli
- [ ] vim naviagtion keys (hjkl)
- [ ] filtering rows/ search values ? 

#### Theme
- [X] highlight col clicking on col header
- [X] highlight row when clicking on row label

#### Dev
- [ ] tests

#### Others
- [ ] benchmarks
