# src/agents/llm_client.py
"""
LLM Client Abstraction
----------------------
Provides a unified interface for interacting with different LLM providers
(OpenAI and Anthropic). Supports both text generation and structured output.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        self.message = message
        super().__init__(f"{provider} error: {message}")


class LLMConfigurationError(LLMError):
    """Exception raised when LLM is not properly configured."""
    pass


class LLMAPIError(LLMError):
    """Exception raised when LLM API call fails."""
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(provider, message)


@dataclass
class LLMResponse:
    """Response from an LLM generation call.
    
    Attributes:
        content: The generated text content.
        tokens_used: Total tokens used (prompt + completion).
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        model: The model that generated the response.
    """
    content: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    model: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Generate text from the LLM."""
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate structured output from the LLM."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: Optional[str] = None):
        """Initialize OpenAI provider.
        
        Parameters
        ----------
        api_key : str
            OpenAI API key.
        model : str
            Model to use (default: gpt-4).
        base_url : Optional[str]
            Custom base URL for API (e.g., for OpenRouter).
        """
        if not api_key:
            raise LLMConfigurationError("openai", "API key is required")
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                if self.base_url:
                    self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
                else:
                    self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise LLMConfigurationError(
                    "openai", 
                    "openai package not installed. Install with: pip install openai"
                )
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Generate text using OpenAI API with retry logic for rate limits.
        
        Parameters
        ----------
        prompt : str
            The user prompt to send to the model.
        system_prompt : Optional[str]
            Optional system prompt to set context.
        max_tokens : int
            Maximum tokens in the response.
        temperature : float
            Sampling temperature (0.0 to 2.0).
            
        Returns
        -------
        LLMResponse
            The generated response with token usage.
        """
        import asyncio
        
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Retry logic for rate limits
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                content = response.choices[0].message.content or ""
                usage = response.usage
                
                return LLMResponse(
                    content=content,
                    tokens_used=usage.total_tokens if usage else 0,
                    prompt_tokens=usage.prompt_tokens if usage else 0,
                    completion_tokens=usage.completion_tokens if usage else 0,
                    model=self.model
                )
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit errors (429) or timeout
                if '429' in str(e) or 'rate' in error_msg or 'too many' in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited. Waiting {wait_time}s before retry {attempt + 2}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                
                # For other errors, log and raise
                if self.api_key and self.api_key in str(e):
                    error_msg = str(e).replace(self.api_key, "[REDACTED]")
                else:
                    error_msg = str(e)
                logger.error("OpenAI API error: %s", error_msg)
                raise LLMAPIError("openai", error_msg)
        
        raise LLMAPIError("openai", "Max retries exceeded due to rate limiting")
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate structured JSON output using OpenAI API.
        
        Parameters
        ----------
        prompt : str
            The user prompt to send to the model.
        response_schema : Dict[str, Any]
            JSON schema describing the expected response structure.
        system_prompt : Optional[str]
            Optional system prompt to set context.
        max_tokens : int
            Maximum tokens in the response.
        temperature : float
            Sampling temperature.
            
        Returns
        -------
        Dict[str, Any]
            Parsed JSON response matching the schema.
        """
        schema_str = json.dumps(response_schema, indent=2)
        structured_prompt = f"""{prompt}

Respond with valid JSON matching this schema:
{schema_str}

Return ONLY the JSON object, no additional text."""

        enhanced_system = system_prompt or ""
        if enhanced_system:
            enhanced_system += "\n\n"
        enhanced_system += "You must respond with valid JSON only. No markdown, no explanations."
        
        response = await self.generate(
            prompt=structured_prompt,
            system_prompt=enhanced_system,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        try:
            # Try to parse the response as JSON
            content = response.content.strip()
            # Handle potential markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse structured response: %s", e)
            raise LLMAPIError("openai", f"Invalid JSON response: {e}")


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        """Initialize Anthropic provider.
        
        Parameters
        ----------
        api_key : str
            Anthropic API key.
        model : str
            Model to use (default: claude-3-sonnet-20240229).
        """
        if not api_key:
            raise LLMConfigurationError("anthropic", "API key is required")
        
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise LLMConfigurationError(
                    "anthropic",
                    "anthropic package not installed. Install with: pip install anthropic"
                )
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Generate text using Anthropic API.
        
        Parameters
        ----------
        prompt : str
            The user prompt to send to the model.
        system_prompt : Optional[str]
            Optional system prompt to set context.
        max_tokens : int
            Maximum tokens in the response.
        temperature : float
            Sampling temperature (0.0 to 1.0).
            
        Returns
        -------
        LLMResponse
            The generated response with token usage.
        """
        client = self._get_client()
        
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await client.messages.create(**kwargs)
            
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
            
            return LLMResponse(
                content=content,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                model=self.model
            )
        except Exception as e:
            error_msg = str(e)
            # Ensure API key is not exposed in error messages
            if self.api_key and self.api_key in error_msg:
                error_msg = error_msg.replace(self.api_key, "[REDACTED]")
            logger.error("Anthropic API error: %s", error_msg)
            raise LLMAPIError("anthropic", error_msg)
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate structured JSON output using Anthropic API.
        
        Parameters
        ----------
        prompt : str
            The user prompt to send to the model.
        response_schema : Dict[str, Any]
            JSON schema describing the expected response structure.
        system_prompt : Optional[str]
            Optional system prompt to set context.
        max_tokens : int
            Maximum tokens in the response.
        temperature : float
            Sampling temperature.
            
        Returns
        -------
        Dict[str, Any]
            Parsed JSON response matching the schema.
        """
        schema_str = json.dumps(response_schema, indent=2)
        structured_prompt = f"""{prompt}

Respond with valid JSON matching this schema:
{schema_str}

Return ONLY the JSON object, no additional text."""

        enhanced_system = system_prompt or ""
        if enhanced_system:
            enhanced_system += "\n\n"
        enhanced_system += "You must respond with valid JSON only. No markdown, no explanations."
        
        response = await self.generate(
            prompt=structured_prompt,
            system_prompt=enhanced_system,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        try:
            content = response.content.strip()
            # Handle potential markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse structured response: %s", e)
            raise LLMAPIError("anthropic", f"Invalid JSON response: {e}")


class LLMClient:
    """Unified LLM client that supports multiple providers.
    
    This class provides a unified interface for interacting with different
    LLM providers (OpenAI and Anthropic) through a provider abstraction.
    
    Example
    -------
    >>> from src.utils.config import APIConfig
    >>> config = APIConfig(
    ...     openai_api_key="sk-...",
    ...     llm_provider="openai",
    ...     llm_model="gpt-4"
    ... )
    >>> client = LLMClient(config)
    >>> response = await client.generate("Hello, world!")
    >>> print(response.content)
    """
    
    def __init__(self, config):
        """Initialize LLM client with configuration.
        
        Parameters
        ----------
        config : APIConfig
            Configuration object containing API keys and provider settings.
            
        Raises
        ------
        LLMConfigurationError
            If the provider is not supported or API key is missing.
        """
        self.config = config
        self._provider: Optional[BaseLLMProvider] = None
        self._initialize_provider()
    
    def _initialize_provider(self) -> None:
        """Initialize the appropriate LLM provider based on configuration."""
        provider_name = self.config.llm_provider.lower()
        model = self.config.llm_model
        
        if provider_name == "openai":
            if not self.config.openai_api_key:
                raise LLMConfigurationError(
                    "openai",
                    "OpenAI API key is required when using OpenAI provider"
                )
            self._provider = OpenAIProvider(
                api_key=self.config.openai_api_key,
                model=model
            )
            logger.info("Initialized OpenAI provider with model: %s", model)
            
        elif provider_name == "openrouter":
            # OpenRouter uses OpenAI-compatible API with different base URL
            api_key = getattr(self.config, 'openrouter_api_key', None) or self.config.openai_api_key
            if not api_key:
                raise LLMConfigurationError(
                    "openrouter",
                    "OpenRouter API key is required when using OpenRouter provider"
                )
            self._provider = OpenAIProvider(
                api_key=api_key,
                model=model,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("Initialized OpenRouter provider with model: %s", model)
            
        elif provider_name == "anthropic":
            if not self.config.anthropic_api_key:
                raise LLMConfigurationError(
                    "anthropic",
                    "Anthropic API key is required when using Anthropic provider"
                )
            self._provider = AnthropicProvider(
                api_key=self.config.anthropic_api_key,
                model=model
            )
            logger.info("Initialized Anthropic provider with model: %s", model)
        
        elif provider_name == "ollama":
            # Ollama uses OpenAI-compatible API at localhost
            self._provider = OpenAIProvider(
                api_key="ollama",  # Ollama doesn't require a real API key
                model=model,
                base_url="http://localhost:11434/v1"
            )
            logger.info("Initialized Ollama provider with model: %s", model)
            
        else:
            raise LLMConfigurationError(
                provider_name,
                f"Unsupported LLM provider: {provider_name}. "
                "Supported providers: openai, openrouter, anthropic, ollama"
            )
    
    @property
    def provider(self) -> BaseLLMProvider:
        """Get the underlying LLM provider."""
        if self._provider is None:
            raise LLMConfigurationError("unknown", "LLM provider not initialized")
        return self._provider
    
    @property
    def provider_name(self) -> str:
        """Get the name of the current provider."""
        return self.config.llm_provider.lower()
    
    @property
    def model_name(self) -> str:
        """Get the name of the current model."""
        return self.config.llm_model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Generate text from the LLM.
        
        Parameters
        ----------
        prompt : str
            The user prompt to send to the model.
        system_prompt : Optional[str]
            Optional system prompt to set context.
        max_tokens : int
            Maximum tokens in the response (default: 2000).
        temperature : float
            Sampling temperature (default: 0.7).
            
        Returns
        -------
        LLMResponse
            The generated response with content and token usage.
            
        Raises
        ------
        LLMAPIError
            If the API call fails.
        """
        logger.debug(
            "Generating text with %s (model=%s, max_tokens=%d, temp=%.2f)",
            self.provider_name, self.model_name, max_tokens, temperature
        )
        return await self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate structured JSON output from the LLM.
        
        Parameters
        ----------
        prompt : str
            The user prompt to send to the model.
        response_schema : Dict[str, Any]
            JSON schema describing the expected response structure.
        system_prompt : Optional[str]
            Optional system prompt to set context.
        max_tokens : int
            Maximum tokens in the response (default: 2000).
        temperature : float
            Sampling temperature (default: 0.7).
            
        Returns
        -------
        Dict[str, Any]
            Parsed JSON response matching the schema.
            
        Raises
        ------
        LLMAPIError
            If the API call fails or response is not valid JSON.
        """
        logger.debug(
            "Generating structured output with %s (model=%s)",
            self.provider_name, self.model_name
        )
        return await self.provider.generate_structured(
            prompt=prompt,
            response_schema=response_schema,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
