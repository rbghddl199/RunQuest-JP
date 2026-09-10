from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '호환성을 위해 fixture 기반 시연 데이터 로더를 실행합니다.'

    def handle(self, *args, **options):
        self.stdout.write(
            'seed_presentation_demo는 fixture 기반 로더로 변경되었습니다.'
        )
        call_command('load_runquest_fixtures', reset=True)
