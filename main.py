from openai import OpenAI
from dotenv import load_dotenv
import os

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from cache_manager import save_log

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from datetime import datetime
import pandas as pd

app = FastAPI()

embedding_model = SentenceTransformer(
    "paraphrase-MiniLM-L3-v2"
)

documents = []
document_names = []

rag_folder = "data/rag_docs"
for filename in os.listdir(rag_folder):
    filepath = os.path.join(rag_folder,filename)
    with open(filepath,"r",encoding="utf-8") as file:
        text = file.read()
        documents.append(text)
        document_names.append(filename)


document_embeddings = embedding_model.encode(documents)

dimension = document_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(document_embeddings))


# temporary storage
declarations = []

# request model
class Declaration(BaseModel):
    producer_id: str
    month: str
    declared_quantities_kg: Dict[str, float]

class QuestionRequest(BaseModel):
    question:str

# home route
@app.get("/")
def home():
    return {"message": "GreenPack Service Running"}

# endpoint 1
@app.post("/submit")
def submit(data: Declaration):

    # validation
    for quantity in data.declared_quantities_kg.values():
        if quantity < 0:
            return {"error": "Negative quantity not allowed"}

    # store data
    record = {
        "record_id": str(uuid4()),
        "producer_id": data.producer_id,
        "month": data.month,
        "declared_quantities_kg": data.declared_quantities_kg,
        "timestamp": str(datetime.now())
    }

    declarations.append(record)

    return record

# endpoint 2
@app.get("/summary/{producer_id}/{month}")
def summary(producer_id: str, month: str):

    # find declaration
    declaration = None

    for item in declarations:
        if item["producer_id"] == producer_id and item["month"] == month:
            declaration = item

    if not declaration:
        return {"error": "Declaration not found"}

    # read ERP file
    df = pd.read_csv("data/erp_feed.csv")

    df = df[
        (df["producer_id"] == producer_id)
        & (df["month"] == month)
    ]

    results = []

    for _, row in df.iterrows():

        category = row["category"]

        procured = row["procured_kg"]

        declared = declaration["declared_quantities_kg"][category]

        difference = abs(declared - procured) / procured * 100

        status = "Mismatch" if difference > 5 else "Matched"

        results.append({
            "category": category,
            "declared_kg": declared,
            "procured_kg": procured,
            "difference_percent": round(difference, 2),
            "status": status
        })

    # GROQ prompt
    prompt = f"""
You are an EPR compliance assistant.

Generate a professional 3-5 sentence reconciliation summary.

Reconciliation data:
{results}

Mention:
- matched categories
- mismatched categories
- recommended action
"""
    try:
        completion = client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages= [
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )
        summary_text = completion.choices[0].message.content
    except Exception as e:
        summary_text = f"AI generation failed: {str(e)}"

    return {
        "producer_id": producer_id,
        "month": month,
        "reconciliation": results,
        "summary": summary_text
    }

# endpoint 3

@app.post("/ask")
def ask_question(data:QuestionRequest):
    question = data.question

    #embed user query
    query_embedding = embedding_model.encode([question])

    #search releavent query
    distances,indices = index.search(
        np.array(query_embedding).astype("float32"),
        k=2
    )

    retrieved_docs = []
    for idx in indices[0]:
        retrieved_docs.append(documents[idx])
    best_doc = "\n".join(retrieved_docs)

    source = document_names[indices[0][0]]

    #Rag prompt

    prompt = f"""
You are an EPR compliance assistant.

Answer ONLY using the provided context.

If the context contains related information, explain it clearly.

ONLY SAY:
'I do not know based on the provoided documents.'

when the answer is completly unavailable.

    

context:
{best_doc}

Question:
{question}
"""
    
    try:

        completion = client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages=[
                {
                    "role":"user",
                    "content":prompt
                 }
            ]
        )

        answer = completion.choices[0].message.content

    except Exception:

        answer = (
            "I do not know based on the provided context"
        ) 

    if "I do not know" in answer:
        source= None   
    
    save_log(question,answer,source)

    return{
        "question" : question,
        "answer": answer,
        "source": source
    }