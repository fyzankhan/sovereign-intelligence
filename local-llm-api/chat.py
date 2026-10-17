
import os
import asyncio
import uuid
from typing import Literal

import httpx
import mysql.connector
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from mysql_connection import MySQLConnection

load_dotenv()

router = APIRouter()

OLLAMA_URL = os.environ["OLLAMA_URL"].rstrip("/")
MODEL = os.environ["OLLAMA_MODEL"]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=20)
    conversation_id: str | None = Field(
        default=None, min_length=1, max_length=36
    )


class ChatResponse(BaseModel):
    model: str
    answer: str
    conversation_id: str


class BenchmarkRequest(BaseModel):
    run_name: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=4000)
    think_enabled: bool = False
    conversation_id: str | None = Field(
        default=None, min_length=1, max_length=36
    )


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db_connection():
    return MySQLConnection.get_connection()


# ==================================================
# CONVERSATIONS
# ==================================================

def save_conversation(
    conversation_id: str,
    model_name: str,
    title: str | None = None,
):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (
                conversation_id, title, model_name
            )
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


# ==================================================
# LLM REQUEST LOGGING
# ==================================================

def insert_llm_request(
    request_id: str,
    conversation_id: str,
    endpoint: str,
    model_name: str,
    prompt: str | None,
    think_enabled: bool,
    status: str,
    prompt_tokens: int | None = None,
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
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO llm_requests (
                request_id, conversation_id, endpoint, model_name,
                prompt, think_enabled, status, prompt_tokens,
                generated_tokens, total_duration_ms, load_duration_ms,
                prompt_eval_duration_ms, generation_duration_ms,
                tokens_per_second, error_message
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                request_id, conversation_id, endpoint, model_name,
                prompt, think_enabled, status, prompt_tokens,
                generated_tokens, total_duration_ms, load_duration_ms,
                prompt_eval_duration_ms, generation_duration_ms,
                tokens_per_second, error_message,
            ),
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


# ==================================================
# BENCHMARK LOGGING
# ==================================================

def insert_benchmark(
    run_name: str,
    model_name: str,
    prompt: str,
    think_enabled: bool,
    prompt_tokens: int | None,
    generated_tokens: int | None,
    total_duration_ms: int | None,
    tokens_per_second: float | None,
) -> int:
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO benchmark_runs (
                run_name, model_name, prompt, think_enabled,
                prompt_tokens, generated_tokens,
                total_duration_ms, tokens_per_second
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_name, model_name, prompt, think_enabled,
                prompt_tokens, generated_tokens,
                total_duration_ms, tokens_per_second,
            ),
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


# ==================================================
# SHARED OLLAMA REQUEST
# ==================================================

async def request_ollama(
    messages: list[dict],
    think: bool = False,
    endpoint: str = "unknown",
    conversation_id: str | None = None,
    benchmark_run_name: str | None = None,
) -> dict:
    request_id = str(uuid.uuid4())

    latest_prompt = next(
        (
            message["content"]
            for message in reversed(messages)
            if message.get("role") == "user"
        ),
        None,
    )

    async def record_request(
        status: str,
        data: dict | None = None,
        error_message: str | None = None,
    ):
        data = data or {}
        eval_count = data.get("eval_count")
        eval_duration = data.get("eval_duration")

        def to_ms(value):
            if isinstance(value, (int, float)):
                return round(value / 1_000_000)
            return None

        tokens_per_second = None

        if (
            isinstance(eval_count, (int, float))
            and isinstance(eval_duration, (int, float))
            and eval_duration > 0
        ):
            tokens_per_second = round(
                eval_count * 1_000_000_000 / eval_duration, 2
            )

        try:
            await asyncio.to_thread(
                insert_llm_request,
                request_id,
                conversation_id,
                endpoint,
                data.get("model", MODEL),
                latest_prompt,
                think,
                status,
                data.get("prompt_eval_count"),
                eval_count,
                to_ms(data.get("total_duration")),
                to_ms(data.get("load_duration")),
                to_ms(data.get("prompt_eval_duration")),
                to_ms(eval_duration),
                tokens_per_second,
                error_message[:4000] if error_message else None,
            )
        except Exception as error:
            print(f"LLM REQUEST LOG ERROR: {error}")

        if status == "success":
            try:
                await asyncio.to_thread(
                    insert_benchmark,
                    (benchmark_run_name or f"auto-{endpoint}")[:100],
                    data.get("model", MODEL),
                    latest_prompt or "",
                    think,
                    data.get("prompt_eval_count"),
                    eval_count,
                    to_ms(data.get("total_duration")),
                    tokens_per_second,
                )
            except Exception as error:
                print(f"AUTOMATIC BENCHMARK INSERT ERROR: {error}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    "stream": False,
                    "think": think,
                },
            )
            response.raise_for_status()
            data = response.json()

        if (
            not isinstance(data.get("message"), dict)
            or not isinstance(data["message"].get("content"), str)
        ):
            raise HTTPException(
                status_code=502,
                detail="Invalid response received from Ollama",
            )

        await record_request("success", data=data)
        return data

    except httpx.TimeoutException as error:
        await record_request("timeout", error_message=str(error))
        raise HTTPException(
            status_code=504, detail="Ollama request timed out"
        ) from error

    except httpx.HTTPStatusError as error:
        await record_request("failed", error_message=str(error))
        raise HTTPException(
            status_code=502, detail="Ollama returned an error"
        ) from error

    except httpx.RequestError as error:
        await record_request("failed", error_message=str(error))
        raise HTTPException(
            status_code=503, detail="Cannot connect to Ollama"
        ) from error

    except HTTPException as error:
        await record_request("failed", error_message=str(error.detail))
        raise

    except ValueError as error:
        await record_request("failed", error_message=str(error))
        raise HTTPException(
            status_code=502, detail="Invalid JSON received from Ollama"
        ) from error


