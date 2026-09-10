import json
import logging
import os

from django.conf import settings
from pydantic import BaseModel, ConfigDict, Field


logger = logging.getLogger(__name__)


class RunFeedbackCopy(BaseModel):
    model_config = ConfigDict(extra='forbid')

    headline: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=500)
    achievements: list[str] = Field(min_length=1, max_length=3)
    cautions: list[str] = Field(min_length=1, max_length=2)
    next_goal_message: str = Field(min_length=1, max_length=200)


def is_openai_enabled():
    return bool(os.getenv('OPENAI_API_KEY')) and settings.EXTERNAL_AI_ENABLED


def get_openai_timeout():
    try:
        return max(1, int(os.getenv('OPENAI_TIMEOUT_SECONDS', '8')))
    except (TypeError, ValueError):
        return 8


def _clean_items(items, fallback, limit):
    cleaned = [
        str(item).strip()[:200]
        for item in items
        if str(item).strip()
    ][:limit]
    return cleaned or fallback


def enhance_feedback(feedback):
    result = {
        **feedback,
        'next_goal': dict(feedback['next_goal']),
        'provider': 'local',
    }
    if not is_openai_enabled():
        return result

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=get_openai_timeout(),
            max_retries=0,
        )
        response = client.responses.parse(
            model=os.getenv('OPENAI_MODEL', 'gpt-5-mini'),
            instructions=(
                '당신은 RunQuest의 한국어 러닝 코치입니다. 서버가 계산한 러닝 분석을 '
                '근거로 따뜻하고 구체적인 피드백 문구를 작성하세요. 제공된 거리, 시간, '
                '페이스, 점수, 비교 수치를 변경하거나 새로운 수치를 만들지 마세요. '
                '의학적 진단을 하지 말고 통증 관련 주의가 필요하면 휴식과 전문가 상담을 '
                '권하세요. headline은 한 문장, summary는 두 문장 이내로 작성하세요. '
                'achievements는 1~3개, cautions는 1~2개로 유지하고 다음 목표 문장은 '
                '서버가 계산한 next_goal 수치와 일치해야 합니다.'
            ),
            input=json.dumps(result, ensure_ascii=False),
            text_format=RunFeedbackCopy,
            max_output_tokens=700,
        )
        refined = response.output_parsed
        if not refined:
            raise ValueError('OpenAI structured feedback response is empty.')

        result['headline'] = refined.headline.strip()[:100]
        result['summary'] = refined.summary.strip()[:500]
        result['achievements'] = _clean_items(
            refined.achievements,
            result['achievements'],
            3,
        )
        result['cautions'] = _clean_items(
            refined.cautions,
            result['cautions'],
            2,
        )
        result['next_goal']['message'] = (
            refined.next_goal_message.strip()[:200]
            or result['next_goal']['message']
        )
        result['provider'] = 'openai'
    except Exception as error:
        logger.warning('OpenAI run feedback enhancement failed: %s', type(error).__name__)
        result['provider'] = 'local_fallback'
    return result
