from typing import Any

from fastapi import APIRouter, HTTPException

from chroma_connection import ChromaConnection

router = APIRouter(prefix="/rag", tags=["RAG"])


class RAG:
    @staticmethod
    def get_collection():
        return ChromaConnection.get_connection().get_or_create_collection(
            name="documents"
        )

    @staticmethod
    def create_document(document: dict):
        document_id = document["document_id"]
        text = document["text"]
        metadata: dict[str, Any] = document.get("metadata", {})
        collection = RAG.get_collection()
        collection.upsert(ids=[document_id], documents=[text], metadatas=[metadata])
        return {"message": "Document saved", "document_id": document_id}

    @staticmethod
    def list_documents(limit: int = 20, offset: int = 0):
        if not 1 <= limit <= 100:
            raise HTTPException(status_code=400,
                                detail="Limit must be between 1 and 100")
        if offset < 0:
            raise HTTPException(status_code=400,
                                detail="Offset cannot be negative")
        result = RAG.get_collection().get(
            limit=limit, offset=offset, include=["documents", "metadatas"]
        )
        return {
            "count": len(result["ids"]),
            "documents": [
                {"document_id": document_id, "text": text, "metadata": metadata}
                for document_id, text, metadata in zip(
                    result["ids"], result["documents"], result["metadatas"]
                )
            ],
        }

    @staticmethod
    def get_document(document_id: str):
        result = RAG.get_collection().get(
            ids=[document_id], include=["documents", "metadatas"]
        )
        if not result["ids"]:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"document_id": result["ids"][0], "text": result["documents"][0],
                "metadata": result["metadatas"][0]}

    @staticmethod
    def update_document(document_id: str, document: dict):
        collection = RAG.get_collection()
        existing = collection.get(ids=[document_id], include=["metadatas"])
        if not existing["ids"]:
            raise HTTPException(status_code=404, detail="Document not found")
        metadata = document.get("metadata")
        if metadata is None:
            metadata = existing["metadatas"][0] or {}
        collection.update(ids=[document_id], documents=[document["text"]],
                          metadatas=[metadata])
        return {"message": "Document updated", "document_id": document_id}

    @staticmethod
    def delete_document(document_id: str):
        collection = RAG.get_collection()
        existing = collection.get(ids=[document_id])
        if not existing["ids"]:
            raise HTTPException(status_code=404, detail="Document not found")
        collection.delete(ids=[document_id])
        return {"message": "Document deleted", "document_id": document_id}


router.add_api_route("/documents", RAG.create_document, methods=["POST"])
router.add_api_route("/documents", RAG.list_documents, methods=["GET"])
router.add_api_route("/documents/{document_id}", RAG.get_document, methods=["GET"])
router.add_api_route("/documents/{document_id}", RAG.update_document, methods=["PUT"])
router.add_api_route("/documents/{document_id}", RAG.delete_document, methods=["DELETE"])
