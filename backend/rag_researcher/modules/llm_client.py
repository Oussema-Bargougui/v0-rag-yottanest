"""
LLM Client Module

Handles communication with OpenRouter API for text generation.

Responsibilities:
- Send prompts to OpenRouter
- Handle API errors
- Return raw text response
- No business logic
- No formatting
- No citations logic

Author: Yottanest Team
Version: 1.0.0
"""
import logging
from typing import Optional, Dict, List
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenRouter LLM API."""
    
    # Default model for generation
    DEFAULT_MODEL = "gpt-4o-mini"
    
    # Default parameters
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 2000
    
    def __init__(self, model: str = DEFAULT_MODEL):
        """
        Initialize LLM client.
        
        Args:
            model: Model name to use
        """
        self.model = model
        self.client = self._initialize_client()
        
        logger.info(f"LLM client initialized: {model}")
    
    def _initialize_client(self) -> OpenAI:
        """
        Initialize OpenAI client for OpenRouter.
        
        Returns:
            Configured OpenAI client
            
        Raises:
            ValueError: If API key is missing
        """
        api_key = Config.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        base_url = Config.OPENROUTER_BASE_URL
        if not base_url:
            base_url = "https://openrouter.ai/api/v1"
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        
        return client
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            model: Override default model
            
        Returns:
            Generated text
            
        Raises:
            ValueError: If prompt is empty
            RuntimeError: If API call fails
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        model = model or self.model
        
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Log request (truncated)
        logger.info(f"Generating response with model: {model}")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        logger.debug(f"System prompt length: {len(system_prompt or '')} chars")
        
        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response text
            content = response.choices[0].message.content
            
            if not content:
                logger.warning("LLM returned empty response")
                return ""
            
            # Log response (truncated)
            logger.info(f"Generated response: {len(content)} chars")
            logger.debug(f"Response preview: {content[:200]}...")
            
            return content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate response: {str(e)}") from e
    
    def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text from message history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model: Override default model
            
        Returns:
            Generated text
            
        Raises:
            ValueError: If messages is empty or invalid
            RuntimeError: If API call fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        model = model or self.model
        
        # Validate messages
        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must have 'role' and 'content' keys")
            if msg["role"] not in ["system", "user", "assistant"]:
                raise ValueError(f"Invalid role: {msg['role']}")
        
        logger.info(f"Generating response with {len(messages)} messages using model: {model}")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            
            if not content:
                logger.warning("LLM returned empty response")
                return ""
            
            logger.info(f"Generated response: {len(content)} chars")
            
            return content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate response: {str(e)}") from e
    
    def check_connection(self) -> bool:
        """
        Check if client can connect to API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Make a minimal request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            
            logger.info("LLM connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"LLM connection test failed: {str(e)}")
            return False