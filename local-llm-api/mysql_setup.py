
import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

load_dotenv()

# --------------------------------------------------
# MySQL configuration
# --------------------------------------------------

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "local_llm_lab")

router = APIRouter(prefix="/mysql", tags=["MySQL Table Setup"])


def get_mysql_connection():
    """Connect to the existing MySQL database."""
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        connection_timeout=10,
    )


# --------------------------------------------------
# Shared table/column synchronization
# --------------------------------------------------

def sync_table(table_name: str, columns: dict):
    """
    Create the table if missing.
    Add each missing column if the table already exists.
    Existing columns are not modified or deleted.
    """
    connection = None
    cursor = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # Table and column definitions are internal constants.
        column_definitions = ", ".join(
            f"`{name}` {definition}"
            for name, definition in columns.items()
        )

        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS `{table_name}` "
            f"({column_definitions}) "
            "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
            "COLLATE=utf8mb4_unicode_ci"
        )

        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        existing_columns = {row[0] for row in cursor.fetchall()}

        added_columns = []

        for column_name, definition in columns.items():
            if column_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE `{table_name}` "
                    f"ADD COLUMN `{column_name}` {definition}"
                )
                added_columns.append(column_name)

        return {
            "table": table_name,
            "created_or_checked": True,
            "added_columns": added_columns,
            "message": (
                "Table created or checked successfully."
                if not added_columns
                else "Missing columns added successfully."
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


# --------------------------------------------------
# Table 1: benchmark_runs
# --------------------------------------------------

def sync_benchmark_runs():
    """Create/check benchmark_runs and add missing columns."""
    columns = {
        "id": (
            "BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY"
        ),
        "run_name": "VARCHAR(100) NOT NULL",
        "model_name": "VARCHAR(150) NOT NULL",
        "prompt": "TEXT NOT NULL",
        "think_enabled": "BOOLEAN NOT NULL DEFAULT FALSE",
        "prompt_tokens": "INT UNSIGNED NULL",
        "generated_tokens": "INT UNSIGNED NULL",
        "total_duration_ms": "BIGINT UNSIGNED NULL",
        "tokens_per_second": "DECIMAL(10, 2) NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    return sync_table("benchmark_runs", columns)


@router.post("/benchmark-runs/sync")
def sync_benchmark_runs_endpoint():
    """Check/create benchmark_runs and add missing columns."""
    return sync_benchmark_runs()


# --------------------------------------------------
# Add more tables below using the same pattern.
#
# For each new table:
# 1. Create sync_<table>() with its column definitions.
# 2. Add a POST endpoint that calls that method.
# --------------------------------------------------



# --------------------------------------------------
# Table 2: llm_requests
# --------------------------------------------------

def sync_llm_requests():
    """Create/check llm_requests and add missing columns."""

    columns = {
        "id": (
            "BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY"
        ),
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
    }

    return sync_table("llm_requests", columns)


@router.post("/llm-requests/sync")
def sync_llm_requests_endpoint():
    """Check/create llm_requests and add missing columns."""
    return sync_llm_requests()


# --------------------------------------------------
# Table 3: conversations
# --------------------------------------------------

def sync_conversations():
    """Create/check conversations and add missing columns."""

    columns = {
        "id": "BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY",
        "conversation_id": "CHAR(36) NOT NULL UNIQUE",
        "title": "VARCHAR(255) NULL",
        "model_name": "VARCHAR(150) NULL",
        "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    }

    return sync_table("conversations", columns)


@router.post("/conversations/sync")
def sync_conversations_endpoint():
    """Check/create conversations and add missing columns."""
    return sync_conversations()

# --------------------------------------------------
# Indexes: llm_requests
# --------------------------------------------------

def sync_llm_requests_indexes():
    connection = None
    cursor = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        indexes = {
            "idx_llm_requests_request_id": "request_id",
            "idx_llm_requests_conversation_id": "conversation_id",
            "idx_llm_requests_model_name": "model_name",
            "idx_llm_requests_status": "status",
            "idx_llm_requests_created_at": "created_at",
        }

        cursor.execute("SHOW INDEX FROM llm_requests")
        existing_indexes = {row[2] for row in cursor.fetchall()}

        added_indexes = []

        for index_name, column_name in indexes.items():
            if index_name not in existing_indexes:
                cursor.execute(
                    f"CREATE INDEX `{index_name}` "
                    f"ON `llm_requests` (`{column_name}`)"
                )
                added_indexes.append(index_name)

        return {
            "table": "llm_requests",
            "added_indexes": added_indexes,
            "message": "Indexes checked successfully.",
        }

    except Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Index setup failed: {error}",
        ) from error

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@router.post("/llm-requests/indexes/sync")
def sync_llm_requests_indexes_endpoint():
    return sync_llm_requests_indexes()