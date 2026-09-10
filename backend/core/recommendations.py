from dataclasses import dataclass
from datetime import timedelta
from math import asin, cos, exp, radians, sin, sqrt
import os
import random
from statistics import mean

from django.db import transaction
from django.utils import timezone

from .models import (
    Course,
    RecommendationItem,
    RecommendationSession,
    RunningRecord,
)


DIFFICULTY_LEVELS = {'easy': 1, 'normal': 2, 'hard': 3}
DEFAULT_LOCATION_PRIORITY_WEIGHT = 0.08
DEFAULT_POPULARITY_WEIGHT = 0.02
TYPE_DIVERSITY_PENALTY = 6.0
DISTRICT_DIVERSITY_PENALTY = 3.5
REFRESH_JITTER_MAX = 4.0

HOME_DIFFICULTY_CANDIDATES = {
    'beginner': ['easy'],
    'intermediate': ['normal'],
    'advanced': ['hard', 'normal'],
}

HOME_FALLBACK_DIFFICULTIES = {
    'beginner': ['easy', 'normal'],
    'intermediate': ['normal', 'easy', 'hard'],
    'advanced': ['hard', 'normal', 'easy'],
}

HOME_DISTANCE_LIMITS = {
    'beginner': (0, 4.5),
    'intermediate': (2.5, 8.5),
    'advanced': (4.5, 99),
}


@dataclass(frozen=True)
class RecommendationWeights:
    user_state: str
    survey: float
    record: float
    safety: float
    returning_recent_count: int = 0


def ordered_records(records):
    return sorted(
        records,
        key=lambda record: record.completed_at or record.started_at,
        reverse=True,
    )


def records_after_latest_gap(records):
    chronological = list(reversed(ordered_records(records)))
    latest_gap_index = None
    for index in range(1, len(chronological)):
        previous_at = chronological[index - 1].completed_at
        current_at = chronological[index].completed_at
        if previous_at and current_at and current_at - previous_at >= timedelta(days=30):
            latest_gap_index = index
    if latest_gap_index is None:
        return []
    return chronological[latest_gap_index:]


def active_weights(count):
    if count <= 2:
        survey, record = 0.8, 0.2
    elif count <= 5:
        survey, record = 0.65, 0.35
    elif count <= 10:
        survey, record = 0.45, 0.55
    elif count <= 20:
        survey, record = 0.25, 0.75
    else:
        survey, record = 0.1, 0.9
    return RecommendationWeights('active', survey, record, 0.0)


def resolve_weights(records, now=None):
    records = ordered_records(records)
    count = len(records)
    if count == 0:
        return RecommendationWeights('new', 1.0, 0.0, 0.0)

    now = now or timezone.now()
    latest_completed_at = records[0].completed_at
    if latest_completed_at <= now - timedelta(days=30):
        return RecommendationWeights('returning', 0.5, 0.3, 0.2)

    post_return_records = records_after_latest_gap(records)
    returning_recent_count = len(post_return_records)
    if post_return_records and returning_recent_count < 10:
        progress = returning_recent_count / 10
        survey = round(0.5 - 0.4 * progress, 2)
        safety = round(0.2 - 0.2 * progress, 2)
        record = round(1.0 - survey - safety, 2)
        return RecommendationWeights(
            'returning',
            survey,
            record,
            safety,
            returning_recent_count,
        )
    if returning_recent_count >= 10:
        return RecommendationWeights('active', 0.1, 0.9, 0.0)
    return active_weights(count)


def closeness_score(value, target, tolerance):
    difference = abs(float(value) - float(target))
    return max(0.0, 100.0 * (1 - difference / tolerance))


def build_record_profile(records):
    if not records:
        return None

    distances = [float(record.distance_km) for record in records]
    paces = [record.average_pace_seconds for record in records]
    course_types = [
        record.course.course_type
        for record in records
        if record.course_id
    ]

    preferred_type = None
    if course_types:
        preferred_type = max(set(course_types), key=course_types.count)

    return {
        'average_distance_km': round(mean(distances), 2),
        'average_pace_seconds': round(mean(paces)),
        'preferred_course_type': preferred_type,
        'longest_distance_km': max(distances),
    }


