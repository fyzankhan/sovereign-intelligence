
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv

load_dotenv()


class ChromaConnection:
    @staticmethod
    def get_connection():
        chroma_path = os.getenv("CHROMA_PATH")

        if chroma_path:
            path = Path(chroma_path)
            if not path.is_absolute():
                path = Path(__file__).resolve().parent / path
        else:
            path = Path(__file__).resolve().parent / "chroma_data"

        path.mkdir(parents=True, exist_ok=True)

        return chromadb.PersistentClient(
            path=str(path.resolve())
        )
