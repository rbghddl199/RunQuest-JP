from django.db.models import Avg, Sum

from .models import CommunityPost, Course, UserProfile


LEVEL_LABELS = {
    'beginner': '초보자 맞춤',
    'returning': '복귀 러너 맞춤',
    'intermediate': '중급자 맞춤',
    'advanced': '상급자 맞춤',
}


def _course_key(record):
    if record.course_id:
        return f'course:{record.course_id}'
    if record.custom_course_id:
        return f'custom:{record.custom_course_id}'
    return None


def _decimal_sum(queryset, field_name):
    value = queryset.aggregate(total=Sum(field_name))['total']
    return round(float(value or 0), 2)


def _average_pace(queryset):
    return queryset.filter(average_pace_seconds__gt=0).aggregate(
        average=Avg('average_pace_seconds'),
    )['average']


def _runner_level(user):
    profile = getattr(user, 'profile', None)
    if profile and profile.user_type == UserProfile.UserType.RETURNING:
        return 'returning'

    survey = getattr(user, 'survey_response', None)
    if survey and survey.experience_level in {'beginner', 'intermediate', 'advanced'}:
        return survey.experience_level

    return 'beginner'


def _is_light_run(record, max_distance):
    if record.course and record.course.difficulty == Course.Difficulty.EASY:
        return True
    return float(record.distance_km or 0) <= max_distance


def _mission(mission_id, title, metric, target, unit, description):
    current = min(metric, target)
    progress = 100 if target <= 0 else min(round((current / target) * 100), 100)
    return {
        'id': mission_id,
        'title': title,
        'current': round(current, 1) if isinstance(current, float) else current,
        'target': target,
        'unit': unit,
        'description': description,
        'completed': current >= target,
        'progress': progress,
    }


def _weekly_share_bonus(user, week_start):
    return _mission(
        'share',
        '러닝 기록 공유 1회',
        CommunityPost.objects.filter(
            author=user,
            running_record__isnull=False,
            created_at__date__gte=week_start,
        ).count(),
        1,
        '회',
        '선택 보너스 활동이에요. 기록을 공유하고 응원을 받아보세요.',
    )


def _mission_templates(level, running_goal):
    base_templates = {
        'beginner': [
            ('weekly_runs', '이번 주 2회 러닝', 2, '회', '부담 없이 러닝 루틴을 시작해요.'),
            ('weekly_distance', '이번 주 5km 달리기', 5, 'km', '이번 주 누적 거리로 천천히 완주해요.'),
            ('explore', '새 코스 1개 완주', 1, '개', '익숙한 난이도 안에서 새 코스를 경험해요.'),
        ],
        'returning': [
            ('weekly_runs', '이번 주 2회 회복 러닝', 2, '회', '무리하지 않고 러닝 감각을 되찾아요.'),
            ('weekly_distance', '이번 주 6km 달리기', 6, 'km', '누적 거리로 컨디션을 천천히 끌어올려요.'),
            ('explore', '새 코스 1개 완주', 1, '개', '가벼운 새 코스로 다시 재미를 붙여요.'),
        ],
        'intermediate': [
            ('weekly_runs', '이번 주 3회 러닝', 3, '회', '꾸준한 주간 루틴을 유지해요.'),
            ('weekly_distance', '이번 주 10km 달리기', 10, 'km', '이번 주 누적 거리로 체력을 쌓아요.'),
            ('diversity', '서로 다른 코스 2개 완주', 2, '개', '코스 변화를 주며 지루함을 줄여요.'),
        ],
        'advanced': [
            ('weekly_runs', '이번 주 4회 러닝', 4, '회', '상급자 루틴에 맞게 빈도를 유지해요.'),
            ('weekly_distance', '이번 주 20km 달리기', 20, 'km', '충분한 누적 거리로 지구력을 쌓아요.'),
            ('long_run', '8km 이상 장거리 1회 완주', 1, '회', '이번 주 한 번은 긴 호흡으로 달려요.'),
        ],
    }
    bonus_templates = {
        'beginner': {
            'health': ('light_runs', '이번 주 2회 가벼운 러닝', 2, '회', '짧고 편한 코스로 몸을 적응시켜요.'),
            'stress_relief': ('light_runs', '이번 주 2회 가벼운 러닝', 2, '회', '부담 없는 페이스로 기분 전환을 해요.'),
            'weight_loss': ('light_runs', '이번 주 2회 가벼운 러닝', 2, '회', '꾸준히 움직이는 시간을 만드는 데 집중해요.'),
            'endurance': ('steady_run', '3km 이상 러닝 1회', 1, '회', '한 번은 조금 더 긴 호흡으로 달려봐요.'),
            'performance': ('steady_run', '3km 이상 러닝 1회', 1, '회', '안정적인 거리에서 페이스 감각을 익혀요.'),
            'race': ('steady_run', '3km 이상 러닝 1회', 1, '회', '완주 감각을 만드는 짧은 목표를 세워요.'),
        },
        'returning': {
            'health': ('light_runs', '이번 주 2회 가벼운 러닝', 2, '회', '컨디션 회복을 우선하며 달려요.'),
            'stress_relief': ('light_runs', '이번 주 2회 가벼운 러닝', 2, '회', '가벼운 코스로 리듬을 되찾아요.'),
            'weight_loss': ('light_runs', '이번 주 2회 가벼운 러닝', 2, '회', '반복 가능한 강도로 움직임을 늘려요.'),
            'endurance': ('steady_run', '4km 이상 러닝 1회', 1, '회', '무리하지 않는 선에서 지속 시간을 늘려요.'),
            'performance': ('steady_run', '4km 이상 러닝 1회', 1, '회', '회복된 감각으로 일정한 페이스를 유지해요.'),
            'race': ('steady_run', '4km 이상 러닝 1회', 1, '회', '대회 준비의 첫 기준 거리를 만들어봐요.'),
        },
        'intermediate': {
            'health': ('light_runs', '이번 주 1회 회복 러닝', 1, '회', '강약 조절로 꾸준함을 지켜요.'),
            'stress_relief': ('light_runs', '이번 주 1회 회복 러닝', 1, '회', '기록보다 컨디션 회복에 초점을 맞춰요.'),
            'weight_loss': ('steady_run', '5km 이상 러닝 1회', 1, '회', '한 번은 충분한 운동 시간을 확보해요.'),
            'endurance': ('long_run', '8km 이상 장거리 1회 완주', 1, '회', '지구력을 쌓는 긴 호흡의 러닝을 해요.'),
            'performance': ('pace', '평균 페이스 10초 개선', 10, '초', '이전 평균보다 조금 더 가볍게 밀어붙여요.'),
            'race': ('long_run', '8km 이상 장거리 1회 완주', 1, '회', '대회 준비에 필요한 지속주를 넣어봐요.'),
        },
        'advanced': {
            'health': ('light_runs', '이번 주 1회 회복 러닝', 1, '회', '강한 루틴 사이에 회복 시간을 확보해요.'),
            'stress_relief': ('light_runs', '이번 주 1회 회복 러닝', 1, '회', '가벼운 페이스로 피로를 풀어요.'),
            'weight_loss': ('diversity', '서로 다른 코스 3개 완주', 3, '개', '다양한 코스로 운동 자극을 넓혀요.'),
            'endurance': ('diversity', '서로 다른 코스 3개 완주', 3, '개', '지형 변화를 주며 지구력을 다져요.'),
            'performance': ('pace', '평균 페이스 15초 개선', 15, '초', '최근 평균보다 선명한 기록 향상을 노려요.'),
            'race': ('pace', '평균 페이스 15초 개선', 15, '초', '레이스 페이스에 가까운 감각을 만들어봐요.'),
        },
    }
    templates = base_templates.get(level, base_templates['beginner'])
    bonus = bonus_templates.get(level, {}).get(running_goal)

    if bonus and bonus[0] not in {item[0] for item in templates}:
        return [*templates, bonus]
    return templates


