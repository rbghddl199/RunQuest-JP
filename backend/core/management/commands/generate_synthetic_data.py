import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.feedback import generate_run_feedback
from core.models import (
    Attendance,
    Course,
    RunningRecord,
    SurveyResponse,
    UserProfile,
)
from core.survey import build_score_profile


class Command(BaseCommand):
    help = '추천 시스템 시연용 합성 사용자와 러닝 기록을 생성합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=20)
        parser.add_argument('--seed', type=int, default=2026)

    def handle(self, *args, **options):
        random.seed(options['seed'])
        courses = list(Course.objects.filter(is_active=True))
        if not courses:
            self.stderr.write('먼저 코스 seed migration을 적용해 주세요.')
            return

        for index in range(options['users']):
            email = f'synthetic{index + 1:03d}@runquest.local'
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email},
            )
            if created:
                user.set_password('Synthetic!2026')
                user.save(update_fields=['password'])
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'nickname': f'합성러너{index + 1:03d}',
                    'survey_completed': True,
                    'user_type': UserProfile.UserType.ACTIVE,
                },
            )
            answers = {
                'experience_level': random.choice(['beginner', 'intermediate', 'advanced']),
                'distance_range': random.choice(['1_3km', '3_5km', '5_10km']),
                'course_type': random.choice(['park', 'river', 'urban', 'trail']),
                'preferred_time': random.choice(['morning', 'evening', 'night']),
                'running_style': random.choice(['solo', 'small_group', 'crew']),
                'running_goal': random.choice(['health', 'weight_loss', 'endurance', 'stress_relief']),
            }
            SurveyResponse.objects.update_or_create(
                user=user,
                defaults={**answers, 'score_profile': build_score_profile(answers)},
            )

            target_count = random.randint(3, 24)
            if user.running_records.count() >= target_count:
                continue
            for run_index in range(target_count):
                course = random.choice(courses)
                distance = max(1, round(float(course.distance_km) * random.uniform(0.8, 1.1), 2))
                pace = random.randint(330, 570)
                completed_at = timezone.now() - timedelta(
                    days=target_count - run_index,
                    hours=random.randint(0, 20),
                )
                record = RunningRecord.objects.create(
                    user=user,
                    course=course,
                    status=RunningRecord.Status.COMPLETED,
                    tracking_mode=RunningRecord.TrackingMode.SIMULATION,
                    distance_km=distance,
                    duration_seconds=round(distance * pace),
                    average_pace_seconds=pace,
                    calories=round(distance * 65),
                    completed_at=completed_at,
                )
                record.ai_feedback = generate_run_feedback(record)
                record.save(update_fields=['ai_feedback'])
                Attendance.objects.get_or_create(
                    user=user,
                    date=timezone.localdate(completed_at),
                    defaults={'running_record': record},
                )
        self.stdout.write(self.style.SUCCESS(
            f'합성 사용자 {options["users"]}명 생성을 완료했습니다.'
        ))