def home_runner_level(user):
    survey = getattr(user, 'survey_response', None)
    if survey and survey.experience_level in HOME_DIFFICULTY_CANDIDATES:
        return survey.experience_level
    return 'beginner'


def home_course_reason(course, survey, level):
    if survey and course.course_type == survey.course_type:
        return f'선호한 {course.get_course_type_display()} 코스라 오늘 고르기 좋아요.'
    if level == 'beginner':
        return '초보 러너도 부담 없이 달리기 좋은 쉬운 코스예요.'
    if level == 'intermediate':
        return '중급 러너에게 알맞은 거리와 난이도의 코스예요.'
    if course.difficulty == 'hard':
        return '상급 러너가 오늘 도전하기 좋은 코스예요.'
    return '상급 러너의 컨디션 조절에 맞는 안정적인 코스예요.'


def build_home_course_recommendations(user, today=None, limit=5):
    today = today or timezone.localdate()
    survey = getattr(user, 'survey_response', None)
    level = home_runner_level(user)
    min_distance, max_distance = HOME_DISTANCE_LIMITS[level]

    queryset = Course.objects.filter(is_active=True)
    candidates = list(
        queryset.filter(
            difficulty__in=HOME_DIFFICULTY_CANDIDATES[level],
            distance_km__gte=min_distance,
            distance_km__lte=max_distance,
        )
    )

    if len(candidates) < limit:
        candidates = list(
            queryset.filter(
                difficulty__in=HOME_FALLBACK_DIFFICULTIES[level],
            )
        )

    if survey:
        preferred = [course for course in candidates if course.course_type == survey.course_type]
        others = [course for course in candidates if course.course_type != survey.course_type]
        pool = preferred + others
    else:
        pool = candidates

    base_random = random.Random(f'home-courses-base:{user.id}:{level}')
    shuffled = list(pool)
    base_random.shuffle(shuffled)
    if len(shuffled) > limit:
        offset = today.toordinal() % len(shuffled)
        shuffled = shuffled[offset:] + shuffled[:offset]

    selected = shuffled[:limit]
    daily_random = random.Random(f'home-courses-order:{user.id}:{today.isoformat()}')
    daily_random.shuffle(selected)
    return [
        {
            'rank': index,
            'course': course,
            'reasons': [home_course_reason(course, survey, level)],
            'score_details': {
                'home_daily': True,
                'level': level,
                'date': today.isoformat(),
            },
        }
        for index, course in enumerate(selected, start=1)
    ]


def haversine_distance_km(latitude, longitude, course):
    latitude_delta = radians(float(course.start_latitude) - float(latitude))
    longitude_delta = radians(float(course.start_longitude) - float(longitude))
    start_latitude = radians(float(latitude))
    course_latitude = radians(float(course.start_latitude))
    value = (
        sin(latitude_delta / 2) ** 2
        + cos(start_latitude)
        * cos(course_latitude)
        * sin(longitude_delta / 2) ** 2
    )
    return 6371.0 * 2 * asin(sqrt(value))


def location_fit(course, latitude, longitude):
    if latitude is None or longitude is None:
        return 0.0, None
    distance_km = haversine_distance_km(latitude, longitude, course)
    score = 100.0 * exp(-distance_km / 2.0)
    return score, round(distance_km, 2)


def location_priority_weight():
    try:
        value = float(
            os.getenv(
                'RECOMMENDATION_LOCATION_WEIGHT',
                DEFAULT_LOCATION_PRIORITY_WEIGHT,
            )
        )
    except (TypeError, ValueError):
        return DEFAULT_LOCATION_PRIORITY_WEIGHT
    return min(0.2, max(0.0, value))


