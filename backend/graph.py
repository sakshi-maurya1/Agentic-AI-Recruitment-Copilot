from rag.retriever import get_retriever


def search_resume(question: str):

    retriever = get_retriever()

    docs = retriever.invoke(question)

    return "\n\n".join(
        doc.page_content
        for doc in docs
    )