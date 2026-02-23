import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_judge import LLMJudgeService


def test_judge_returns_fake_verdict():
    """LLM responds with fake verdict and reasoning."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": '{"verdict": "fake", "reasoning": "用詞模板化，缺乏具體細節。"}'
    }

    with patch("httpx.post", return_value=mock_response):
        result = service.judge("這家餐廳超棒！強烈推薦！", hybrid_score=0.52)

    assert result["verdict"] == "fake"
    assert "用詞模板化" in result["reasoning"]


def test_judge_returns_real_verdict():
    """LLM responds with real verdict."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": '{"verdict": "real", "reasoning": "描述具體、有細節，可信。"}'
    }

    with patch("httpx.post", return_value=mock_response):
        result = service.judge("點了牛肉麵，等了20分鐘，湯頭偏鹹但麵條Q彈。", hybrid_score=0.45)

    assert result["verdict"] == "real"


def test_judge_ollama_unavailable_returns_none():
    """When Ollama is down, judge returns None gracefully."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    with patch("httpx.post", side_effect=Exception("connection refused")):
        result = service.judge("任意評論", hybrid_score=0.50)

    assert result is None


def test_judge_malformed_json_returns_none():
    """When Ollama returns non-parseable output, returns None."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "我不確定這是什麼格式"}

    with patch("httpx.post", return_value=mock_response):
        result = service.judge("任意評論", hybrid_score=0.55)

    assert result is None
