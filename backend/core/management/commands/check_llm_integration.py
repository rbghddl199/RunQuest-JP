import json
import os
import time

import requests
from django.core.management.base import BaseCommand

from core.llm_service import check_guardrail, enhance_chat_reply, get_llm_timeout


class Command(BaseCommand):
    help = 'Validate LLM guardrail and answer-generation integration.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prompt',
            default='대전에서 오늘 5km 정도 달릴 코스를 추천해줘.',
            help='Prompt used for the live LLM validation.',
        )
        parser.add_argument(
            '--timeout-seconds',
            type=int,
            default=None,
            help='Temporarily override LLM_TIMEOUT_SECONDS for this check.',
        )

    def handle(self, *args, **options):
        original_timeout = os.environ.get('LLM_TIMEOUT_SECONDS')
        if options['timeout_seconds'] is not None:
            os.environ['LLM_TIMEOUT_SECONDS'] = str(options['timeout_seconds'])

        prompt = options['prompt']
        started_at = time.perf_counter()
        result = {
            'enabled': bool(os.environ.get('LLM_KEY')),
            'model': os.environ.get('LLM_MODEL', 'gpt-5-nano'),
            'timeout_seconds': get_llm_timeout(),
            'checks': {},
        }

        try:
            guardrail = check_guardrail(prompt)
            answer, provider, answer_request = enhance_chat_reply(
                prompt,
                {'distance_km': 5},
                None,
                '5km 조건에 맞는 코스를 고를 수 있도록 거리와 난이도를 먼저 확인해 주세요.',
                'course_recommendation',
                recent_messages=[
                    {
                        'role': 'assistant',
                        'content': '원하는 거리와 분위기를 알려주시면 코스를 추천할게요.',
                        'intent': 'needs_detail',
                    },
                ],
            )

            result['checks']['guardrail'] = {
                'passed': guardrail.get('result'),
                'source': guardrail.get('source'),
                'category': guardrail.get('category'),
                'request': guardrail.get('request'),
            }
            result['checks']['answer'] = {
                'provider': provider,
                'request': answer_request,
                'sample': answer,
            }
            requests_made = int(bool(guardrail.get('request'))) + int(bool(answer_request))
            elapsed_values = [
                item.get('elapsed_ms')
                for item in (guardrail.get('request'), answer_request)
                if isinstance(item, dict) and item.get('elapsed_ms') is not None
            ]
            status_codes = [
                item.get('status_code')
                for item in (guardrail.get('request'), answer_request)
                if isinstance(item, dict)
            ]
            result['summary'] = {
                'requests_made': requests_made,
                'measured_latency_ms': sum(elapsed_values),
                'wall_clock_ms': round((time.perf_counter() - started_at) * 1000),
                'status_codes': status_codes,
                'timeout_detected': any(code is None for code in status_codes),
                'quota_exceeded_detected': any(code == 429 for code in status_codes),
            }
        except requests.Timeout as error:
            result['checks']['exception'] = {
                'type': type(error).__name__,
                'message': str(error),
            }
            result['summary'] = {
                'requests_made': None,
                'timeout_detected': True,
                'quota_exceeded_detected': False,
                'wall_clock_ms': round((time.perf_counter() - started_at) * 1000),
            }
        finally:
            if options['timeout_seconds'] is not None:
                if original_timeout is None:
                    os.environ.pop('LLM_TIMEOUT_SECONDS', None)
                else:
                    os.environ['LLM_TIMEOUT_SECONDS'] = original_timeout

        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
