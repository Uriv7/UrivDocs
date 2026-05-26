"""
UrivDocs — models/llm.py
Key optimizations:
  - keep_alive=-1: model stays loaded in RAM forever (no cold start between requests)
  - warmup(): sends dummy request at startup so first real query is instant
  - Shorter prompt context = faster generation
"""
from __future__ import annotations
import os
from loguru import logger

LLM_MODEL   = os.getenv("LLM_MODEL",       "llama3.2:3b")   # Fast default
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL",  "http://localhost:11434")


class LocalLLM:
    def __init__(self):
        import ollama
        self.client = ollama.AsyncClient(host=OLLAMA_BASE)
        self.model  = LLM_MODEL

    async def warmup(self):
        """
        Send a tiny dummy request at startup.
        This forces Ollama to load the model into RAM so the FIRST real
        query has zero cold-start delay.
        keep_alive=-1 keeps the model loaded permanently.
        """
        try:
            logger.info(f"Pre-loading LLM model into RAM: {self.model}")
            resp = await self.client.generate(
                model=self.model,
                prompt="hi",
                options={"num_predict": 1},   # generate only 1 token
                keep_alive=-1,                 # keep model in RAM forever
            )
            logger.info(f"✓ LLM model loaded and ready: {self.model}")
        except Exception as e:
            logger.warning(f"LLM warmup failed (model may not be pulled yet): {e}")

    async def generate(self, prompt: str) -> str:
        resp = await self.client.generate(
            model=self.model,
            prompt=prompt,
            keep_alive=-1,        # stay loaded after this call
        )
        if isinstance(resp, dict):
            return resp.get("response", "").strip()
        return getattr(resp, "response", str(resp)).strip()

    async def stream(self, prompt: str):
        """Stream tokens. keep_alive=-1 ensures model stays in RAM."""
        try:
            async for chunk in await self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
                keep_alive=-1,
            ):
                token = (chunk.get("response", "") if isinstance(chunk, dict)
                         else getattr(chunk, "response", ""))
                if token:
                    yield token
            return
        except TypeError:
            pass

        try:
            result = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
                keep_alive=-1,
            )
            if hasattr(result, "__await__"):
                result = await result
            async for chunk in result:
                token = (chunk.get("response", "") if isinstance(chunk, dict)
                         else getattr(chunk, "response", ""))
                if token:
                    yield token
            return
        except Exception as e:
            logger.warning(f"Stream attempt 2 failed: {e}")

        # Final fallback: non-streaming word-by-word
        logger.warning("Falling back to non-streaming")
        try:
            full = await self.generate(prompt)
            for word in full.split(" "):
                yield word + " "
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            yield f"[Error: {e}]"

    async def health_check(self) -> bool:
        try:
            models = await self.client.list()
            raw = (models.get("models", []) if isinstance(models, dict)
                   else getattr(models, "models", []))
            available = []
            for m in raw:
                if isinstance(m, dict):
                    name = m.get("name") or m.get("model") or ""
                else:
                    name = getattr(m, "model", None) or getattr(m, "name", None) or ""
                available.append(str(name))
            logger.info(f"Ollama models: {available}")
            return any(self.model in m for m in available)
        except Exception as e:
            logger.warning(f"Ollama health: {e}")
            return False
