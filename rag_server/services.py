import chromadb
from sentence_transformers import SentenceTransformer
from pdfminer.high_level import extract_text
from docx import Document
import os
# import asyncio
import uuid  # To generate a unique ID for each document
import logging
from fastapi import HTTPException

logging.basicConfig(level=logging.DEBUG)


# Initialize ChromaDB and embeddings model
chroma_client = chromadb.PersistentClient("chromadb_store")
chroma_collection = chroma_client.get_or_create_collection("document_embeddings")
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

async def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return extract_text(file_path)
    elif ext == ".docx":
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    elif ext == ".txt":
        with open(file_path, "r") as file:
            return file.read()
    else:
        raise ValueError("Unsupported file format")


async def process_document(file_path):
    text_content = await extract_text_from_file(file_path)
    embedding = embedding_model.encode(text_content)
    
    # Generate a unique ID for this document
    document_id = str(uuid.uuid4())
    
    # Store the embedding, text content, and ID in ChromaDB
    chroma_collection.add(
        ids=[document_id],
        embeddings=[embedding],
        metadatas={"content": text_content}
    )


async def query_documents(query_text):
    try:
        query_embedding = embedding_model.encode(query_text)
        
        logging.debug(f"Query embedding generated: {query_embedding}")

        # Query the ChromaDB collection
        results = chroma_collection.query(query_embeddings=[query_embedding], n_results=5)
        
        logging.debug(f"Raw query results: {results}")
        
        # Check if the expected 'metadatas' key is present in the results
        metadatas = results.get("metadatas", [])
        
        if not metadatas:
            raise ValueError("No metadata found in query results")
        
        # Extract the relevant text from the metadata
        relevant_texts = [doc[0].get("content", "") for doc in metadatas if doc]
        
        # Concatenate the top 3 documents for response context
        response_text = "\n\n".join(relevant_texts[:3])
        
        return response_text

    except Exception as e:
        logging.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")