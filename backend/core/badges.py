from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import Attendance, Badge, RunningRecord, UserBadge


BADGE_DEFINITIONS = [
    {
        'code': 'first-finish',
        'name': '첫 완주',
        'description': '첫 번째 러닝을 끝까지 완료했어요.',
        'icon': 'footprints',
        'color': '#0866ff',
        'condition_type': 'run_count',
        'condition_value': 1,
        'sort_order': 1,
    },
    {
        'code': 'five-kilometers',
        'name': '5km 러너',
        'description': '누적 거리 5km를 달성했어요.',
        'icon': 'route',
        'color': '#12a58c',
        'condition_type': 'total_distance',
        'condition_value': 5,
        'sort_order': 2,
    },
    {
        'code': 'ten-kilometers',
        'name': '10km 러너',
        'description': '누적 거리 10km를 달성했어요.',
        'icon': 'medal',
        'color': '#7b4ce2',
        'condition_type': 'total_distance',
        'condition_value': 10,
        'sort_order': 3,
    },
    {
        'code': 'three-runs',
        'name': '꾸준한 시작',
        'description': '러닝을 3회 완료했어요.',
        'icon': 'flame',
        'color': '#f07a28',
        'condition_type': 'run_count',
        'condition_value': 3,
        'sort_order': 4,
    },
    {
        'code': 'three-day-streak',
        'name': '3일 연속 출석',
        'description': '3일 연속으로 러닝 출석을 완료했어요.',
        'icon': 'calendar-check',
        'color': '#0b83c9',
        'condition_type': 'attendance_streak',
        'condition_value': 3,
        'sort_order': 5,
    },
    {
        'code': 'night-runner',
        'name': '달빛 러너',
        'description': '오후 8시 이후 러닝을 완료했어요.',
        'icon': 'moon',
        'color': '#4056b5',
        'condition_type': 'night_run',
        'condition_value': 1,
        'sort_order': 6,
    },
]


def ensure_badges():
    if Badge.objects.exists():
        return
    for definition in BADGE_DEFINITIONS:
        Badge.objects.create(
            code=definition['code'],
            **{
                key: value
                for key, value in definition.items()
                if key != 'code'
            },
        )


def longest_attendance_streak(user):
    dates = list(
        Attendance.objects.filter(user=user)
        .order_by('date')
        .values_list('date', flat=True)
    )
    longest = 0
    current = 0
    previous = None
    for date in dates:
        current = current + 1 if previous and date == previous + timedelta(days=1) else 1
        longest = max(longest, current)
        previous = date
    return longest


def current_attendance_streak(user):
    dates = set(
        Attendance.objects.filter(user=user).values_list('date', flat=True)
    )
    cursor = timezone.localdate()
    if cursor not in dates:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def badge_progress(user, badge, stats=None):
    records = RunningRecord.objects.filter(
        user=user,
        status=RunningRecord.Status.COMPLETED,
    )
    stats = stats or {
        'run_count': records.count(),
        'total_distance': float(
            records.aggregate(total=Sum('distance_km'))['total'] or 0
        ),
        'attendance_streak': longest_attendance_streak(user),
        'night_run': records.filter(completed_at__hour__gte=20).count(),
        'river_run': records.filter(course__course_type='river').count(),
        'park_run': records.filter(course__course_type__in=['park', 'trail']).count(),
        'fast_run': records.filter(
            average_pace_seconds__gt=0,
            average_pace_seconds__lte=390,
        ).count(),
        'long_run': records.filter(distance_km__gte=10).count(),
        'distinct_course': records.exclude(course=None).values('course').distinct().count(),
        'community_post': user.community_posts.count(),
    }
    value = stats.get(badge.condition_type, 0)
    return min(100, round((value / badge.condition_value) * 100)), value


def award_eligible_badges(user):
    ensure_badges()
    records = RunningRecord.objects.filter(
        user=user,
        status=RunningRecord.Status.COMPLETED,
    )
    stats = {
        'run_count': records.count(),
        'total_distance': float(
            records.aggregate(total=Sum('distance_km'))['total'] or 0
        ),
        'attendance_streak': longest_attendance_streak(user),
        'night_run': records.filter(completed_at__hour__gte=20).count(),
        'river_run': records.filter(course__course_type='river').count(),
        'park_run': records.filter(course__course_type__in=['park', 'trail']).count(),
        'fast_run': records.filter(
            average_pace_seconds__gt=0,
            average_pace_seconds__lte=390,
        ).count(),
        'long_run': records.filter(distance_km__gte=10).count(),
        'distinct_course': records.exclude(course=None).values('course').distinct().count(),
        'community_post': user.community_posts.count(),
    }
    awarded = []
    for badge in Badge.objects.all():
        progress, _ = badge_progress(user, badge, stats)
        if progress >= 100:
            user_badge, created = UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
            )
            if created:
                awarded.append(user_badge)
    return awarded
