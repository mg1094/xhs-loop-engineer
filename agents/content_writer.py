"""
Agent 2: Content Generation
Generates Xiaohongshu posts via LLM API, with configurable backends.
"""

import yaml
import os
import json
import http.client
from pathlib import Path
from typing import Optional


class ContentWriter:
    def __init__(
        self,
        config_path: str = "config/schedule.yaml",
        style_path: str = "config/style.yaml",
    ):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        with open(style_path) as f:
            self.style = yaml.safe_load(f)

    def build_prompt(self, topic: str, article_type: str = "xiaobai") -> str:
        """Build the content generation prompt from template."""
        prompt_template = Path("prompts/content_writer.md").read_text(encoding="utf-8")

        style_summary = yaml.dump(
            self.style, allow_unicode=True, default_flow_style=False
        )

        return prompt_template.format(
            style_guide=style_summary,
            topic=topic,
            article_type=article_type,
        )

    def call_anthropic(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
    ) -> str:
        """Call Anthropic Claude API directly."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        conn = http.client.HTTPSConnection("api.anthropic.com")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        body = json.dumps(
            {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        conn.request("POST", "/v1/messages", body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode())

        if response.status != 200:
            raise RuntimeError(f"API error ({response.status}): {data}")

        return data["content"][0]["text"]

    def call_openai_compatible(
        self,
        prompt: str,
        api_base: str,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
    ) -> str:
        """Call any OpenAI-compatible API (OpenAI, DeepSeek, local vLLM, etc.)."""
        conn = http.client.HTTPSConnection(api_base.replace("https://", "").split("/")[0])
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        body = json.dumps(
            {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        path = "/".join(api_base.replace("https://", "").split("/")[1:] + ["chat", "completions"])
        if not path.startswith("/"):
            path = "/" + path

        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode())

        if response.status != 200:
            raise RuntimeError(f"API error ({response.status}): {data}")

        return data["choices"][0]["message"]["content"]

    def generate(
        self,
        topic: str,
        article_type: str = "xiaobai",
        backend: str = "manual",
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> dict:
        """
        Generate content via configured LLM backend.

        Backends:
            - "manual": Return the prompt for manual use (default)
            - "anthropic": Call Anthropic Claude API directly
            - "openai": Call any OpenAI-compatible API
        """
        prompt = self.build_prompt(topic, article_type)

        if backend == "manual":
            return {
                "topic": topic,
                "type": article_type,
                "prompt": prompt,
                "content": None,
                "status": "prompt_ready",
                "message": "Send this prompt to an LLM to generate content",
            }

        try:
            if backend == "anthropic":
                content = self.call_anthropic(
                    prompt, model=model or "claude-sonnet-4-6", max_tokens=max_tokens
                )
            elif backend == "openai":
                content = self.call_openai_compatible(
                    prompt,
                    api_base=api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
                    api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
                    model=model or os.environ.get("OPENAI_MODEL", "gpt-4o"),
                    max_tokens=max_tokens,
                )
            else:
                raise ValueError(f"Unknown backend: {backend}")

            return {
                "topic": topic,
                "type": article_type,
                "content": content,
                "backend": backend,
                "model": model,
                "status": "generated",
                "message": f"Content generated via {backend}/{model}",
            }
        except Exception as e:
            return {
                "topic": topic,
                "type": article_type,
                "prompt": prompt,
                "content": None,
                "status": "error",
                "message": str(e),
            }

    def run(self, topic: str, article_type: str = "xiaobai") -> dict:
        """Legacy interface — uses manual backend."""
        return self.generate(topic, article_type, backend="manual")