def combine_scores(personalized_score, location_score, popularity_score, location_applied):
    if not location_applied:
        return personalized_score * (1 - DEFAULT_POPULARITY_WEIGHT) + popularity_score * DEFAULT_POPULARITY_WEIGHT

    location_bonus = location_score * location_priority_weight()
    popularity_bonus = popularity_score * DEFAULT_POPULARITY_WEIGHT
    return min(100.0, personalized_score + location_bonus + popularity_bonus)


def diversify_ranked_courses(ranked, limit=7):
    selected = []
    remaining = list(ranked)

    while remaining and len(selected) < limit:
        type_counts = {}
        district_counts = {}
        for item in selected:
            course = item['course']
            type_counts[course.course_type] = type_counts.get(course.course_type, 0) + 1
            district_counts[course.district] = district_counts.get(course.district, 0) + 1

        def adjusted_score(item):
            course = item['course']
            penalty = (
                type_counts.get(course.course_type, 0) * TYPE_DIVERSITY_PENALTY
                + district_counts.get(course.district, 0) * DISTRICT_DIVERSITY_PENALTY
            )
            return item['total_score'] - penalty

        next_item = max(
            remaining,
            key=lambda item: (
                adjusted_score(item),
                item['total_score'],
                item['course'].popularity_score,
            ),
        )
        selected.append(next_item)
        remaining.remove(next_item)

    return selected


def survey_fit(course, survey):
    profile = survey.score_profile
    target_distance = profile['target_distance_km']
    preferred_types = profile['preferred_course_types']
    preferred_time = profile['preferred_time']
    experience_score = profile['experience_score']

    distance = closeness_score(course.distance_km, target_distance, max(target_distance, 4))
    course_type = 100 if course.course_type in preferred_types else 35
    time = (
        100
        if preferred_time == 'any' or preferred_time in course.recommended_times
        else 45
    )
    difficulty_gap = abs(
        DIFFICULTY_LEVELS[course.difficulty] - min(experience_score, 3)
    )
    difficulty = max(20, 100 - difficulty_gap * 40)

    goal = survey.running_goal
    goal_score = 70
    if goal in {'health', 'stress_relief'}:
        goal_score = 100 if course.difficulty == 'easy' else 60
    elif goal == 'weight_loss':
        goal_score = 90 if course.distance_km >= 4 else 70
    elif goal == 'endurance':
        goal_score = 95 if course.distance_km >= 5 else 65
    elif goal in {'performance', 'race'}:
        goal_score = 100 if course.difficulty in {'normal', 'hard'} else 60

    total = (
        distance * 0.32
        + course_type * 0.25
        + time * 0.15
        + difficulty * 0.18
        + goal_score * 0.10
    )
    return total, {
        'distance': round(distance, 2),
        'course_type': course_type,
        'time': time,
        'difficulty': difficulty,
        'goal': goal_score,
    }


def record_fit(course, record_profile):
    if not record_profile:
        return 0.0, {
            'distance': 0,
            'course_type': 0,
            'difficulty': 0,
        }

    average_distance = record_profile['average_distance_km']
    distance = closeness_score(
        course.distance_km,
        average_distance,
        max(average_distance, 4),
    )
    course_type = (
        100
        if course.course_type == record_profile['preferred_course_type']
        else 50
    )
    difficulty = 90
    if course.difficulty == 'hard' and average_distance < 6:
        difficulty = 40

    total = distance * 0.6 + course_type * 0.25 + difficulty * 0.15
    return total, {
        'distance': round(distance, 2),
        'course_type': course_type,
        'difficulty': difficulty,
    }


def safety_fit(course, survey, record_profile, user_state):
    score = 100.0
    if survey.experience_level == 'beginner':
        if course.difficulty == 'normal':
            score -= 25
        elif course.difficulty == 'hard':
            score -= 60
    if course.elevation_gain_m > 100:
        score -= 25

    if user_state == 'returning' and record_profile:
        safe_distance = record_profile['average_distance_km'] * 0.8
        if float(course.distance_km) > safe_distance:
            score -= min(
                45,
                (float(course.distance_km) - safe_distance) * 10,
            )
        if course.difficulty == 'hard':
            score -= 30

    return max(0.0, score)


