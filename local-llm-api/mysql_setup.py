from mysql.connector import Error
from fastapi import APIRouter, HTTPException

from mysql_connection import MySQLConnection

router = APIRouter(prefix="/mysql", tags=["MySQL Table Setup"])


class MySQLSetup:
    @staticmethod
    def sync_table(table_name: str, columns: dict):
        connection = None
        cursor = None
        try:
            connection = MySQLConnection.get_connection(connection_timeout=10)
            cursor = connection.cursor()
            definitions = ", ".join(
                f"`{name}` {definition}"
                for name, definition in columns.items()
            )
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS `{table_name}` ({definitions}) "
                "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
                "COLLATE=utf8mb4_unicode_ci"
            )
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            existing = {row[0] for row in cursor.fetchall()}
            added = []
            for name, definition in columns.items():
                if name not in existing:
                    cursor.execute(
                        f"ALTER TABLE `{table_name}` "
                        f"ADD COLUMN `{name}` {definition}"
                    )
                    added.append(name)
            return {
                "table": table_name,
                "created_or_checked": True,
                "added_columns": added,
                "message": (
                    "Table created or checked successfully."
                    if not added else "Missing columns added successfully."
                ),
            }
        except Error as error:
            raise HTTPException(
                status_code=500,
                detail=f"MySQL setup failed for {table_name}: {error}",
            ) from error
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    @staticmethod
    def sync_benchmark_runs():
        return MySQLSetup.sync_table("benchmark_runs", {
            "id": "BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY",
            "run_name": "VARCHAR(100) NOT NULL",
            "model_name": "VARCHAR(150) NOT NULL",
            "prompt": "TEXT NOT NULL",
            "think_enabled": "BOOLEAN NOT NULL DEFAULT FALSE",
            "prompt_tokens": "INT UNSIGNED NULL",
            "generated_tokens": "INT UNSIGNED NULL",
            "total_duration_ms": "BIGINT UNSIGNED NULL",
            "tokens_per_second": "DECIMAL(10, 2) NULL",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        })

    @staticmethod
    def sync_llm_requests():
        return MySQLSetup.sync_table("llm_requests", {
            "id": "BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY",
            "request_id": "CHAR(36) NULL",
            "conversation_id": "CHAR(36) NULL",
            "endpoint": "VARCHAR(150) NULL",
            "model_name": "VARCHAR(150) NOT NULL",
            "prompt": "TEXT NULL",
            "think_enabled": "BOOLEAN NOT NULL DEFAULT FALSE",
            "status": "VARCHAR(30) NOT NULL DEFAULT 'success'",
            "prompt_tokens": "INT UNSIGNED NULL",
            "generated_tokens": "INT UNSIGNED NULL",
            "total_duration_ms": "BIGINT UNSIGNED NULL",
            "load_duration_ms": "BIGINT UNSIGNED NULL",
            "prompt_eval_duration_ms": "BIGINT UNSIGNED NULL",
            "generation_duration_ms": "BIGINT UNSIGNED NULL",
            "tokens_per_second": "DECIMAL(10, 2) NULL",
            "error_message": "TEXT NULL",
            "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        })

    @staticmethod
    def sync_conversations():
        return MySQLSetup.sync_table("conversations", {
            "id": "BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY",
            "conversation_id": "CHAR(36) NOT NULL UNIQUE",
            "title": "VARCHAR(255) NULL",
            "model_name": "VARCHAR(150) NULL",
            "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        })

    @staticmethod
    def sync_llm_requests_indexes():
        connection = None
        cursor = None
        try:
            connection = MySQLConnection.get_connection(connection_timeout=10)
            cursor = connection.cursor()
            indexes = {
                "idx_llm_requests_request_id": "request_id",
                "idx_llm_requests_conversation_id": "conversation_id",
                "idx_llm_requests_model_name": "model_name",
                "idx_llm_requests_status": "status",
                "idx_llm_requests_created_at": "created_at",
            }
            cursor.execute("SHOW INDEX FROM llm_requests")
            existing = {row[2] for row in cursor.fetchall()}
            added = []
            for index_name, column_name in indexes.items():
                if index_name not in existing:
                    cursor.execute(
                        f"CREATE INDEX `{index_name}` ON `llm_requests` "
                        f"(`{column_name}`)"
                    )
                    added.append(index_name)
            return {"table": "llm_requests", "added_indexes": added,
                    "message": "Indexes checked successfully."}
        except Error as error:
            raise HTTPException(status_code=500,
                                detail=f"Index setup failed: {error}") from error
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()


router.add_api_route("/benchmark-runs/sync", MySQLSetup.sync_benchmark_runs,
                     methods=["POST"])
router.add_api_route("/llm-requests/sync", MySQLSetup.sync_llm_requests,
                     methods=["POST"])
router.add_api_route("/conversations/sync", MySQLSetup.sync_conversations,
                     methods=["POST"])
router.add_api_route("/llm-requests/indexes/sync",
                     MySQLSetup.sync_llm_requests_indexes, methods=["POST"])
