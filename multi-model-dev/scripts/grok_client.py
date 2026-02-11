#!/usr/bin/env python3
"""
Grok API Client

A robust client for xAI's Grok API with:
- Rate limiting and exponential backoff
- Automatic retries on transient errors
- Response parsing and validation
- Streaming support (optional)

Usage:
    from grok_client import GrokClient
    
    client = GrokClient()  # Uses GROK_API_KEY env var
    response = client.chat("Explain quantum computing")
    print(response.content)
"""

import os
import time
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Generator
from enum import Enum

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    raise


class GrokModel(Enum):
    """Available Grok models."""
    GROK_2 = "grok-2"
    GROK_2_MINI = "grok-2-mini"  # Faster, cheaper
    GROK_BETA = "grok-beta"


@dataclass
class GrokResponse:
    """Parsed response from Grok API."""
    content: str
    model: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    raw_response: Dict[str, Any]
    
    @property
    def code_blocks(self) -> List[str]:
        """Extract code blocks from response."""
        import re
        pattern = r'```(?:\w+)?\n(.*?)```'
        return re.findall(pattern, self.content, re.DOTALL)
    
    @property
    def first_code_block(self) -> Optional[str]:
        """Get the first code block, if any."""
        blocks = self.code_blocks
        return blocks[0].strip() if blocks else None


class GrokError(Exception):
    """Base exception for Grok API errors."""
    pass


class GrokRateLimitError(GrokError):
    """Rate limit exceeded."""
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s" if retry_after else "Rate limit exceeded")


class GrokAuthError(GrokError):
    """Authentication failed."""
    pass


class GrokClient:
    """
    Grok API client with rate limiting and retries.
    
    Args:
        api_key: Grok API key (defaults to GROK_API_KEY env var)
        base_url: API base URL (defaults to https://api.x.ai/v1)
        max_retries: Maximum retry attempts for transient errors
        retry_delay: Initial delay between retries (exponential backoff)
        timeout: Request timeout in seconds
    """
    
    DEFAULT_BASE_URL = "https://api.x.ai/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 60
    ):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        if not self.api_key:
            raise GrokError("GROK_API_KEY not set. Set environment variable or pass api_key parameter.")
        
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def chat(
        self,
        prompt: str,
        model: GrokModel = GrokModel.GROK_2,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> GrokResponse:
        """
        Send a chat completion request.
        
        Args:
            prompt: User message/prompt
            model: Grok model to use
            system_prompt: Optional system message
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters passed to API
            
        Returns:
            GrokResponse with parsed content and metadata
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat_messages(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def chat_messages(
        self,
        messages: List[Dict[str, str]],
        model: GrokModel = GrokModel.GROK_2,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> GrokResponse:
        """
        Send a chat completion with multiple messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Grok model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters
            
        Returns:
            GrokResponse with parsed content
        """
        payload = {
            "model": model.value if isinstance(model, GrokModel) else model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        return self._request_with_retry("POST", "/chat/completions", json=payload)
    
    def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> GrokResponse:
        """
        Make request with automatic retry on transient errors.
        """
        url = f"{self.base_url}{endpoint}"
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self._session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Success
                if response.status_code == 200:
                    return self._parse_response(response.json())
                
                # Rate limit - check for Retry-After header
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_seconds = int(retry_after) if retry_after else None
                    
                    if attempt < self.max_retries:
                        wait_time = retry_seconds or (self.retry_delay * (2 ** attempt))
                        print(f"Rate limited. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    
                    raise GrokRateLimitError(retry_seconds)
                
                # Auth error - don't retry
                if response.status_code in (401, 403):
                    raise GrokAuthError(f"Authentication failed: {response.text}")
                
                # Server error - retry
                if response.status_code >= 500:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)
                        print(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Other error
                raise GrokError(f"API error {response.status_code}: {response.text}")
                
            except requests.exceptions.Timeout:
                last_error = GrokError(f"Request timeout after {self.timeout}s")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Timeout. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
            except requests.exceptions.ConnectionError as e:
                last_error = GrokError(f"Connection error: {e}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Connection error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
        
        raise last_error or GrokError("Request failed after all retries")
    
    def _parse_response(self, data: Dict[str, Any]) -> GrokResponse:
        """Parse API response into GrokResponse."""
        try:
            choice = data["choices"][0]
            usage = data.get("usage", {})
            
            return GrokResponse(
                content=choice["message"]["content"],
                model=data.get("model", "unknown"),
                finish_reason=choice.get("finish_reason", "unknown"),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                raw_response=data
            )
        except (KeyError, IndexError) as e:
            raise GrokError(f"Failed to parse response: {e}\nRaw: {data}")
    
    def code_task(
        self,
        task: str,
        language: Optional[str] = None,
        model: GrokModel = GrokModel.GROK_2
    ) -> GrokResponse:
        """
        Specialized method for code generation tasks.
        
        Args:
            task: Description of the coding task
            language: Target programming language (optional)
            model: Grok model to use
            
        Returns:
            GrokResponse (use .first_code_block to extract code)
        """
        system_prompt = """You are an expert software engineer. Follow these guidelines:
1. Write clean, production-ready code
2. Include error handling and edge cases
3. Add brief comments for complex logic
4. Use modern best practices and idioms
5. Return code in a single markdown code block"""
        
        if language:
            system_prompt += f"\n6. Use {language} programming language"
        
        return self.chat(
            prompt=task,
            system_prompt=system_prompt,
            model=model,
            temperature=0.3  # Lower temp for code
        )


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Grok API CLI")
    parser.add_argument("prompt", nargs="?", help="Prompt to send to Grok")
    parser.add_argument("--model", "-m", default="grok-2", choices=["grok-2", "grok-2-mini", "grok-beta"])
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--temperature", "-t", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--code", "-c", action="store_true", help="Code generation mode")
    parser.add_argument("--language", "-l", help="Target language for code generation")
    
    args = parser.parse_args()
    
    if not args.prompt:
        # Interactive mode
        print("Grok CLI (Ctrl+D to exit)")
        try:
            while True:
                prompt = input("\n> ").strip()
                if not prompt:
                    continue
                
                client = GrokClient()
                if args.code:
                    response = client.code_task(prompt, language=args.language)
                else:
                    response = client.chat(prompt, system_prompt=args.system, temperature=args.temperature)
                
                print(f"\n{response.content}")
                print(f"\n[{response.total_tokens} tokens]")
        except EOFError:
            print("\nBye!")
    else:
        client = GrokClient()
        
        if args.code:
            response = client.code_task(args.prompt, language=args.language)
        else:
            model = GrokModel(args.model)
            response = client.chat(
                args.prompt,
                model=model,
                system_prompt=args.system,
                temperature=args.temperature,
                max_tokens=args.max_tokens
            )
        
        print(response.content)
        print(f"\n[{response.model} | {response.total_tokens} tokens | {response.finish_reason}]")
