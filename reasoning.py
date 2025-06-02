def triage_decision(vitals, symptoms, history):
    # Define triage criteria as a list of dictionaries (rules)
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

    # Check each rule in order
    for rule in triage_rules:
        if rule["condition"](vitals, symptoms):
            return {
                "Triage": rule["Triage"],
                "Recommendation": rule["Recommendation"]
            }

    # Default fallback
    return {
        "Triage": "Non-Urgent",
        "Recommendation": "Routine care. Book a follow-up in 1-2 weeks if needed."
    }
