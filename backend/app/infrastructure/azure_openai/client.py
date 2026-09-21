"""Azure OpenAI client wrapper producing structured (Pydantic-validated) JSON outputs.

Uses LangChain's AzureChatOpenAI under the hood so it can be composed inside LangGraph
nodes, with tenacity-based retries for resilience against transient API errors.
"""
from __future__ import annotations

from typing import Type, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)


class AzureOpenAIClient:
    """Thin, testable wrapper around Azure OpenAI (GPT-4o) chat completions."""

    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_deployment_gpt4o,
            temperature=0.4,
            timeout=30,
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: Type[TModel]
    ) -> TModel:
        """Invoke the model and parse/validate the response against `schema`.

        Uses LangChain's structured-output binding (function-calling / JSON schema mode)
        so the LLM's response is guaranteed to be shaped like `schema` (or an exception
        is raised and retried).
        """
        structured_llm = self._llm.with_structured_output(schema)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        try:
            result = await structured_llm.ainvoke(messages)
        except Exception as exc:
            logger.error("azure_openai_structured_call_failed", error=str(exc))
            raise
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = await self._llm.ainvoke(messages)
        return response.content if isinstance(response.content, str) else str(response.content)


_client: AzureOpenAIClient | None = None


def get_azure_openai_client() -> AzureOpenAIClient:
    global _client
    if _client is None:
        _client = AzureOpenAIClient()
    return _client
