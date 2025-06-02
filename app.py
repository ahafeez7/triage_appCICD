import streamlit as st
import json
import pandas as pd
from reasoning import triage_decision

st.set_page_config(page_title="Enhanced Triage App (5 Levels)", layout="wide")

st.markdown("# 🏥 Patient Triage App Dashboard (5-Level Triage)")

uploaded_file = st.file_uploader("Upload patient data (JSON)", type=["json"])
if uploaded_file:
    patients_data = json.load(uploaded_file)
    triage_results = []

    for patient in patients_data:
        vitals = patient["Vitals"]
        symptoms = patient["Symptoms"]
        history = patient["MedicalHistory"]

        triage_output = triage_decision(vitals, symptoms, history)
        triage_results.append({
            "PatientID": patient["PatientID"],
            "Triage": triage_output["Triage"],
            "Recommendation": triage_output["Recommendation"]
        })

    # Display triage results as DataFrame
    df = pd.DataFrame(triage_results)
    st.subheader("📊 Triage Results (Table View)")
    st.dataframe(df, use_container_width=True)

    # Color-coded triage level summary with scrolling container
    st.subheader("🔎 Triage Level Summary & Recommendations")
    with st.container():
        st.markdown("""
        <div style='max-height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;'>
        """, unsafe_allow_html=True)

        html_content = ""
        triage_colors = {
            "Critical": "red",
            "Emergent": "orange",
            "Urgent": "gold",
            "Semi-Urgent": "blue",
            "Non-Urgent": "green"
        }
        triage_emojis = {
            "Critical": "🚨",
            "Emergent": "⚠️",
            "Urgent": "🔶",
            "Semi-Urgent": "🟦",
            "Non-Urgent": "✅"
        }

        for result in triage_results:
            color = triage_colors.get(result["Triage"], "black")
            emoji = triage_emojis.get(result["Triage"], "")
            html_content += f"<p style='color:{color}; font-weight:bold;'>{emoji} Patient {result['PatientID']}: {result['Triage']}</p>"
            html_content += f"<p style='margin-top: -10px;'><i>Recommendation: {result['Recommendation']}</i></p>"

        st.markdown(html_content, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Download results as CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Triage Results", csv, "triage_results.csv", "text/csv")

    # Patient details preview
    st.subheader("🧑‍⚕️ Patient Details")
    for patient, result in zip(patients_data, triage_results):
        with st.expander(f"Patient {result['PatientID']} Details & Triage: {result['Triage']}"):
            st.json(patient)
            st.write(f"**Recommendation:** {result['Recommendation']}")

    # Search / filter functionality
    search_id = st.text_input("🔍 Search by Patient ID")
    if search_id:
        filtered = [r for r in triage_results if str(r["PatientID"]) == search_id]
        st.write("Filtered Results:", filtered)

    # Charts for triage summary
    st.subheader("📈 Triage Level Counts")
    triage_counts = pd.Series([r["Triage"] for r in triage_results]).value_counts()
    st.bar_chart(triage_counts)
    st.metric("Critical Cases", triage_counts.get("Critical", 0))
