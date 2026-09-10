from time import perf_counter

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext, override_settings
from rest_framework.test import APIClient

from core.models import CommunityPost


if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')


def measure(label, callback):
    started_at = perf_counter()
    with CaptureQueriesContext(connection) as queries:
        response = callback()
    elapsed_ms = (perf_counter() - started_at) * 1000
    print(
        f'{label}: status={response.status_code} '
        f'elapsed_ms={elapsed_ms:.2f} queries={len(queries)}'
    )
    return response


user = User.objects.filter(profile__survey_completed=True).first() or User.objects.first()
if not user:
    raise RuntimeError('성능 측정에 사용할 사용자가 없습니다.')

client = APIClient()
client.force_authenticate(user=user)

post = CommunityPost.objects.order_by('-created_at').first()

with override_settings(RUNQUEST_PERFORMANCE_LOGS=True, EXTERNAL_AI_ENABLED=False):
    measure(
        'community.list.latest',
        lambda: client.get('/api/community/posts/', {'limit': 12, 'ordering': 'latest'}),
    )
    measure(
        'community.list.popular',
        lambda: client.get('/api/community/posts/', {'limit': 12, 'ordering': 'popular'}),
    )
    if post:
        measure(
            'community.detail',
            lambda: client.get(f'/api/community/posts/{post.id}/'),
        )
    measure(
        'chat.local.reply',
        lambda: client.post(
            '/api/chat/conversation/',
            {'content': '오늘 가볍게 달릴 코스 추천해줘'},
            format='json',
        ),
    )
