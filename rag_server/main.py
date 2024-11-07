from fastapi import FastAPI, File, UploadFile, HTTPException
from services import process_document, query_documents
from models import QueryRequest, QueryResponse
import uvicorn
import os

# Initialize FastAPI app
app = FastAPI()

# Ensure the documents directory exists
DOCUMENTS_DIR = "documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Endpoint to ingest and store a document
@app.post("/ingest/")
async def ingest_document(file: UploadFile = File(...)):
    try:
        # Save the uploaded file to the documents directory
        file_path = os.path.join(DOCUMENTS_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process the document and store embeddings in ChromaDB
        await process_document(file_path)
        return {"message": f"Document '{file.filename}' ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {e}")

# Endpoint to query documents based on user input
@app.post("/query/", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    try:
        # Query the document embeddings and return the result
        response_text = await query_documents(request.query)
        return QueryResponse(answer=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

# Run the app only if this script is the main entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
