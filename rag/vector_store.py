import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

RESUME_VECTOR_DB = "data/resume_vectorstore"

JD_VECTOR_DB = "data/jd_vectorstore"

def create_vector_store(documents, document_type: str):

    if document_type == "resume":
        vector_db_path = RESUME_VECTOR_DB
    else:
        vector_db_path = JD_VECTOR_DB

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunked_documents = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

    if os.path.exists(vector_db_path):

        db = FAISS.load_local(
            vector_db_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

        db.add_documents(chunked_documents)

    else:

        db = FAISS.from_documents(
            chunked_documents,
            embeddings
        )

    db.save_local(vector_db_path)

    return db
