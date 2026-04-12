from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shlex
import os
import requests

from . import register

@dataclass
class WebSearch:
    name: str = "web_search"
    description: str = "Search the web for relevant information"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        # Load api key and verify it is found
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return "Error: SERPER_API_KEY not found"
        # Set up the url/payload
        url = "https://google.serper.dev/search"
        payload = {
            "q": args.get('query'),
            "num": 3
        }
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        # Try to do the request and catch the exception if fails
        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
        except Exception as e:
            return f"Search error: {e}"
        # Loop over the returned results and parse the info we want from them
        results = []
        for item in data.get("organic", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            results.append(f"{title}\n{snippet}\n{link}")
        # Return the results
        return "\n".join(results[:5]) if results else "No results found."
    

register(WebSearch())