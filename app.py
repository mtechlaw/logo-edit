from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image

from processor import batch_process, process_logo, zip_outputs

st.set_page_config(page_title="Logo Branding Tool", layout="wide")
st.title("Logo Branding Tool")
st.caption("Converts provider logos into your badge format: 356x346 canvas, white circular background, centred logo, PNG output.")

st.sidebar.header("Brand settings")
threshold = st.sidebar.slider("White background removal threshold", 220, 255, 245)
logo_scale = st.sidebar.slider("Logo size inside badge", 0.35, 0.80, 0.62, 0.01)
circle_margin = st.sidebar.slider("Circle margin", 0, 30, 12)

uploaded_files = st.file_uploader(
    "Upload logo files",
    type=["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"],
    accept_multiple_files=True,
)

if uploaded_files:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        in_dir = tmp_path / "in"
        out_dir = tmp_path / "out"
        in_dir.mkdir()
        out_dir.mkdir()

        for f in uploaded_files:
            (in_dir / f.name).write_bytes(f.read())

        outputs = batch_process(
            in_dir,
            out_dir,
            threshold=threshold,
            circle_margin=circle_margin,
            logo_scale=logo_scale,
        )

        st.subheader("Preview")
        cols = st.columns(3)
        for i, out in enumerate(outputs):
            with cols[i % 3]:
                st.image(str(out), caption=out.name, use_container_width=True)
                st.download_button(
                    label=f"Download {out.name}",
                    data=out.read_bytes(),
                    file_name=out.name,
                    mime="image/png",
                )

        zip_path = tmp_path / "branded_logos.zip"
        zip_outputs(out_dir, zip_path)
        st.download_button(
            label="Download all as ZIP",
            data=zip_path.read_bytes(),
            file_name="branded_logos.zip",
            mime="application/zip",
        )
else:
    st.info("Upload one or more provider logos to generate branded PNG badges.")