def build_reasons(
    course,
    survey,
    survey_details,
    record_profile,
    user_state,
    location_distance_km=None,
):
    reasons = []
    goal = getattr(survey, 'running_goal', '')

    def add_reason(reason):
        if reason not in reasons:
            reasons.append(reason)

    if location_distance_km is not None:
        add_reason(f'현재 위치에서 약 {location_distance_km:g}km 떨어진 코스예요.')
    if user_state == 'returning':
        add_reason('복귀 러닝을 위해 거리와 난이도를 안전하게 보정했어요.')
    if survey_details['course_type'] == 100:
        add_reason(f'선호한 {course.get_course_type_display()} 코스예요.')
    if goal in {'health', 'stress_relief'} and course.difficulty == 'easy':
        add_reason('건강 관리와 스트레스 해소에 맞는 편안한 코스예요.')
    elif goal == 'weight_loss' and float(course.distance_km) >= 4:
        add_reason('체중 관리 목표에 맞춰 충분한 러닝 시간을 확보할 수 있어요.')
    elif goal == 'endurance' and float(course.distance_km) >= 5:
        add_reason('지구력 향상을 위해 긴 호흡으로 달리기 좋아요.')
    elif goal in {'performance', 'race'} and course.difficulty in {'normal', 'hard'}:
        add_reason('기록 향상을 위해 페이스를 끌어올리기 좋은 난이도예요.')
    if survey_details['distance'] >= 75:
        add_reason(f'희망 거리와 가까운 {course.distance_km}km 코스예요.')
    if survey_details['time'] == 100:
        add_reason('선호 시간대에 달리기 좋아요.')
    if record_profile and abs(
        float(course.distance_km) - record_profile['average_distance_km']
    ) <= 1.5:
        add_reason('평소 달리는 거리와 잘 맞아요.')
    if record_profile and course.difficulty == 'hard' and record_profile['longest_distance_km'] >= 7:
        add_reason('긴 거리 경험이 있어 도전 코스로 활용하기 좋아요.')
    if course.elevation_gain_m <= 20 and course.difficulty != 'hard':
        add_reason('고도 변화가 적어 안정적으로 페이스를 유지하기 좋아요.')
    if course.popularity_score >= 100:
        add_reason('다른 러너들도 자주 선택한 검증된 코스예요.')
    if survey.experience_level == 'beginner' and course.difficulty == 'easy':
        add_reason('초보 러너가 부담 없이 시작하기 좋아요.')
    elif survey.experience_level == 'intermediate' and course.difficulty == 'normal':
        add_reason('중급 러너에게 적당한 자극을 주는 코스예요.')
    elif survey.experience_level == 'advanced' and course.difficulty == 'hard':
        add_reason('상급 러너가 훈련 강도를 올리기 좋은 코스예요.')
    if record_profile and course.difficulty != 'hard' and record_profile['average_pace_seconds'] >= 420:
        add_reason('최근 페이스를 고려해 무리 없이 이어가기 좋은 코스예요.')
    if course.elevation_gain_m >= 100:
        add_reason('업힐 구간이 있어 하체 근력과 심폐 자극에 좋아요.')
    if course.course_type == Course.CourseType.RIVER:
        add_reason('강변 코스라 리듬을 유지하며 달리기 좋아요.')
    elif course.course_type == Course.CourseType.PARK:
        add_reason('공원 코스라 회복주와 가벼운 조깅에 잘 맞아요.')
    elif course.course_type == Course.CourseType.TRAIL:
        add_reason('트레일 감각을 느끼며 색다르게 달릴 수 있어요.')
    if not reasons:
        add_reason('현재 러닝 성향과 균형이 좋은 코스예요.')
    return reasons[:4]


