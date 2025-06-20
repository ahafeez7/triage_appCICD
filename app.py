__import__("pysqlite3")
import sys
import json
import pandas as pd
import streamlit as st
from chroma_patient_store import collection
from reasoning import triage_decision

# SQLite patch (must come after all imports to avoid E402)
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

st.set_page_config(page_title="Enhanced Triage App (5 Levels)", layout="wide")

st.markdown("# 🏥 Patient Triage App Dashboard (5-Level Triage)")

# 📋 Age group filter selector for similar case search
age_group_filter = st.selectbox(
    "📋 Filter similar cases by Age Group:",
    options=["All", "child", "adult", "senior"],
    index=0,
)

uploaded_file = st.file_uploader("Upload patient data (JSON)", type=["json"])
if uploaded_file:
    patients_data = json.load(uploaded_file)
    triage_results = []

    for patient in patients_data:
        vitals = patient["Vitals"]
        symptoms = patient["Symptoms"]
        history = patient["MedicalHistory"]
        patient_id = patient["PatientID"]

        triage_output = triage_decision(
            vitals,
            symptoms,
            history,
            patient_id=patient_id,
            age_group_filter=age_group_filter if age_group_filter != "All" else None,
        )

        triage_results.append(
            {
                "PatientID": patient_id,
                "Triage": triage_output["Triage"],
                "Recommendation": triage_output["Recommendation"],
                "SimilarCases": triage_output.get("SimilarCases", []),
            }
        )

    df = pd.DataFrame(triage_results)
    st.subheader("📊 Triage Results (Table View)")
    st.dataframe(df.drop(columns=["SimilarCases"]), use_container_width=True)

    st.subheader("🔎 Triage Level Summary & Recommendations")
    with st.container():
        st.markdown(
            "<div style='max-height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;'>",
            unsafe_allow_html=True,
        )

        html_content = ""
        triage_colors = {
            "Critical": "red",
            "Emergent": "orange",
            "Urgent": "gold",
            "Semi-Urgent": "blue",
            "Non-Urgent": "green",
        }
        triage_emojis = {
            "Critical": "🚨",
            "Emergent": "⚠️",
            "Urgent": "🔶",
            "Semi-Urgent": "🟦",
            "Non-Urgent": "✅",
        }

        for result in triage_results:
            color = triage_colors.get(result["Triage"], "black")
            emoji = triage_emojis.get(result["Triage"], "")
            html_content += f"<p style='color:{color}; font-weight:bold;'>{emoji} Patient {result['PatientID']}: {result['Triage']}</p>"
            html_content += f"<p style='margin-top: -10px;'><i>Recommendation: {result['Recommendation']}</i></p>"

        st.markdown(html_content, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    csv = df.drop(columns=["SimilarCases"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Triage Results", csv, "triage_results.csv", "text/csv"
    )

    st.subheader("🧑‍⚕️ Patient Details")
    for patient, result in zip(patients_data, triage_results):
        with st.expander(
            f"Patient {result['PatientID']} Details & Triage: {result['Triage']}"
        ):
            st.json(patient)
            st.write(f"**Recommendation:** {result['Recommendation']}")

            similar_cases = result.get("SimilarCases", [])
            if similar_cases:
                st.markdown("**🔁 Similar Past Cases (via ChromaDB):**")
                for i, case in enumerate(similar_cases, 1):
                    anchor_id = f"case_{result['PatientID']}_{i}"
                    st.markdown(f"<a name='{anchor_id}'></a>", unsafe_allow_html=True)
                    st.markdown(
                        f"- [Case {i}](#{anchor_id}): {case}", unsafe_allow_html=True
                    )

    search_id = st.text_input("🔍 Search by Patient ID")
    if search_id:
        filtered = [
            r
            for r in triage_results
            if str(r["PatientID"]).lower() == search_id.lower()
        ]
        st.write("Filtered Results:", filtered)

    st.subheader("📈 Triage Level Counts")
    triage_counts = pd.Series([r["Triage"] for r in triage_results]).value_counts()
    st.bar_chart(triage_counts)
    st.metric("Critical Cases", triage_counts.get("Critical", 0))

    # ----------------------------------------
    # 📊 Real-Time Metadata Analytics
    # ----------------------------------------
    st.subheader("📊 Real-Time Embedding Metadata Analytics")

    try:
        data = collection.get(include=["metadatas"])
        metadatas = data.get("metadatas", [])

        if metadatas:
            df_meta = pd.DataFrame(metadatas)

            # Ensure safe access to all expected columns
            for col in ["age_group", "label", "added"]:
                if col not in df_meta:
                    df_meta[col] = None

            # Safely extract dropdown options
            age_group_options = (
                sorted(df_meta["age_group"].dropna().unique())
                if "age_group" in df_meta
                else []
            )
            label_options = (
                sorted(df_meta["label"].dropna().unique()) if "label" in df_meta else []
            )

            # 🔍 Interactive filtering UI
            col1, col2 = st.columns(2)
            with col1:
                selected_age_group = st.multiselect(
                    "Filter by Age Group", options=age_group_options, default=[]
                )
            with col2:
                selected_label = st.multiselect(
                    "Filter by Label", options=label_options, default=[]
                )

            filtered_meta = df_meta.copy()
            if selected_age_group:
                filtered_meta = filtered_meta[
                    filtered_meta["age_group"].isin(selected_age_group)
                ]
            if selected_label:
                filtered_meta = filtered_meta[
                    filtered_meta["label"].isin(selected_label)
                ]

            with st.expander("📋 Filtered Metadata Table"):
                st.dataframe(filtered_meta)

            st.markdown("### 🔢 Age Group Distribution")
            st.bar_chart(filtered_meta["age_group"].value_counts())

            st.markdown("### 🏷 Label Distribution")
            st.bar_chart(filtered_meta["label"].value_counts())

            if "added" in filtered_meta:
                filtered_meta["added"] = pd.to_datetime(
                    filtered_meta["added"], errors="coerce"
                )
                filtered_meta = filtered_meta.dropna(subset=["added"])
                filtered_meta["date"] = filtered_meta["added"].dt.date
                st.markdown("### 📅 Embedding Timestamps by Day")
                st.line_chart(filtered_meta["date"].value_counts().sort_index())

    except Exception as e:
        st.warning(f"⚠️ Could not load metadata: {e}")
