from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import (
    Attendance,
    Badge,
    ChatMessage,
    CommunityComment,
    CommunityPost,
    Course,
    RecommendationSession,
    RunningRecord,
    SurveyResponse,
)


FIXTURE_FILES = [
    '01_users.json',
    '02_courses.json',
    '03_badges.json',
    '04_surveys.json',
    '05_running_records.json',
    '06_attendance.json',
    '07_saved_courses.json',
    '08_user_badges.json',
    '09_posts.json',
    '10_comments.json',
    '11_post_likes.json',
    '12_post_bookmarks.json',
    '13_chatbot_history.json',
    '14_recommend_history.json',
]

EXPECTED_COUNTS = {
    'users': 50,
    'courses': 22,
    'badges': 10,
    'surveys': 50,
    'running_records': 664,
    'attendance': 654,
    'posts': 50,
    'comments': 150,
    'chat_messages': 12,
    'recommendation_sessions': 50,
}


class Command(BaseCommand):
    help = '변환된 RunQuest JSON fixture를 순서대로 로드하고 개수를 검증합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='기존 DB 데이터를 먼저 삭제한 뒤 fixture를 로드합니다.',
        )

    def handle(self, *args, **options):
        fixture_dir = Path(__file__).resolve().parents[3] / 'fixtures' / 'runquest'
        missing = [
            name for name in FIXTURE_FILES
            if not (fixture_dir / name).exists()
        ]
        if missing:
            raise CommandError(
                f'fixture 파일이 없습니다: {", ".join(missing)}'
            )

        if options['reset']:
            self.stdout.write('기존 데이터를 초기화합니다.')
            call_command('flush', interactive=False, verbosity=0)

        try:
            with transaction.atomic():
                for name in FIXTURE_FILES:
                    self.stdout.write(f'로드 중: {name}')
                    call_command(
                        'loaddata',
                        str(fixture_dir / name),
                        verbosity=0,
                    )
                self.validate_counts()
                call_command('polish_demo_data', verbosity=0)
        except Exception as error:
            raise CommandError(f'fixture 로드 실패: {error}') from error

        self.stdout.write(self.style.SUCCESS(
            'RunQuest fixture 로드와 데이터 검증을 완료했습니다.'
        ))
        self.stdout.write(
            '시연 로그인: new@runquest.com / !@1q2w3e4r'
        )

    def validate_counts(self):
        actual = {
            'users': User.objects.count(),
            'courses': Course.objects.count(),
            'badges': Badge.objects.count(),
            'surveys': SurveyResponse.objects.count(),
            'running_records': RunningRecord.objects.count(),
            'attendance': Attendance.objects.count(),
            'posts': CommunityPost.objects.count(),
            'comments': CommunityComment.objects.count(),
            'chat_messages': ChatMessage.objects.count(),
            'recommendation_sessions': RecommendationSession.objects.count(),
        }
        mismatches = [
            f'{name}: 예상 {expected}, 실제 {actual[name]}'
            for name, expected in EXPECTED_COUNTS.items()
            if actual[name] != expected
        ]
        if mismatches:
            raise CommandError('; '.join(mismatches))