# ==================================================
# CHAT WITHOUT MEMORY
# ==================================================

@router.post("/chat/no-memory", response_model=ChatResponse)
async def chat_no_memory(request: ChatRequest):
    latest_message = request.messages[-1]

    if latest_message.role != "user":
        raise HTTPException(
            status_code=400,
            detail="The last message must be from the user",
        )

    conversation_id = request.conversation_id or str(uuid.uuid4())

    try:
        await asyncio.to_thread(
            save_conversation,
            conversation_id,
            MODEL,
            latest_message.content[:255],
        )
    except mysql.connector.Error as error:
        print(f"CONVERSATION INSERT ERROR: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save conversation to MySQL",
        ) from error

    data = await request_ollama(
        messages=[{"role": "user", "content": latest_message.content}],
        endpoint="chat/no-memory",
        conversation_id=conversation_id,
    )

    return ChatResponse(
        model=data.get("model", MODEL),
        answer=data["message"]["content"],
        conversation_id=conversation_id,
    )


# ==================================================
# CHAT WITH MEMORY
# ==================================================

@router.post("/chat/with-memory", response_model=ChatResponse)
async def chat_with_memory(request: ChatRequest):
    if request.messages[-1].role != "user":
        raise HTTPException(
            status_code=400,
            detail="The last message must be from the user",
        )

    conversation_id = request.conversation_id or str(uuid.uuid4())
    latest_prompt = request.messages[-1].content

    try:
        await asyncio.to_thread(
            save_conversation,
            conversation_id,
            MODEL,
            latest_prompt[:255],
        )
    except mysql.connector.Error as error:
        print(f"CONVERSATION INSERT ERROR: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save conversation to MySQL",
        ) from error

    data = await request_ollama(
        messages=[message.model_dump() for message in request.messages],
        endpoint="chat/with-memory",
        conversation_id=conversation_id,
    )

    return ChatResponse(
        model=data.get("model", MODEL),
        answer=data["message"]["content"],
        conversation_id=conversation_id,
    )


# ==================================================
# RUN BENCHMARK
# ==================================================

@router.post("/benchmarks/run")
async def run_benchmark(request: BenchmarkRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    try:
        await asyncio.to_thread(
            save_conversation,
            conversation_id,
            MODEL,
            request.prompt[:255],
        )
    except mysql.connector.Error as error:
        print(f"CONVERSATION INSERT ERROR: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save benchmark conversation",
        ) from error

    data = await request_ollama(
        messages=[{"role": "user", "content": request.prompt}],
        think=request.think_enabled,
        endpoint="benchmarks/run",
        conversation_id=conversation_id,
        benchmark_run_name=request.run_name,
    )

    total_duration = data.get("total_duration")
    generated_tokens = data.get("eval_count")
    eval_duration = data.get("eval_duration")

    tokens_per_second = None
    if (
        isinstance(generated_tokens, (int, float))
        and isinstance(eval_duration, (int, float))
        and eval_duration > 0
    ):
        tokens_per_second = round(
            generated_tokens * 1_000_000_000 / eval_duration, 2
        )

    return {
        "message": "Benchmark completed and automatically logged",
        "run_name": request.run_name,
        "model": data.get("model", MODEL),
        "conversation_id": conversation_id,
        "answer": data["message"]["content"],
        "metrics": {
            "prompt_tokens": data.get("prompt_eval_count"),
            "generated_tokens": generated_tokens,
            "total_duration_ms": (
                round(total_duration / 1_000_000)
                if isinstance(total_duration, (int, float))
                else None
            ),
            "tokens_per_second": tokens_per_second,
        },
    }


# ==================================================
# GET BENCHMARK HISTORY
# ==================================================

@router.get("/benchmarks")
def get_benchmarks(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id, run_name, model_name, prompt, think_enabled,
                prompt_tokens, generated_tokens, total_duration_ms,
                tokens_per_second, created_at
            FROM benchmark_runs
            ORDER BY id DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )

        rows = cursor.fetchall()

        return {
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "results": rows,
        }

    except mysql.connector.Error as error:
        print(f"BENCHMARK READ ERROR: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve benchmarks from MySQL",
        ) from error

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
