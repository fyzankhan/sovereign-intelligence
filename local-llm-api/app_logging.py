import asyncio
import uuid

import mysql.connector
from fastapi import APIRouter, HTTPException, Query

from mysql_connection import MySQLConnection

router = APIRouter()


class Logging:
    @staticmethod
    def get_db_connection():
        return MySQLConnection.get_connection()

    @staticmethod
    def save_conversation(conversation_id: str, model_name: str,
                          title: str | None = None):
        connection = None
        cursor = None
        try:
            connection = Logging.get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (conversation_id, title, model_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    model_name = VALUES(model_name),
                    title = COALESCE(title, VALUES(title)),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (conversation_id, title, model_name),
            )
            connection.commit()
        except mysql.connector.Error:
            if connection and connection.is_connected():
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    @staticmethod
    def insert_llm_request(
        request_id: str, conversation_id: str, endpoint: str,
        model_name: str, prompt: str | None, think_enabled: bool,
        status: str, prompt_tokens: int | None = None,
        generated_tokens: int | None = None,
        total_duration_ms: int | None = None,
        load_duration_ms: int | None = None,
        prompt_eval_duration_ms: int | None = None,
        generation_duration_ms: int | None = None,
        tokens_per_second: float | None = None,
        error_message: str | None = None,
    ):
        connection = None
        cursor = None
        try:
            connection = Logging.get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO llm_requests (
                    request_id, conversation_id, endpoint, model_name,
                    prompt, think_enabled, status, prompt_tokens,
                    generated_tokens, total_duration_ms, load_duration_ms,
                    prompt_eval_duration_ms, generation_duration_ms,
                    tokens_per_second, error_message
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (request_id, conversation_id, endpoint, model_name, prompt,
                 think_enabled, status, prompt_tokens, generated_tokens,
                 total_duration_ms, load_duration_ms,
                 prompt_eval_duration_ms, generation_duration_ms,
                 tokens_per_second, error_message),
            )
            connection.commit()
        except mysql.connector.Error:
            if connection and connection.is_connected():
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    @staticmethod
    def insert_benchmark(
        run_name: str, model_name: str, prompt: str, think_enabled: bool,
        prompt_tokens: int | None, generated_tokens: int | None,
        total_duration_ms: int | None, tokens_per_second: float | None,
    ) -> int:
        connection = None
        cursor = None
        try:
            connection = Logging.get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO benchmark_runs (
                    run_name, model_name, prompt, think_enabled,
                    prompt_tokens, generated_tokens,
                    total_duration_ms, tokens_per_second
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (run_name, model_name, prompt, think_enabled, prompt_tokens,
                 generated_tokens, total_duration_ms, tokens_per_second),
            )
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error:
            if connection and connection.is_connected():
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    @staticmethod
    async def run_benchmark(request: dict):
        from chat import MODEL, request_ollama

        run_name = request["run_name"]
        prompt = request["prompt"]
        think_enabled = request.get("think_enabled", False)
        conversation_id = request.get("conversation_id") or str(uuid.uuid4())

        try:
            await asyncio.to_thread(
                Logging.save_conversation, conversation_id, MODEL, prompt[:255]
            )
        except mysql.connector.Error as error:
            raise HTTPException(
                status_code=500,
                detail="Failed to save benchmark conversation",
            ) from error

        data = await request_ollama(
            messages=[{"role": "user", "content": prompt}],
            think=think_enabled, endpoint="benchmarks/run",
            conversation_id=conversation_id, benchmark_run_name=run_name,
        )
        total_duration = data.get("total_duration")
        generated_tokens = data.get("eval_count")
        eval_duration = data.get("eval_duration")
        tokens_per_second = (
            round(generated_tokens * 1_000_000_000 / eval_duration, 2)
            if isinstance(generated_tokens, (int, float))
            and isinstance(eval_duration, (int, float)) and eval_duration > 0
            else None
        )
        return {
            "message": "Benchmark completed and automatically logged",
            "run_name": run_name, "model": data.get("model", MODEL),
            "conversation_id": conversation_id,
            "answer": data["message"]["content"],
            "metrics": {
                "prompt_tokens": data.get("prompt_eval_count"),
                "generated_tokens": generated_tokens,
                "total_duration_ms": (
                    round(total_duration / 1_000_000)
                    if isinstance(total_duration, (int, float)) else None
                ),
                "tokens_per_second": tokens_per_second,
            },
        }

    @staticmethod
    def get_benchmarks(limit: int = Query(default=20, ge=1, le=100),
                       offset: int = Query(default=0, ge=0)):
        connection = None
        cursor = None
        try:
            connection = Logging.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, run_name, model_name, prompt, think_enabled,
                       prompt_tokens, generated_tokens, total_duration_ms,
                       tokens_per_second, created_at
                FROM benchmark_runs ORDER BY id DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cursor.fetchall()
            return {"count": len(rows), "limit": limit,
                    "offset": offset, "results": rows}
        except mysql.connector.Error as error:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve benchmarks from MySQL",
            ) from error
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()


router.add_api_route("/benchmarks/run", Logging.run_benchmark, methods=["POST"])
router.add_api_route("/benchmarks", Logging.get_benchmarks, methods=["GET"])
