from __future__ import annotations

import io
from pathlib import Path

import streamlit as st

from processor import LogoSettings, batch_zip, load_image_from_bytes, render_badge_from_bytes

st.set_page_config(page_title="Logo Branding Tool v3", layout="wide")
st.title("Logo Branding Tool v3")
st.caption("Updated to match the style reference more closely: exact circle badge, transparent outer area, smaller centred logo.")

with st.sidebar:
    st.header("Default style")
    default_threshold = st.slider("Background removal threshold", 220, 255, 245)
    default_scale = st.slider("Logo scale inside circle", 0.30, 0.70, 0.46, 0.01)
    default_x = st.slider("Horizontal nudge", -60, 60, 0)
    default_y = st.slider("Vertical nudge", -60, 60, 0)
    st.markdown("**Badge spec**")
    st.code("356 x 346 px canvas\n346 px exact circle\n5 px transparent side gutters", language=None)

uploads = st.file_uploader(
    "Upload logos",
    type=["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff", "svg"],
    accept_multiple_files=True,
)

if "file_settings_v3" not in st.session_state:
    st.session_state.file_settings_v3 = {}

def get_file_key(uploaded_file) -> str:
    return f"{uploaded_file.name}-{uploaded_file.size}"

if uploads:
    rendered = []
    cols = st.columns(4)

    for idx, uploaded in enumerate(uploads):
        key = get_file_key(uploaded)
        if key not in st.session_state.file_settings_v3:
            st.session_state.file_settings_v3[key] = {
                "threshold": default_threshold,
                "logo_scale": default_scale,
                "x_offset": default_x,
                "y_offset": default_y,
            }

        data = uploaded.getvalue()

        with cols[idx % 4]:
            st.markdown(f"**{uploaded.name}**")
            try:
                source = load_image_from_bytes(data, uploaded.name)
            except Exception as e:
                st.error(f"Could not open {uploaded.name}: {e}")
                continue

            settings_dict = st.session_state.file_settings_v3[key]

            with st.expander("Adjust", expanded=False):
                settings_dict["threshold"] = st.slider(
                    f"Threshold · {uploaded.name}", 220, 255, settings_dict["threshold"], key=f"th-{key}"
                )
                settings_dict["logo_scale"] = st.slider(
                    f"Scale · {uploaded.name}", 0.30, 0.70, float(settings_dict["logo_scale"]), 0.01, key=f"sc-{key}"
                )
                settings_dict["x_offset"] = st.slider(
                    f"X offset · {uploaded.name}", -60, 60, int(settings_dict["x_offset"]), key=f"x-{key}"
                )
                settings_dict["y_offset"] = st.slider(
                    f"Y offset · {uploaded.name}", -60, 60, int(settings_dict["y_offset"]), key=f"y-{key}"
                )
                st.session_state.file_settings_v3[key] = settings_dict

            settings = LogoSettings(**settings_dict)
            branded = render_badge_from_bytes(data, uploaded.name, settings)

            tab1, tab2 = st.tabs(["Original", "Styled"])
            with tab1:
                st.image(source, use_container_width=True)
            with tab2:
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
                key=f"dl-{key}",
                use_container_width=True,
            )

    if rendered:
        zip_path = Path("/tmp/branded_logos_v3.zip")
        batch_zip(rendered, zip_path)
        st.markdown("---")
        st.download_button(
            "Download all as ZIP",
            data=zip_path.read_bytes(),
            file_name="branded_logos_v3.zip",
            mime="application/zip",
            use_container_width=True,
        )
else:
    st.info("Upload one or more logos to start.")
