import json
import re
import httpx
from app.core.config import settings


JUDGE_PROMPT = """你是一個評論真實性分析師。請判斷以下評論是否為真實評論或假評論（業配/刷評論）。

評論內容：
{text}

系統初步評分：{hybrid_score:.0%}（越低越可疑）

請以 JSON 格式回覆，格式如下：
{{"verdict": "real" 或 "fake", "reasoning": "用繁體中文說明判斷理由，2-3句話"}}

只輸出 JSON，不要有其他文字。"""


class LLMJudgeService:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_URL
        self.model = "qwen3:14b"

    def judge(self, text: str, hybrid_score: float) -> dict | None:
        """
        Ask Qwen3-14B to judge a borderline review.
        Returns {"verdict": "real"|"fake", "reasoning": str} or None on failure.
        """
        prompt = JUDGE_PROMPT.format(text=text, hybrid_score=hybrid_score)
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "think": False},
                timeout=30.0,
            )
            response.raise_for_status()
            raw = response.json().get("response", "")
            # Strip Qwen3 <think>...</think> blocks if thinking mode was not disabled
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            parsed = json.loads(raw)
            if "verdict" in parsed and "reasoning" in parsed:
                return parsed
            return None
        except Exception:
            return None


llm_judge_service = LLMJudgeService()
