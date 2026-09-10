from django.utils import timezone

from .badges import current_attendance_streak
from .models import CommunityComment, CommunityPost, Course, RunningRecord


STAGES = [
    (100, 6, 'legend', '전설 러너', 'purple'),
    (30, 5, 'crown', '크라운 러너', 'gold'),
    (14, 4, 'blaze', '블레이즈 러너', 'orange'),
    (7, 3, 'flame', '플레임 러너', 'red'),
    (3, 2, 'spark', '스파크 러너', 'blue'),
    (1, 1, 'seed', '새싹 러너', 'teal'),
    (0, 0, 'rest', '휴식 중인 러너', 'gray'),
]

STYLE_DEFINITIONS = {
    'ember': ('불꽃형', '#ff6b35'),
    'moon': ('달빛형', '#7257e8'),
    'speed': ('번개형', '#8a4fff'),
    'wave': ('물결형', '#168fe5'),
    'nature': ('숲형', '#43a833'),
}

COURSE_TYPE_PROFILES = {
    Course.CourseType.PARK: ('공원형 러너', '공원, 산책로처럼 안정적인 코스를 선호해요.'),
    Course.CourseType.RIVER: ('리버사이드 러너', '강변과 하천 주변 코스를 편하게 느껴요.'),
    Course.CourseType.LAKE: ('리버사이드 러너', '호수와 물길 주변 코스를 선호해요.'),
    Course.CourseType.URBAN: ('도심형 러너', '접근성 좋은 도심 코스를 즐겨요.'),
    Course.CourseType.TRAIL: ('트레일 러너', '숲길과 업힐이 있는 코스를 즐겨요.'),
}


def _tag(name, reason):
    return {'name': name, 'reason': reason}


def build_running_profile(user):
    records = list(
        RunningRecord.objects.filter(
            user=user,
            status=RunningRecord.Status.COMPLETED,
        ).select_related('course').order_by('-completed_at')[:50]
    )
    survey = getattr(user, 'survey_response', None)
    record_count = len(records)
    course_records = [record for record in records if record.course_id]
    course_types = [record.course.course_type for record in course_records]
    distinct_courses = {record.course_id for record in course_records}
    average_distance = (
        sum(float(record.distance_km or 0) for record in records) / record_count
        if record_count else 0
    )
    longest_distance = max((float(record.distance_km or 0) for record in records), default=0)
    hard_count = sum(1 for record in course_records if record.course.difficulty == Course.Difficulty.HARD)
    easy_count = sum(1 for record in course_records if record.course.difficulty == Course.Difficulty.EASY)
    uphill_count = sum(1 for record in course_records if record.course.elevation_gain_m >= 80)
    morning_count = sum(
        5 <= timezone.localtime(record.completed_at).hour < 12
        for record in records
        if record.completed_at
    )
    night_count = sum(
        timezone.localtime(record.completed_at).hour >= 18
        for record in records
        if record.completed_at
    )
    streak = current_attendance_streak(user)
    post_count = CommunityPost.objects.filter(author=user).count()
    comment_count = CommunityComment.objects.filter(author=user).count()

    total_course_count = max(1, len(course_types))
    course_preferences = [
        (
            '공원형 러너',
            course_types.count(Course.CourseType.PARK),
            COURSE_TYPE_PROFILES[Course.CourseType.PARK][1],
        ),
        (
            '리버사이드 러너',
            course_types.count(Course.CourseType.RIVER) + course_types.count(Course.CourseType.LAKE),
            '강변, 하천, 호수처럼 물길 주변 코스를 편하게 느껴요.',
        ),
        (
            '도심형 러너',
            course_types.count(Course.CourseType.URBAN),
            COURSE_TYPE_PROFILES[Course.CourseType.URBAN][1],
        ),
        (
            '트레일 러너',
            course_types.count(Course.CourseType.TRAIL),
            COURSE_TYPE_PROFILES[Course.CourseType.TRAIL][1],
        ),
    ]
    scores = {
        name: {
            'score': count / total_course_count,
            'description': description,
            'reason': f'최근 완주 코스 중 {count}회가 {name.replace(" 러너", "")} 성향이에요.',
        }
        for name, count, description in course_preferences
        if count
    }

    if course_types:
        dominant = max(scores.values(), key=lambda item: item['score']) if scores else None
        if not dominant or dominant['score'] < 0.45:
            primary_type = '균형형 러너'
            description = '특정 코스 취향에 치우치지 않고 다양한 환경에서 달려요.'
            primary_reason = '최근 코스 유형이 한쪽으로 크게 치우치지 않았어요.'
        else:
            primary_type = next(name for name, item in scores.items() if item is dominant)
            description = dominant['description']
            primary_reason = dominant['reason']
    elif survey and survey.course_type in COURSE_TYPE_PROFILES:
        primary_type, description = COURSE_TYPE_PROFILES[survey.course_type]
        primary_reason = '설문에서 선호한 코스 유형을 기준으로 판단했어요.'
    else:
        primary_type = '균형형 러너'
        description = '아직 충분한 기록이 없어 다양한 코스를 탐색하기 좋은 단계예요.'
        primary_reason = '러닝 기록이 쌓이면 더 정확한 코스 취향을 분석할 수 있어요.'

    tags = []
    if average_distance <= 3.5 and easy_count >= max(1, record_count * 0.4):
        tags.append(_tag('회복형', '짧고 쉬운 코스를 자주 선택했어요.'))
    if longest_distance >= 8 or hard_count >= 2 or uphill_count >= 2:
        tags.append(_tag('챌린지형', '긴 거리나 업힐 코스 경험이 있어요.'))
    if survey and survey.running_goal in {'performance', 'race'}:
        tags.append(_tag('스피드형', '기록 향상 목표가 뚜렷해요.'))
    if longest_distance >= 7 or average_distance >= 5.5:
        tags.append(_tag('지구력형', '긴 거리와 지속 시간을 꾸준히 쌓고 있어요.'))
    if record_count >= 8 and streak >= 3:
        tags.append(_tag('루틴형', '반복 기록과 연속 출석 흐름이 보여요.'))
    if streak >= 7 or record_count >= 20:
        tags.append(_tag('꾸준형', '출석과 러닝 빈도가 안정적으로 높아요.'))
    if night_count >= max(2, record_count * 0.45):
        tags.append(_tag('야간형', '저녁과 야간 시간대 기록이 많아요.'))
    if morning_count >= max(2, record_count * 0.45):
        tags.append(_tag('모닝형', '아침 시간대 기록이 많아요.'))
    if len(distinct_courses) >= 5 and len(distinct_courses) / max(1, len(course_records)) >= 0.5:
        tags.append(_tag('탐험형', '여러 코스를 고르게 경험하고 있어요.'))
    if survey and survey.running_goal in {'stress_relief', 'health'}:
        tags.append(_tag('힐링형', '건강 관리와 기분 전환 목적이 잘 드러나요.'))
    if survey and survey.running_goal == 'weight_loss':
        tags.append(_tag('다이어트형', '체중 관리와 칼로리 소모 목표가 있어요.'))
    if (survey and survey.running_style in {'small_group', 'crew'}) or post_count + comment_count >= 3:
        tags.append(_tag('소셜형', '커뮤니티 활동이나 함께 뛰기 성향이 보여요.'))

    unique_tags = []
    seen = set()
    for tag in tags:
        if tag['name'] not in seen and tag['name'] not in primary_type:
            seen.add(tag['name'])
            unique_tags.append(tag)

    return {
        'type': primary_type,
        'primary_type': primary_type,
        'category': '코스 취향형',
        'description': description,
        'preferred_time': '',
        'secondary_types': unique_tags[:3],
        'tags': [item['name'] for item in unique_tags[:3]],
        'reasons': [primary_reason, *[item['reason'] for item in unique_tags[:2]]],
        'next_recommendation': '대표 성향과 보조 태그를 함께 반영해 다음 코스를 추천할게요.',
    }


