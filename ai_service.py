import os
import json
import re
from typing import List, Dict
import httpx

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
_INFERENCE_ENDPOINT = "https://inference.do-ai.run/v1/chat/completions"
_API_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY")
_MODEL = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")

# ------------------------------------------------------------
# Helper: extract JSON from LLM response (handles markdown code blocks)
# ------------------------------------------------------------
def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

# ------------------------------------------------------------
# Core async call to DigitalOcean Inference API
# ------------------------------------------------------------
async def _call_inference(messages: List[Dict], max_tokens: int = 512) -> Dict:
    payload = {
        "model": _MODEL,
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    timeout = httpx.Timeout(90.0)
    headers = {"Authorization": f"Bearer {_API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(_INFERENCE_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # The content is typically under choices[0].message.content
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_str = _extract_json(content)
            return json.loads(json_str)
        except Exception:
            # Fallback payload – informative but safe for callers
            return {"note": "AI service temporarily unavailable"}

# ------------------------------------------------------------
# Public helpers used by route handlers
# ------------------------------------------------------------
async def generate_tags(title: str, url: str) -> List[str]:
    """Ask the LLM to generate 3‑5 lowercase tags for a bookmark.
    Returns a list of tag strings.
    """
    system_prompt = "You are an assistant that extracts concise, lowercase tags (no spaces) for web bookmarks."
    user_prompt = f"Title: {title}\nURL: {url}\nProvide a JSON array of 3-5 tags."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    result = await _call_inference(messages)
    # Expected format: {"tags": ["tag1", "tag2"]} OR just ["tag1",...] directly
    if isinstance(result, dict) and "tags" in result:
        return result["tags"]
    if isinstance(result, list):
        return result
    # Fallback – empty list
    return []

async def generate_summary(title: str, url: str) -> Dict:
    """Ask the LLM to generate a short (max 2 sentences) summary for a bookmark.
    Returns a dict with at least a "summary" key.
    """
    system_prompt = "You are an assistant that writes a concise two‑sentence summary for a web page based on its title and URL."
    user_prompt = f"Title: {title}\nURL: {url}\nProvide a JSON object with a \"summary\" field."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    result = await _call_inference(messages)
    if isinstance(result, dict) and "summary" in result:
        return {"summary": result["summary"]}
    # Fallback
    return {"note": "AI service temporarily unavailable"}
