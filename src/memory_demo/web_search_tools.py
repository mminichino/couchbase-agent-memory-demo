"""LangChain web-search tool backed by Tavily."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field


class WebSearchArgs(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="The search query used to find current information.",
    )


def _format_search_result(result: Any) -> str:
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        results = result.get("results")
        if not isinstance(results, list):
            return json.dumps(result, ensure_ascii=False)
    elif isinstance(result, list):
        results = result
    else:
        return str(result)

    formatted: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get("title", "Untitled result")
        content = item.get("content", "")
        url = item.get("url", "")
        formatted.append(f"{title}\n{content}\nSource: {url}")
    return "\n\n".join(formatted) or "No relevant search results found."


def _web_search(query: str) -> str:
    result = TavilySearch(max_results=3).invoke({"query": query})
    return _format_search_result(result)


async def _aweb_search(query: str) -> str:
    result = await TavilySearch(max_results=3).ainvoke({"query": query})
    return _format_search_result(result)


web_search_function: StructuredTool = StructuredTool.from_function(
    func=_web_search,
    coroutine=_aweb_search,
    name="web_search",
    description=(
        "Search the web with Tavily for current, recent, or time-sensitive "
        "information that may not be in the model's training data."
    ),
    args_schema=WebSearchArgs,
)

__all__ = ["WebSearchArgs", "web_search_function"]