@transaction.atomic
def generate_recommendation_session(user, latitude=None, longitude=None):
    survey = user.survey_response
    records = list(
        RunningRecord.objects.filter(
            user=user,
            status=RunningRecord.Status.COMPLETED,
        )
        .select_related('course')
        .order_by('-completed_at')
    )
    weights = resolve_weights(records)
    post_return_records = records_after_latest_gap(records)
    if weights.user_state == 'returning' and post_return_records:
        profile_records = ordered_records(post_return_records)[:20]
    else:
        profile_records = records[:20]
    record_profile = build_record_profile(profile_records)
    location_applied = latitude is not None and longitude is not None

    RecommendationSession.objects.filter(
        user=user,
        is_active=True,
    ).update(is_active=False)

    session = RecommendationSession.objects.create(
        user=user,
        user_state=weights.user_state,
        survey_weight=weights.survey,
        record_weight=weights.record,
        safety_weight=weights.safety,
        record_count=len(records),
        returning_recent_count=weights.returning_recent_count,
        current_latitude=latitude,
        current_longitude=longitude,
        location_priority_weight=location_priority_weight() if location_applied else 0,
    )

    ranked = []
    for course in Course.objects.filter(is_active=True):
        survey_score, survey_details = survey_fit(course, survey)
        record_score, record_details = record_fit(course, record_profile)
        safety_score = safety_fit(
            course,
            survey,
            record_profile,
            weights.user_state,
        )
        personalized_score = (
            survey_score * weights.survey
            + record_score * weights.record
            + safety_score * weights.safety
        )
        location_score, location_distance_km = location_fit(
            course,
            latitude,
            longitude,
        )
        total_score = combine_scores(
            personalized_score,
            location_score,
            course.popularity_score,
            location_applied,
        )
        refresh_jitter = random.SystemRandom().uniform(0, REFRESH_JITTER_MAX)
        total_score = min(100.0, total_score + refresh_jitter)
        reasons = build_reasons(
            course,
            survey,
            survey_details,
            record_profile,
            weights.user_state,
            location_distance_km,
        )
        ranked.append(
            {
                'course': course,
                'total_score': total_score,
                'survey_score': survey_score,
                'record_score': record_score,
                'safety_score': safety_score,
                'location_score': location_score,
                'reasons': reasons,
                'score_details': {
                    'survey': survey_details,
                    'record': record_details,
                    'location': {
                        'applied': location_applied,
                        'distance_km': location_distance_km,
                        'score': round(location_score, 2),
                        'priority_weight': location_priority_weight() if location_applied else 0,
                    },
                    'refresh_jitter': round(refresh_jitter, 2),
                },
            }
        )

    ranked.sort(
        key=lambda item: (
            item['total_score'],
            item['course'].popularity_score,
        ),
        reverse=True,
    )
    ranked = diversify_ranked_courses(ranked, limit=7)

    RecommendationItem.objects.bulk_create(
        [
            RecommendationItem(
                session=session,
                course=item['course'],
                rank=index,
                total_score=round(item['total_score'], 2),
                survey_score=round(item['survey_score'], 2),
                record_score=round(item['record_score'], 2),
                safety_score=round(item['safety_score'], 2),
                location_score=round(item['location_score'], 2),
                reasons=item['reasons'],
                score_details=item['score_details'],
            )
            for index, item in enumerate(ranked, start=1)
        ]
    )
    return session


def get_active_session(user):
    return (
        RecommendationSession.objects.filter(user=user, is_active=True)
        .prefetch_related('items__course')
        .first()
    )


def current_item(session):
    items = list(session.items.all())
    if not items:
        return None
    index = min(session.current_index, len(items) - 1)
    return items[index]


def advance_item(session):
    item_count = session.items.count()
    if not item_count:
        return None
    session.current_index = (session.current_index + 1) % item_count
    session.save(update_fields=['current_index', 'updated_at'])
    return current_item(session)
