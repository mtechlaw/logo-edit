from __future__ import annotations

import io
from pathlib import Path

import streamlit as st
from PIL import Image

from processor import LogoSettings, batch_zip, load_image_from_bytes, render_badge_from_bytes

st.set_page_config(page_title="Logo Branding Tool Pro", layout="wide")
st.title("Logo Branding Tool Pro")
st.caption("Upload provider logos, adjust them visually, and export branded PNG badges.")

with st.sidebar:
    st.header("Global defaults")
    default_threshold = st.slider("Background removal threshold", 220, 255, 245)
    default_scale = st.slider("Logo size", 0.35, 0.82, 0.62, 0.01)
    default_margin = st.slider("Circle margin", 0, 30, 12)
    default_x = st.slider("Horizontal nudge", -80, 80, 0)
    default_y = st.slider("Vertical nudge", -80, 80, 0)
    st.markdown("---")
    st.write("Badge output")
    st.code("356 x 346 px\nWhite circular background\nTransparent outside area", language=None)

uploads = st.file_uploader(
    "Drop or browse logo files",
    type=["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff", "svg"],
    accept_multiple_files=True,
)

if "file_settings" not in st.session_state:
    st.session_state.file_settings = {}

def get_file_key(uploaded_file) -> str:
    return f"{uploaded_file.name}-{uploaded_file.size}"

if uploads:
    rendered = []
    preview_columns = 4
    cols = st.columns(preview_columns)

    for idx, uploaded in enumerate(uploads):
        file_key = get_file_key(uploaded)
        if file_key not in st.session_state.file_settings:
            st.session_state.file_settings[file_key] = {
                "threshold": default_threshold,
                "logo_scale": default_scale,
                "circle_margin": default_margin,
                "x_offset": default_x,
                "y_offset": default_y,
            }

        with cols[idx % preview_columns]:
            data = uploaded.getvalue()

            try:
                source = load_image_from_bytes(data, uploaded.name)
            except Exception as e:
                st.error(f"Could not open {uploaded.name}: {e}")
                continue

            st.markdown(f"**{uploaded.name}**")
            before_tab, after_tab = st.tabs(["Original", "Branded"])
            with before_tab:
                st.image(source, use_container_width=True)

            with st.expander("Edit settings", expanded=False):
                settings_dict = st.session_state.file_settings[file_key]
                settings_dict["threshold"] = st.slider(
                    f"Threshold · {uploaded.name}", 220, 255, settings_dict["threshold"], key=f"th-{file_key}"
                )
                settings_dict["logo_scale"] = st.slider(
                    f"Scale · {uploaded.name}", 0.35, 0.82, float(settings_dict["logo_scale"]), 0.01, key=f"sc-{file_key}"
                )
                settings_dict["circle_margin"] = st.slider(
                    f"Margin · {uploaded.name}", 0, 30, int(settings_dict["circle_margin"]), key=f"mg-{file_key}"
                )
                settings_dict["x_offset"] = st.slider(
                    f"X offset · {uploaded.name}", -80, 80, int(settings_dict["x_offset"]), key=f"x-{file_key}"
                )
                settings_dict["y_offset"] = st.slider(
                    f"Y offset · {uploaded.name}", -80, 80, int(settings_dict["y_offset"]), key=f"y-{file_key}"
                )
                st.session_state.file_settings[file_key] = settings_dict

            settings = LogoSettings(**st.session_state.file_settings[file_key])
            branded = render_badge_from_bytes(data, uploaded.name, settings)

            with after_tab:
                st.image(branded, use_container_width=True)

            out_name = f"{Path(uploaded.name).stem}_branded.png"
            buf = io.BytesIO()
            branded.save(buf, format="PNG")
            rendered.append((uploaded.name, branded))
            st.download_button(
                "Download PNG",
                data=buf.getvalue(),
                file_name=out_name,
                mime="image/png",
                key=f"dl-{file_key}",
                use_container_width=True,
            )

    if rendered:
        zip_path = Path("/tmp/branded_logos.zip")
        batch_zip(rendered, zip_path)
        st.markdown("---")
        st.download_button(
            "Download all as ZIP",
            data=zip_path.read_bytes(),
            file_name="branded_logos.zip",
            mime="application/zip",
            use_container_width=True,
        )
else:
    st.info("Upload one or more files to start. SVG, PNG, JPG, WEBP, BMP and TIFF are supported.")