def build_profile_style(user):
    records = RunningRecord.objects.filter(
        user=user,
        status=RunningRecord.Status.COMPLETED,
    )
    streak = current_attendance_streak(user)
    stage = next(item for item in STAGES if streak >= item[0])
    if streak <= 0:
        next_stage = next(
            (
                {'days': days, 'name': name}
                for days, _, _, name, _ in reversed(STAGES)
                if days > streak
            ),
            None,
        )
        return {
            'streak_days': streak,
            'stage_index': stage[1],
            'stage_code': stage[2],
            'stage_name': stage[3],
            'stage_color': stage[4],
            'style_code': 'rest',
            'style_name': '기본형',
            'accent_color': '#94a3b8',
            'frame_url': None,
            'style_scores': {
                'moon': 0,
                'wave': 0,
                'speed': 0,
                'nature': 0,
            },
            'next_stage': next_stage,
        }
    recent = list(
        records.select_related('course').order_by('-completed_at')[:20]
    )
    course_types = [
        record.course.course_type
        for record in recent
        if record.course_id
    ]
    evening_count = sum(
        timezone.localtime(record.completed_at).hour >= 18
        for record in recent
        if record.completed_at
    )
    river_count = sum(item in {'river', 'lake'} for item in course_types)
    park_count = sum(item in {'park', 'trail'} for item in course_types)
    fast_count = sum(
        0 < record.average_pace_seconds <= 390 for record in recent
    )
    record_count = max(1, len(recent))
    style_scores = {
        'moon': evening_count / record_count,
        'wave': river_count / record_count,
        'speed': fast_count / record_count,
        'nature': park_count / record_count,
    }
    strongest_style, strongest_score = max(
        style_scores.items(),
        key=lambda item: item[1],
    )

    style_code = strongest_style if strongest_score >= 0.6 else 'ember'
    style_name, accent = STYLE_DEFINITIONS[style_code]

    next_stage = next(
        (
            {'days': days, 'name': name}
            for days, _, _, name, _ in reversed(STAGES)
            if days > streak
        ),
        None,
    )
    return {
        'streak_days': streak,
        'stage_index': stage[1],
        'stage_code': stage[2],
        'stage_name': stage[3],
        'stage_color': stage[4],
        'style_code': style_code,
        'style_name': style_name,
        'accent_color': accent,
        'frame_url': f'/profile-frames/{style_code}/stage-{stage[1]}.png',
        'style_scores': {
            key: round(value, 2) for key, value in style_scores.items()
        },
        'next_stage': next_stage,
    }