def build_weekly_mission(user, completed_records, week_start):
    weekly_records_qs = completed_records.filter(
        completed_at__date__gte=week_start,
    ).select_related('course', 'custom_course')
    previous_records_qs = completed_records.filter(
        completed_at__date__lt=week_start,
    ).select_related('course', 'custom_course')

    weekly_records = list(weekly_records_qs)
    previous_records = list(previous_records_qs)
    survey = getattr(user, 'survey_response', None)
    level = _runner_level(user)
    light_distance = {
        'beginner': 3.5,
        'returning': 4,
        'intermediate': 4.5,
        'advanced': 5,
    }.get(level, 3.5)
    steady_distance = {
        'beginner': 3,
        'returning': 4,
        'intermediate': 5,
        'advanced': 8,
    }.get(level, 3)

    weekly_course_keys = {key for key in (_course_key(record) for record in weekly_records) if key}
    previous_course_keys = {key for key in (_course_key(record) for record in previous_records) if key}
    previous_average_pace = _average_pace(previous_records_qs)
    weekly_average_pace = _average_pace(weekly_records_qs)
    pace_improvement = 0
    if previous_average_pace and weekly_average_pace:
        pace_improvement = max(0, round(previous_average_pace - weekly_average_pace))

    metrics = {
        'weekly_runs': len(weekly_records),
        'light_runs': sum(1 for record in weekly_records if _is_light_run(record, light_distance)),
        'weekly_distance': _decimal_sum(weekly_records_qs, 'distance_km'),
        'diversity': len(weekly_course_keys),
        'pace': pace_improvement,
        'explore': len(weekly_course_keys - previous_course_keys),
        'steady_run': sum(1 for record in weekly_records if float(record.distance_km or 0) >= steady_distance),
        'long_run': sum(1 for record in weekly_records if float(record.distance_km or 0) >= 8),
    }

    templates = _mission_templates(
        level,
        survey.running_goal if survey else None,
    )
    missions = [
        _mission(mission_id, title, metrics.get(mission_id, 0), target, unit, description)
        for mission_id, title, target, unit, description in templates
    ]

    completed_count = sum(1 for mission in missions if mission['completed'])
    active = next((mission for mission in missions if not mission['completed']), None)
    if active is None:
        active = {
            'id': 'all_clear',
            'title': '이번 주 미션 올 클리어',
            'current': len(missions),
            'target': len(missions),
            'unit': '개',
            'description': '이번 주 성향 맞춤 미션을 모두 완료했어요.',
            'completed': True,
            'progress': 100,
        }

    active['level'] = level
    active['level_label'] = LEVEL_LABELS.get(level, LEVEL_LABELS['beginner'])
    active['current_position'] = min(completed_count + 1, len(missions))
    active['total_missions'] = len(missions)
    active['completed_count'] = completed_count
    active['bonus_mission'] = _weekly_share_bonus(user, week_start)
    active['next_title'] = next(
        (
            mission['title']
            for mission in missions
            if not mission['completed'] and mission['id'] != active['id']
        ),
        None,
    )
    return active
