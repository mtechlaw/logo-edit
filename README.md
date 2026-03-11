# Logo Branding Tool

This tool converts provider logos into a consistent branded badge style:

- Canvas: **356 x 346 px**
- Background: **white circle**
- Logo: **centered**
- Output: **PNG**
- Outside the circle: **transparent**

## Files

- `app.py` — Streamlit interface
- `processor.py` — core image processing logic
- `requirements.txt` — dependencies

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

The tool removes **near-white backgrounds** automatically. That works well for logos on white backgrounds, but it may need adjustment for logos with very light elements. Use the threshold slider in the app to fine-tune the result.
