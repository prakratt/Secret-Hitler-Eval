"""OpenRouter API client for accessing multiple AI models."""
from __future__ import annotations
import os
import json
import re
from typing import Optional, List, Dict, Any
import httpx
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    id: str
    name: str
    provider: str
    context_length: int = 8192


# Top AI models across different providers
# Updated to use the latest available models on OpenRouter
AVAILABLE_MODELS = [
    ModelConfig("openai/gpt-4o", "GPT-4o", "OpenAI", 128000),
    ModelConfig("openai/gpt-5.1", "GPT-5.1", "OpenAI", 128000),
    ModelConfig("anthropic/claude-opus-4.5", "Claude Opus 4.5", "Anthropic", 200000),
    ModelConfig("anthropic/claude-sonnet-4.5", "Claude Sonnet 4.5", "Anthropic", 200000),
    ModelConfig("x-ai/grok-4-fast", "Grok 4", "xAI", 131072),
    ModelConfig("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet", "Anthropic", 200000),
    ModelConfig("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B", "Meta", 131072),
]


class OpenRouterClient:
    """Client for OpenRouter API."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable.")

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/ai-secret-hitler",
                "X-Title": "AI Secret Hitler",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )

    def chat_completion(
        self,
        model: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> dict:
        """Send a chat completion request."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    def _repair_truncated_json(self, json_str: str, function_name: str) -> Optional[dict]:
        """Try to repair truncated JSON by closing open strings and objects."""
        # First, try to extract required parameters using regex (more reliable for truncated JSON)
        try:
            if function_name == "investigate_action":
                match = re.search(r'"player_seat"\s*:\s*(\d+)', json_str)
                if match:
                    return {"player_seat": int(match.group(1)), "reasoning": ""}
            elif function_name == "discard_policy":
                match = re.search(r'"discard_index"\s*:\s*(\d+)', json_str)
                if match:
                    return {"discard_index": int(match.group(1)), "reasoning": ""}
            elif function_name == "enact_policy":
                match = re.search(r'"enact_index"\s*:\s*(\d+)', json_str)
                if match:
                    return {"enact_index": int(match.group(1)), "reasoning": ""}
            elif function_name == "nominate_chancellor":
                match = re.search(r'"player_seat"\s*:\s*(\d+)', json_str)
                if match:
                    return {"player_seat": int(match.group(1)), "reasoning": ""}
            elif function_name == "vote":
                match = re.search(r'"choice"\s*:\s*"([^"]+)"', json_str)
                if match:
                    return {"choice": match.group(1), "reasoning": ""}
        except:
            pass
        
        # If regex extraction failed, try to repair the JSON structure
        try:
            # Find the last complete key-value pair before truncation
            # Look for patterns like "key":value or "key":"value
            last_colon = json_str.rfind(':')
            if last_colon > 0:
                # Check if we're in the middle of a string value
                after_colon = json_str[last_colon + 1:].strip()
                if after_colon.startswith('"'):
                    # We're in a string value - find where it started and close it
                    # Find the opening quote after the colon
                    quote_start = json_str.find('"', last_colon)
                    if quote_start > 0:
                        # Close the string and the object
                        json_str = json_str[:quote_start] + '""'
            
            # Close any unclosed strings (odd number of quotes means unclosed)
            quote_count = json_str.count('"')
            if quote_count % 2 != 0:
                # Find the last quote and see if we need to close it
                last_quote_idx = json_str.rfind('"')
                if last_quote_idx > 0:
                    # Check if this quote is part of a value (has : before it)
                    before_quote = json_str[:last_quote_idx]
                    if ':' in before_quote:
                        # Close the string
                        json_str = json_str[:last_quote_idx + 1] + '"'
            
            # Close any open braces/brackets
            open_braces = json_str.count('{') - json_str.count('}')
            open_brackets = json_str.count('[') - json_str.count(']')
            
            json_str += '}' * open_braces
            json_str += ']' * open_brackets
            
            # Try parsing the repaired JSON
            return json.loads(json_str)
        except:
            return None

    def get_tool_call(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.7
    ) -> Optional[dict]:
        """Get a tool call from the model."""
        # Use higher max_tokens for tool calls to avoid truncation
        response = self.chat_completion(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
            max_tokens=2048  # Increased to handle long reasoning strings
        )

        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})

        # Check for tool calls
        tool_calls = message.get("tool_calls", [])
        if tool_calls:
            tool_call = tool_calls[0]
            function_info = tool_call.get("function", {})
            function_name = function_info.get("name")
            arguments_raw = function_info.get("arguments")
            
            # Parse arguments - could be a string (JSON) or already a dict
            if arguments_raw is None:
                print(f"Warning: Tool call from {model} has no arguments")
                return None
            
            if isinstance(arguments_raw, str):
                try:
                    arguments = json.loads(arguments_raw)
                except json.JSONDecodeError as e:
                    # Try to repair truncated JSON (common when reasoning strings are too long)
                    arguments = self._repair_truncated_json(arguments_raw, function_name)
                    if arguments is None:
                        print(f"Error: Failed to parse JSON arguments from {model}: {e}")
                        print(f"Raw arguments (truncated): {arguments_raw[:200]}...")
                        return None
            elif isinstance(arguments_raw, dict):
                arguments = arguments_raw
            else:
                print(f"Warning: Unexpected arguments type from {model}: {type(arguments_raw)}")
                return None
            
            return {
                "name": function_name,
                "arguments": arguments
            }

        return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def get_default_models(count: int = 7) -> list[ModelConfig]:
    """Get a list of default models to use for the game."""
    return AVAILABLE_MODELS[:count]
