# Logo Styling Tool

This revision matches the reference style more closely.

## What changed

- Uses an **exact 346 px circle** inside a **356 x 346 px** transparent canvas
- Leaves **5 px transparent gutters** on the left and right
- Uses a **smaller default logo scale** for more breathing room
- Removes white backgrounds using **edge-connected flood fill** instead of blanket white deletion
- Supports batch export and SVG files

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```
