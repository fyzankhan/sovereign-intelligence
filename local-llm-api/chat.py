from __future__ import annotations

import asyncio
import os
import uuid

import httpx
import mysql.connector
from fastapi import APIRouter, HTTPException

from app_logging import Logging

router = APIRouter()


class Chat:
    OLLAMA_URL = os.environ["OLLAMA_URL"].rstrip("/")
    MODEL = os.environ["OLLAMA_MODEL"]

    @staticmethod
    async def request_ollama(
        messages: list[dict], think: bool = False,
        endpoint: str = "unknown", conversation_id: str | None = None,
        benchmark_run_name: str | None = None,
    ) -> dict:
        request_id = str(uuid.uuid4())
        latest_prompt = next(
            (m["content"] for m in reversed(messages)
             if m.get("role") == "user"), None
        )

        async def record_request(status: str, data: dict | None = None,
                                 error_message: str | None = None):
            data = data or {}
            eval_count = data.get("eval_count")
            eval_duration = data.get("eval_duration")

            def to_ms(value):
                return round(value / 1_000_000) if isinstance(value, (int, float)) else None

            tokens_per_second = (
                round(eval_count * 1_000_000_000 / eval_duration, 2)
                if isinstance(eval_count, (int, float))
                and isinstance(eval_duration, (int, float)) and eval_duration > 0
                else None
            )
            try:
                await asyncio.to_thread(
                    Logging.insert_llm_request, request_id, conversation_id,
                    endpoint, data.get("model", Chat.MODEL), latest_prompt,
                    think, status, data.get("prompt_eval_count"), eval_count,
                    to_ms(data.get("total_duration")),
                    to_ms(data.get("load_duration")),
                    to_ms(data.get("prompt_eval_duration")),
                    to_ms(eval_duration), tokens_per_second,
                    error_message[:4000] if error_message else None,
                )
            except Exception as error:
                print(f"LLM REQUEST LOG ERROR: {error}")

            if status == "success":
                try:
                    await asyncio.to_thread(
                        Logging.insert_benchmark,
                        (benchmark_run_name or f"auto-{endpoint}")[:100],
                        data.get("model", Chat.MODEL), latest_prompt or "",
                        think, data.get("prompt_eval_count"), eval_count,
                        to_ms(data.get("total_duration")), tokens_per_second,
                    )
                except Exception as error:
                    print(f"AUTOMATIC BENCHMARK INSERT ERROR: {error}")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{Chat.OLLAMA_URL}/api/chat",
                    json={"model": Chat.MODEL, "messages": messages,
                          "stream": False, "think": think},
                )
                response.raise_for_status()
                data = response.json()
            if (not isinstance(data.get("message"), dict)
                    or not isinstance(data["message"].get("content"), str)):
                raise HTTPException(status_code=502,
                                    detail="Invalid response received from Ollama")
            await record_request("success", data=data)
            return data
        except httpx.TimeoutException as error:
            await record_request("timeout", error_message=str(error))
            raise HTTPException(status_code=504,
                                detail="Ollama request timed out") from error
        except httpx.HTTPStatusError as error:
            await record_request("failed", error_message=str(error))
            raise HTTPException(status_code=502,
                                detail="Ollama returned an error") from error
        except httpx.RequestError as error:
            await record_request("failed", error_message=str(error))
            raise HTTPException(status_code=503,
                                detail="Cannot connect to Ollama") from error
        except HTTPException as error:
            await record_request("failed", error_message=str(error.detail))
            raise
        except ValueError as error:
            await record_request("failed", error_message=str(error))
            raise HTTPException(status_code=502,
                                detail="Invalid JSON received from Ollama") from error

    @staticmethod
    async def chat_no_memory(request: dict):
        messages = request["messages"]
        latest = messages[-1]
        if latest["role"] != "user":
            raise HTTPException(status_code=400,
                                detail="The last message must be from the user")
        conversation_id = request.get("conversation_id") or str(uuid.uuid4())
        try:
            await asyncio.to_thread(Logging.save_conversation, conversation_id,
                                    Chat.MODEL, latest["content"][:255])
        except mysql.connector.Error as error:
            raise HTTPException(status_code=500,
                                detail="Failed to save conversation to MySQL") from error
        data = await Chat.request_ollama(
            [{"role": "user", "content": latest["content"]}],
            endpoint="chat/no-memory", conversation_id=conversation_id,
        )
        return {"model": data.get("model", Chat.MODEL),
                "answer": data["message"]["content"],
                "conversation_id": conversation_id}

    @staticmethod
    async def chat_with_memory(request: dict):
        messages = request["messages"]
        if messages[-1]["role"] != "user":
            raise HTTPException(status_code=400,
                                detail="The last message must be from the user")
        conversation_id = request.get("conversation_id") or str(uuid.uuid4())
        prompt = messages[-1]["content"]
        try:
            await asyncio.to_thread(Logging.save_conversation, conversation_id,
                                    Chat.MODEL, prompt[:255])
        except mysql.connector.Error as error:
            raise HTTPException(status_code=500,
                                detail="Failed to save conversation to MySQL") from error
        data = await Chat.request_ollama(
            messages,
            endpoint="chat/with-memory", conversation_id=conversation_id,
        )
        return {"model": data.get("model", Chat.MODEL),
                "answer": data["message"]["content"],
                "conversation_id": conversation_id}


router.add_api_route("/chat/no-memory", Chat.chat_no_memory,
                     methods=["POST"])
router.add_api_route("/chat/with-memory", Chat.chat_with_memory,
                     methods=["POST"])
