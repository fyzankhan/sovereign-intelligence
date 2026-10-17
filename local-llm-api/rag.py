
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chroma_connection import ChromaConnection

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


class DocumentCreate(BaseModel):
    document_id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    text: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None


def get_collection():
    return ChromaConnection.get_connection().get_or_create_collection(
        name="documents"
    )


@router.post("/documents")
def create_document(document: DocumentCreate):
    collection = get_collection()

    collection.upsert(
        ids=[document.document_id],
        documents=[document.text],
        metadatas=[document.metadata],
    )

    return {
        "message": "Document saved",
        "document_id": document.document_id,
    }



@router.get("/documents")
def list_documents(limit: int = 20, offset: int = 0):
    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100",
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="Offset cannot be negative",
        )

    collection = get_collection()

    result = collection.get(
        limit=limit,
        offset=offset,
        include=["documents", "metadatas"],
    )

    return {
        "count": len(result["ids"]),
        "documents": [
            {
                "document_id": document_id,
                "text": text,
                "metadata": metadata,
            }
            for document_id, text, metadata in zip(
                result["ids"],
                result["documents"],
                result["metadatas"],
            )
        ],
    }



@router.get("/documents/{document_id}")
def get_document(document_id: str):
    collection = get_collection()

    result = collection.get(
        ids=[document_id],
        include=["documents", "metadatas"],
    )

    if not result["ids"]:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "document_id": result["ids"][0],
        "text": result["documents"][0],
        "metadata": result["metadatas"][0],
    }



@router.put("/documents/{document_id}")
def update_document(
    document_id: str,
    document: DocumentUpdate,
):
    collection = get_collection()

    existing = collection.get(ids=[document_id])

    if not existing["ids"]:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    metadata = (
        document.metadata
        if document.metadata is not None
        else (existing["metadatas"][0] or {})
    )

    collection.update(
        ids=[document_id],
        documents=[document.text],
        metadatas=[metadata],
    )

    return {
        "message": "Document updated",
        "document_id": document_id,
    }



@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    collection = get_collection()

    existing = collection.get(ids=[document_id])

    if not existing["ids"]:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    collection.delete(ids=[document_id])

    return {
        "message": "Document deleted",
        "document_id": document_id,
    }
