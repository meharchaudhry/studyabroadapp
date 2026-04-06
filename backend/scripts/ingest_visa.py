import os
import glob
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def main():
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "visa_docs")
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma_db")
    
    print(f"Loading authentic visa documents from {docs_dir}")
    
    # Use plain Python file reading to avoid needing "unstructured" package
    documents = []
    for filepath in glob.glob(os.path.join(docs_dir, "*.md")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        source_name = os.path.basename(filepath)
        # Extract country from filename
        country = "Unknown"
        if "UKVI" in source_name or "UK" in source_name:
            country = "UK"
        elif "USCIS" in source_name or "F1" in source_name:
            country = "US"
        elif "IRCC" in source_name or "Canada" in source_name:
            country = "Canada"
            
        documents.append(Document(
            page_content=content,
            metadata={"source": source_name, "country": country}
        ))

    if not documents:
        print("⚠️  No .md files found. Run scripts/scrape_visa.py first.")
        return
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    
    print(f"Embedding {len(docs)} visa policy chunks into ChromaDB...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Store locally in chroma_db
    Chroma.from_documents(
        documents=docs, 
        embedding=embeddings, 
        persist_directory=db_dir
    )
    print(f"✅ Ingested {len(docs)} chunks from {len(documents)} visa docs into ChromaDB at {db_dir}")

if __name__ == "__main__":
    main()
