"""실제 응답 토큰을 기록합니다. 공고·API 키·개인 데이터는 로그에 넣지 않습니다."""
import json
import logging
from contextvars import ContextVar
from decimal import Decimal

request_usage: ContextVar[list | None] = ContextVar("request_usage", default=None)
# 공식 표준 요금, USD / 100만 토큰. 미등록 모델은 비용을 추정하지 않습니다.
RATES = {"gpt-4.1-mini": ("0.40", "0.10", "1.60"),
         "gpt-4.1-mini-2025-04-14": ("0.40", "0.10", "1.60")}
PRICING_DATE = "2026-10-15"


def response_usage(response, model, operation):
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    if type(input_tokens) is not int or type(output_tokens) is not int or min(input_tokens, output_tokens) < 0:
        return None
    cached = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0)
    cached = cached if type(cached) is int and 0 <= cached <= input_tokens else 0
    rates = RATES.get(model)
    cost = None
    if rates:
        price, cached_price, output_price = map(Decimal, rates)
        cost = str(((input_tokens - cached) * price + cached * cached_price + output_tokens * output_price) / Decimal(1000000))
    response_id = getattr(response, "id", None)
    return {"response_id": response_id if isinstance(response_id, str) else None,
            "operation": operation, "model": model, "input_tokens": input_tokens,
            "cached_input_tokens": cached, "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens, "estimated_cost_usd": cost,
            "pricing_date": PRICING_DATE if rates else None}


def record_usage(response, model, operation):
    entry = response_usage(response, model, operation)
    if entry is None:
        return
    records = request_usage.get()
    if records is not None:
        records.append(entry)
    logging.getLogger("uvicorn.error").info("llm_usage %s", json.dumps(entry, ensure_ascii=True))
