# chroma_patient_store.py

import chromadb
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Initialize ChromaDB Persistent Client
client = chromadb.PersistentClient(path="./chroma_store")
collection = client.get_or_create_collection(name="patients")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def _build_text(vitals, symptoms, history):
    """
    Combine structured patient input into a single string for embedding.
    """
    return f"Vitals: {vitals}, Symptoms: {symptoms}, History: {history}"

def embedding_exists(patient_id):
    """
    Check if a patient ID already exists in the collection.
    """
    try:
        result = collection.get(ids=[str(patient_id)], include=["documents"])
        return len(result.get("ids", [])) > 0
    except:
        return False

def add_patient_embedding(patient_id, vitals, symptoms, history, metadata=None):
    """
    Embed and store a patient's data with optional metadata.
    Avoids duplicates by checking PatientID.
    """
    if embedding_exists(patient_id):
        return  # Skip duplicate

    text = _build_text(vitals, symptoms, history)
    embedding = model.encode(text).tolist()

    # Generate default metadata if not supplied
    if metadata is None:
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
            "added": datetime.utcnow().isoformat(),
            "label": "triaged",
            "age_group": age_group
        }

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[str(patient_id)],
        metadatas=[metadata]
    )

def query_similar_cases(vitals, symptoms, history, top_k=3, age_group_filter=None):
    """
    Query ChromaDB for the top-k most similar patient cases.
    Optionally filter by age group metadata.
    """
    text = _build_text(vitals, symptoms, history)
    query_embedding = model.encode(text).tolist()

    # Metadata-based filter (e.g., age_group = 'senior')
    where_filter = {"age_group": age_group_filter} if age_group_filter else {}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter
    )

    return results["documents"][0] if results["documents"] else []