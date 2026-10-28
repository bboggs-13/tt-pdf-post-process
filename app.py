from __future__ import annotations

import hashlib
import io
from pathlib import Path

import streamlit as st

from caption_engine import CaptionJob, analyze_pdf, apply_captions, format_caption

st.set_page_config(page_title="TT Site Visit Photo Captioner", page_icon="📷", layout="wide")

def invalidate_export():
    st.session_state.generated_pdf = None
st.title("TT Site Visit Photo Captioner")
st.caption("Add observation-linked captions to photographs in a post-processed TT report PDF.")
st.info(
    "Only photo pages containing a **Photographs:** heading are edited. Existing photo captions are retained, "
    "and each detected caption can be checked or corrected before export. The uploaded report stays in this app session."
)

uploaded = st.file_uploader("Upload a post-processed site visit report (PDF)", type=["pdf"])

if uploaded:
    pdf_bytes = uploaded.getvalue()
    fingerprint = hashlib.sha256(pdf_bytes).hexdigest()
    if st.session_state.get("fingerprint") != fingerprint:
        report_no, detected_jobs, notes = analyze_pdf(pdf_bytes)
        st.session_state.fingerprint = fingerprint
        st.session_state.source_pdf = pdf_bytes
        st.session_state.jobs = detected_jobs
        st.session_state.report_no = report_no
        st.session_state.notes = notes
        st.session_state.generated_pdf = None
        st.session_state.export_warnings = []

    st.subheader("1. Confirm report and observations")
    report_no = st.text_input("Report number", value=st.session_state.report_no, help="Detected from 'Special Inspection Report #…'; change if needed.", on_change=invalidate_export)
    st.session_state.report_no = report_no.strip()

    notes = st.session_state.notes
    if notes:
        for note in notes:
            st.warning(note)

    jobs: list[CaptionJob] = st.session_state.jobs
    if not jobs:
        st.error("No photos were detected. This app requires embedded photo images on pages headed 'Photographs:'.")
        st.stop()

    st.write(f"Detected **{len(jobs)} photo(s)** across **{len({j.page_index for j in jobs})} photo page(s)**.")
    if any(j.warning for j in jobs):
        st.warning("Some observation links need review. Check every card below before exporting.")

    for i, job in enumerate(jobs):
        with st.container(border=True):
            st.markdown(f"**Page {job.page_number} · Photo {job.photo_number}**")
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                options = ["NCR", "GO", "Skip"]
                default = job.observation_type if job.observation_type in {"NCR", "GO"} else "Skip"
                current_kind = st.selectbox(
                    "Observation type", options, index=options.index(default), key=f"kind_{i}", on_change=invalidate_export
                )
            with c2:
                obs_value = st.text_input(
                    "Observation number", value=job.observation_number, key=f"obs_{i}",
                    help="Enter only the numeric observation identifier, e.g. 1.", on_change=invalidate_export,
                )
            with c3:
                caption_value = st.text_input(
                    "Existing photo caption", value=job.caption, key=f"caption_{i}",
                    help="Preserve or edit the caption text already under the photo.", on_change=invalidate_export,
                )
            if current_kind != "Skip" and report_no.strip() and obs_value.strip():
                preview = format_caption(report_no, current_kind, obs_value.strip(), job.photo_number, caption_value)
                st.caption(f"Preview · {preview}")
            else:
                st.caption("This photo will be skipped until its observation type and number are set.")
            if job.warning:
                st.warning(job.warning)
            jobs[i].observation_type = None if current_kind == "Skip" else current_kind
            jobs[i].observation_number = obs_value.strip()
            jobs[i].caption = caption_value.strip()

    st.subheader("2. Generate reviewed PDF")
    st.caption("Captions are left-aligned beneath their photos. If needed, text size decreases to keep it above the next photo row.")
    if st.button("Apply captions", type="primary"):
        if not report_no.strip():
            st.error("Enter the report number before exporting.")
        else:
            with st.spinner("Applying captions to the photo pages…"):
                output, warnings = apply_captions(pdf_bytes, jobs, report_no.strip())
            st.session_state.generated_pdf = output
            st.session_state.export_warnings = warnings

    if st.session_state.get("generated_pdf"):
        warnings = st.session_state.export_warnings
        if warnings:
            with st.expander(f"Review {len(warnings)} export note(s)", expanded=True):
                for warning in warnings:
                    st.warning(warning)
        else:
            st.success("Captioned PDF is ready. No layout warnings were reported.")
        base = Path(uploaded.name).stem
        st.download_button(
            "Download captioned PDF",
            data=st.session_state.generated_pdf,
            file_name=f"{base}_captioned.pdf",
            mime="application/pdf",
            type="primary",
        )
else:
    st.markdown("#### Workflow")
    st.markdown("1. Upload a post-processed report PDF.\n2. Review detected photo pages, observation types, and caption text.\n3. Apply captions and download a separate PDF copy.")
    st.caption("The source PDF is not overwritten. Non-photo pages are not modified.")
