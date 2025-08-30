"""
LLM integration service for CrewAI AutoDev.

This module defines a generic LLM client (`LLMService`) that can call an
external language model provider (e.g. OpenAI) asynchronously. It also defines
a simple `CodeGenerationAgent` that uses the LLM to generate a project
structure based on a template and description. The cost of each call is
estimated using predefined pricing for supported models.
"""
"""LLM integration service for CrewAI AutoDev."""

from __future__ import annotations
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
from pydantic import BaseModel

class LLMProvider(str, Enum):
    OPENAI = "openai"

@dataclass 
class LLMConfig:
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    max_retries: int = 3
    timeout_sec: int = 60

class LLMRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    system_prompt: Optional[str] = None

class LLMResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    finish_reason: str

class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
        self.pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.0025, "output": 0.01},
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = self.pricing.get(model, self.pricing["gpt-4o-mini"])
        return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])

    async def _make_openai_request(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = request.messages.copy()
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})
        
        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        base_url = self.config.base_url or "https://api.openai.com/v1"
        url = f"{base_url}/chat/completions"
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI API error {response.status}: {error_text}")
            
            data = await response.json()
            choice = data["choices"][0]
            usage = data["usage"]
            
            input_tokens = usage["prompt_tokens"]
            output_tokens = usage["completion_tokens"]
            cost = self._calculate_cost(request.model, input_tokens, output_tokens)
            
            return LLMResponse(
                content=choice["message"]["content"],
                model=request.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                finish_reason=choice["finish_reason"]
            )

    async def complete(self, request: LLMRequest, cost_tracker=None) -> Tuple[LLMResponse, bool]:
        for attempt in range(self.config.max_retries):
            try:
                response = await self._make_openai_request(request)
                budget_exceeded = False
                if cost_tracker:
                    budget_exceeded = cost_tracker.add_usage(response.input_tokens, response.output_tokens)
                return response, budget_exceeded
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise e

from __future__ import annotations
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
from pydantic import BaseModel


class LLMProvider(str, Enum):
    """Supported providers for the LLM service."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for the LLM service."""
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    max_retries: int = 3
    timeout_sec: int = 60


class LLMRequest(BaseModel):
    """Request payload for a language model invocation."""
    messages: List[Dict[str, str]]
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    system_prompt: Optional[str] = None


class LLMResponse(BaseModel):
    """Standardized response returned from an LLM call."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    finish_reason: str


class LLMService:
    """
    Generic asynchronous client for an external LLM provider. Supports a
    configurable provider and simple cost tracking for budgeting.
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        # Token pricing per model (input and output costs per 1K tokens)
        self.pricing: Dict[str, Dict[str, float]] = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        }

    async def __aenter__(self) -> "LLMService":
        """Enter the async context manager by creating the HTTP session."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup the HTTP session when exiting the context manager."""
        if self.session:
            await self.session.close()

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Compute the cost in USD for a given number of tokens using pricing table."""
        rates = self.pricing.get(model, self.pricing["gpt-4o-mini"])
        return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])

    async def _make_openai_request(self, request: LLMRequest) -> LLMResponse:
        """Send a chat completion request to the OpenAI API and return a standardized response."""
        assert self.session is not None, "HTTP session is not initialized"

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        messages = request.messages.copy()
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})
        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        base_url = self.config.base_url or "https://api.openai.com/v1"
        url = f"{base_url}/chat/completions"
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                # Include response text for easier debugging
                error_text = await response.text()
                raise Exception(f"OpenAI API error {response.status}: {error_text}")
            data = await response.json()
            choice = data["choices"][0]
            usage = data["usage"]
            input_tokens = usage["prompt_tokens"]
            output_tokens = usage["completion_tokens"]
            cost = self._calculate_cost(request.model, input_tokens, output_tokens)
            return LLMResponse(
                content=choice["message"]["content"],
                model=request.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                finish_reason=choice["finish_reason"]
            )

    async def complete(self, request: LLMRequest, cost_tracker=None) -> Tuple[LLMResponse, bool]:
        """
        Perform the LLM request with retries and optional cost tracking. Returns
        the response and a boolean indicating if budget was exceeded.
        """
        last_exception: Optional[Exception] = None
        for attempt in range(self.config.max_retries):
            try:
                if self.config.provider == LLMProvider.OPENAI:
                    response = await self._make_openai_request(request)
                else:
                    raise NotImplementedError(f"Provider {self.config.provider} not implemented")
                budget_exceeded = False
                if cost_tracker:
                    budget_exceeded = cost_tracker.add_usage(
                        response.input_tokens,
                        response.output_tokens
                    )
                return response, budget_exceeded
            except Exception as e:
                last_exception = e
                # Exponential backoff for retry
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
        raise Exception(f"LLM request failed after {self.config.max_retries} attempts: {last_exception}")


class CodeGenerationAgent:
    """
    Wraps the LLM service to generate a full project structure given a
    template identifier and description. Parses the structured JSON output
    expected from the LLM.
    """

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    async def generate_project_structure(
        self,
        template_id: str,
        description: str,
        cost_tracker=None
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Request the LLM to generate a structured project description. Returns a
        dictionary with keys: files (mapping paths to contents), structure (list of
        paths), instructions and architecture. Also returns whether budget was exceeded.
        """
        system_prompt = (
            "You are an expert software architect. Generate a complete project structure "
            "with all necessary files and their content. Return your response as a JSON object with this structure: "
            "{\n  \"files\": {\"path/to/file.py\": \"file content here\"}, \"structure\": [], \"instructions\": \"...\", "
            "\"architecture\": {\"components\": [], \"tech_stack\": [], \"deployment\": \"\"}\n}"
        )

        if template_id == "rest_api":
            user_prompt = (
                "Create a FastAPI REST API project with the following requirements:\n"
                f"{description}\n\n"
                "Include:\n"
                "- main.py with FastAPI app\n"
                "- models.py with Pydantic models\n"
                "- database.py with SQLAlchemy setup\n"
                "- requirements.txt\n"
                "- Dockerfile\n"
                "- README.md\n"
                "- Basic CRUD endpoints\n"
            )
        else:
            user_prompt = f"Create a {template_id} project with requirements: {description}"

        request = LLMRequest(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            model=self.llm_service.config.default_model,
            temperature=0.1,
            max_tokens=4000,
        )
        response, budget_exceeded = await self.llm_service.complete(request, cost_tracker)
        try:
            project_data: Dict[str, Any] = json.loads(response.content)
            return project_data, budget_exceeded
        except json.JSONDecodeError:
            # Fallback if the model did not return valid JSON
            return {
                "files": {"generated_output.txt": response.content},
                "structure": [],
                "instructions": "Manual review required - failed to parse structured output",
                "architecture": {"components": [], "tech_stack": [], "deployment": ""},
            }, budget_exceeded