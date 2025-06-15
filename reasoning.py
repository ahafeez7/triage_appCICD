# reasoning.py

from datetime import datetime
from chroma_patient_store import query_similar_cases, add_patient_embedding


def triage_decision(vitals, symptoms, history, patient_id="temp", age_group_filter=None):
    """
    Rule-based triage with vector embedding and age-group-based filtering of similar cases.
    """

    age_group = "unknown"
    if "Age" in vitals:
        age = vitals["Age"]
        if age < 18:
            age_group = "child"
        elif age < 65:
            age_group = "adult"
        else:
            age_group = "senior"

    metadata = {
        "label": "triaged",
        "added": datetime.utcnow().isoformat(),
        "age_group": age_group
    }

    add_patient_embedding(
        patient_id=patient_id,
        vitals=vitals,
        symptoms=symptoms,
        history=history,
        metadata=metadata
    )

    similar_cases = query_similar_cases(
        vitals=vitals,
        symptoms=symptoms,
        history=history,
        top_k=3,
        age_group_filter=age_group_filter or age_group
    )

    triage_rules = [
        {
            "condition": lambda v, s: "chest pain" in s or "shortness of breath" in s,
            "Triage": "Critical",
            "Recommendation": "Immediate medical attention required. Call emergency services or send to ER."
        },
        {
            "condition": lambda v, s: v["BP"] < 90 or v["HR"] > 130,
            "Triage": "Emergent",
            "Recommendation": "Seek urgent care within 15 minutes."
        },
        {
            "condition": lambda v, s: "fever" in s or v["Temp"] > 38,
            "Triage": "Urgent",
            "Recommendation": "Prompt medical evaluation advised. See doctor within 1 hour."
        },
        {
            "condition": lambda v, s: "dizziness" in s or "fatigue" in s,
            "Triage": "Semi-Urgent",
            "Recommendation": "Monitor symptoms. Visit primary care within 2-4 hours if needed."
        },
    ]

    for rule in triage_rules:
        if rule["condition"](vitals, symptoms):
            return {
                "Triage": rule["Triage"],
                "Recommendation": rule["Recommendation"],
                "SimilarCases": similar_cases
            }

    return {
        "Triage": "Non-Urgent",
        "Recommendation": "Routine care. Book a follow-up in 1-2 weeks if needed.",
        "SimilarCases": similar_cases
    }
