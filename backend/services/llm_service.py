"""
LLM integration service for the AutoDev project.

This module wraps interactions with large language models (LLMs) such
as OpenAI's GPT series. It supports cost tracking via a provided
`CostTracker` and exposes higher level operations like project
structure generation and code reviews.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

import aiohttp
from pydantic import BaseModel

from ..models import JobAttempt
from .budget_manager import CostTracker


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for connecting to an LLM provider."""
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    max_retries: int = 3
    timeout_sec: int = 60


class LLMRequest(BaseModel):
    """Request payload sent to the LLM service."""
    messages: List[Dict[str, str]]
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    system_prompt: Optional[str] = None


class LLMResponse(BaseModel):
    """Response received from the LLM service."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    finish_reason: str


class LLMService:
    """Service for interacting with remote LLM providers."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        # pricing per 1K tokens for supported models
        self.pricing: Dict[str, Dict[str, float]] = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        }

    async def __aenter__(self) -> "LLMService":
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_sec)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            await self.session.close()

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = self.pricing.get(model, self.pricing["gpt-4o-mini"])
        return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])

    async def _make_openai_request(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
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
                error_text = await response.text()
                raise Exception(f"OpenAI API error {response.status}: {error_text}")
            data = await response.json()
            choice = data["choices"][0]
            usage = data["usage"]
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = self._calculate_cost(request.model, input_tokens, output_tokens)
            return LLMResponse(
                content=choice["message"]["content"],
                model=request.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                finish_reason=choice.get("finish_reason", "")
            )

    async def complete(self, request: LLMRequest, cost_tracker: Optional[CostTracker] = None) -> Tuple[LLMResponse, bool]:
        """Complete an LLM request with retry and budget handling."""
        last_exception: Optional[Exception] = None
        for attempt in range(self.config.max_retries):
            try:
                if self.config.provider == LLMProvider.OPENAI:
                    response = await self._make_openai_request(request)
                else:
                    raise NotImplementedError(f"Provider {self.config.provider} not implemented")
                budget_exceeded = False
                if cost_tracker:
                    budget_exceeded = cost_tracker.add_usage(response.input_tokens, response.output_tokens)
                return response, budget_exceeded
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
        raise Exception(f"LLM request failed after {self.config.max_retries} attempts: {last_exception}")


class CodeGenerationAgent:
    """High-level API for generating code and project structure using LLMs."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    async def generate_project_structure(
        self,
        template_id: str,
        description: str,
        cost_tracker: Optional[CostTracker] = None,
    ) -> Tuple[Dict[str, Any], bool]:
        """Generate a project structure based on a template and description."""
        system_prompt = (
            "You are an expert software architect. Generate a complete project structure "
            "with all necessary files and their content. Return your response as a JSON object with this structure:\n"
            "{\n"
            "  \"files\": {\n"
            "    \"path/to/file.py\": \"file content here\",\n"
            "    \"another/file.js\": \"content...\"\n"
            "  },\n"
            "  \"structure\": [\"folder1/\", \"folder2/file.txt\"],\n"
            "  \"instructions\": \"Setup and run instructions\",\n"
            "  \"architecture\": {\n"
            "    \"components\": [\"component1\", \"component2\"],\n"
            "    \"tech_stack\": [\"tech1\", \"tech2\"],\n"
            "    \"deployment\": \"deployment strategy\"\n"
            "  }\n"
            "}"
        )
        if template_id == "rest_api":
            user_prompt = (
                f"Create a FastAPI REST API project with the following requirements:\n"
                f"{description}\n\n"
                "Include:\n"
                "- main.py with FastAPI app\n"
                "- models.py with Pydantic models\n"
                "- database.py with SQLAlchemy setup\n"
                "- requirements.txt\n"
                "- Dockerfile\n"
                "- README.md\n"
                "- Basic CRUD endpoints\n"
                "- Database migrations\n"
                "- Unit tests\n"
            )
        elif template_id == "nextjs_web_app":
            user_prompt = (
                f"Create a Next.js web application with:\n"
                f"{description}\n\n"
                "Include:\n"
                "- pages/index.tsx\n"
                "- components/ folder with reusable components\n"
                "- styles/ with Tailwind CSS\n"
                "- package.json\n"
                "- next.config.js\n"
                "- TypeScript configuration\n"
                "- Basic authentication\n"
                "- API routes\n"
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
            project_data = json.loads(response.content)
            return project_data, budget_exceeded
        except json.JSONDecodeError:
            return {
                "files": {"generated_output.txt": response.content},
                "structure": [],
                "instructions": "Manual review required - failed to parse structured output",
                "architecture": {"components": [], "tech_stack": [], "deployment": ""},
            }, budget_exceeded

    async def review_code(
        self,
        files: Dict[str, str],
        review_type: str = "security",
        cost_tracker: Optional[CostTracker] = None,
    ) -> Tuple[Dict[str, Any], bool]:
        """Review generated code for quality, security, and best practices."""
        system_prompt = (
            f"You are an expert code reviewer specializing in {review_type} reviews.\n"
            "Analyze the provided code and return a JSON response with:\n"
            "{\n"
            "  \"overall_score\": 8.5,\n"
            "  \"issues\": [\n"
            "    {\"severity\": \"high|medium|low\", \"file\": \"path\", \"line\": 10, \"message\": \"description\", \"fix\": \"suggested fix\"},\n"
            "  ],\n"
            "  \"recommendations\": [\"suggestion1\", \"suggestion2\"],\n"
            "  \"approved\": true,\n"
            "  \"summary\": \"Overall assessment\"\n"
            "}"
        )
        code_content = ""
        for file_path, content in list(files.items())[:10]:
            code_content += f"\n=== {file_path} ===\n{content[:1000]}\n"
        user_prompt = f"Review the following code for {review_type}:\n{code_content}"
        request = LLMRequest(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=2000,
        )
        response, budget_exceeded = await self.llm_service.complete(request, cost_tracker)
        try:
            review_data = json.loads(response.content)
            return review_data, budget_exceeded
        except json.JSONDecodeError:
            return {
                "overall_score": 7.0,
                "issues": [
                    {"severity": "medium", "file": "unknown", "line": 0, "message": "Automated review failed", "fix": "Manual review required"}
                ],
                "recommendations": ["Perform manual code review"],
                "approved": False,
                "summary": "Automated review encountered parsing error",
            }, budget_exceeded
