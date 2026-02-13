from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from pydantic_ai import Agent, DeferredToolRequests, Tool

from .. import constants as cs
from .. import exceptions as ex
from .. import logs as ls
from ..config import ModelConfig, settings
from ..prompts import (
    CYPHER_SYSTEM_PROMPT,
    LOCAL_CYPHER_SYSTEM_PROMPT,
    build_rag_orchestrator_prompt,
)
from ..providers.base import get_provider_from_config

if TYPE_CHECKING:
    from pydantic_ai.models import Model


def _create_provider_model(config: ModelConfig) -> Model:
    provider = get_provider_from_config(config)
    return provider.create_model(config.model_id)


def _clean_cypher_response(response_text: str) -> str:
    """Extract valid Cypher query from LLM response.

    Handles responses where the LLM adds explanatory text after the query.
    Extracts only the lines that are part of the Cypher query itself.
    """
    query = response_text.strip().replace(cs.CYPHER_BACKTICK, "")
    if query.startswith(cs.CYPHER_PREFIX):
        query = query[len(cs.CYPHER_PREFIX) :].strip()

    lines = query.split("\n")
    cypher_lines = []

    cypher_keywords = {
        "MATCH",
        "WHERE",
        "RETURN",
        "WITH",
        "OPTIONAL",
        "UNWIND",
        "CREATE",
        "MERGE",
        "DELETE",
        "SET",
        "REMOVE",
        "ORDER",
        "SKIP",
        "LIMIT",
        "UNION",
    }

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        first_word = stripped.split()[0].upper() if stripped.split() else ""

        if any(
            stripped.startswith(word)
            for word in [
                "Alternatively",
                "Note:",
                "Note that",
                "This query",
                "You can also",
                "Explanation:",
                "This will",
            ]
        ):
            break

        if (
            first_word in cypher_keywords
            or stripped.startswith("(")
            or stripped.startswith("AND ")
            or stripped.startswith("OR ")
            or cypher_lines
        ):
            cypher_lines.append(stripped)
        elif not cypher_lines:
            cypher_lines.append(stripped)

    result = "\n".join(cypher_lines)

    if not result.endswith(cs.CYPHER_SEMICOLON):
        result += cs.CYPHER_SEMICOLON

    return result


class CypherGenerator:
    def __init__(self) -> None:
        try:
            config = settings.active_cypher_config
            llm = _create_provider_model(config)

            system_prompt = (
                LOCAL_CYPHER_SYSTEM_PROMPT
                if config.provider == cs.Provider.OLLAMA
                else CYPHER_SYSTEM_PROMPT
            )

            self.agent = Agent(
                model=llm,
                system_prompt=system_prompt,
                output_type=str,
                retries=settings.AGENT_RETRIES,
            )
        except Exception as e:
            raise ex.LLMGenerationError(ex.LLM_INIT_CYPHER.format(error=e)) from e

    async def generate(self, natural_language_query: str) -> str:
        logger.info(ls.CYPHER_GENERATING.format(query=natural_language_query))
        try:
            result = await self.agent.run(natural_language_query)
            if (
                not isinstance(result.output, str)
                or cs.CYPHER_MATCH_KEYWORD not in result.output.upper()
            ):
                raise ex.LLMGenerationError(
                    ex.LLM_INVALID_QUERY.format(output=result.output)
                )

            query = _clean_cypher_response(result.output)
            logger.info(ls.CYPHER_GENERATED.format(query=query))
            return query
        except Exception as e:
            logger.error(ls.CYPHER_ERROR.format(error=e))
            raise ex.LLMGenerationError(ex.LLM_GENERATION_FAILED.format(error=e)) from e


def create_rag_orchestrator(tools: list[Tool]) -> Agent:
    try:
        config = settings.active_orchestrator_config
        llm = _create_provider_model(config)

        return Agent(
            model=llm,
            system_prompt=build_rag_orchestrator_prompt(tools),
            tools=tools,
            retries=settings.AGENT_RETRIES,
            output_retries=settings.ORCHESTRATOR_OUTPUT_RETRIES,
            output_type=[str, DeferredToolRequests],
        )
    except Exception as e:
        raise ex.LLMGenerationError(ex.LLM_INIT_ORCHESTRATOR.format(error=e)) from e
