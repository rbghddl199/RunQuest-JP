import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'backend' / 'fixtures' / 'source'
OUTPUT = ROOT / 'backend' / 'fixtures' / 'runquest'


def load(name):
    return json.loads((SOURCE / name).read_text(encoding='utf-8'))


def save(name, objects):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(
        json.dumps(objects, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def fixture(model, pk, **fields):
    return {'model': model, 'pk': pk, 'fields': fields}


def kst(value):
    if not value:
        return value
    return value if value.endswith(('Z', '+09:00')) else f'{value}+09:00'


def parse_datetime(value):
    return datetime.fromisoformat(kst(value))


def pace_seconds(value):
    match = re.match(r"(\d+)'(\d+)\"", value)
    return int(match.group(1)) * 60 + int(match.group(2))


def route_pairs(points):
    return [[point['lat'], point['lng']] for point in points]


def track_points(points, started_at, duration):
    interval = duration / max(1, len(points) - 1)
    return [
        {
            'latitude': point['lat'],
            'longitude': point['lng'],
            'accuracy': 8,
            'timestamp': round(
                (started_at + timedelta(seconds=index * interval)).timestamp() * 1000
            ),
        }
        for index, point in enumerate(points)
    ]


def survey_profile(fields):
    distance_map = {
        '1_3': ('1_3km', 2.0),
        '3_5': ('3_5km', 4.0),
        '5_10': ('5_10km', 7.5),
        '10_plus': ('10km_plus', 12.0),
    }
    goal_map = {
        'health': 'health',
        'stress': 'stress_relief',
        'stamina': 'endurance',
        'record': 'performance',
    }
    goal = goal_map[fields['purpose']]
    distance_range, target_distance = distance_map[fields['distance']]
    experience_score = {
        'beginner': 1,
        'intermediate': 2,
        'advanced': 3,
    }[fields['experience']]
    goal_profiles = {
        'health': {'intensity': 1, 'pace_focus': 0.3, 'recovery_focus': 0.8},
        'stress_relief': {'intensity': 1, 'pace_focus': 0.2, 'recovery_focus': 1.0},
        'endurance': {'intensity': 2, 'pace_focus': 0.6, 'recovery_focus': 0.4},
        'performance': {'intensity': 3, 'pace_focus': 1.0, 'recovery_focus': 0.3},
    }
    normalized = {
        'experience_level': fields['experience'],
        'distance_range': distance_range,
        'course_type': fields['course_type'],
        'preferred_time': fields['time_zone'],
        'running_style': 'solo',
        'running_goal': goal,
    }
    profile = {
        'experience_score': experience_score,
        'target_distance_km': target_distance,
        'preferred_course_types': [fields['course_type']],
        'preferred_time': fields['time_zone'],
        'social_preference': 'solo',
        'goal': goal,
        'goal_profile': goal_profiles[goal],
        'safety_adjustment': 0.85 if fields['experience'] == 'beginner' else 1.0,
        'survey_weight': 1.0,
        'record_weight': 0.0,
    }
    return normalized, profile


def build_users(users, surveys, records):
    record_dates = {}
    for item in records:
        record_dates.setdefault(item['fields']['user'], []).append(
            parse_datetime(item['fields']['created_at'])
        )
    survey_users = {item['fields']['user'] for item in surveys}
    objects = []
    for item in users:
        pk = item['pk']
        fields = item['fields']
        dates = sorted(record_dates.get(pk, []), reverse=True)
        if not dates:
            user_type = 'new'
        elif datetime(2026, 6, 22, tzinfo=dates[0].tzinfo) - dates[0] >= timedelta(days=30):
            user_type = 'returning'
        else:
            user_type = 'active'
        objects.extend([
            fixture(
                'auth.user',
                pk,
                password=fields['password'],
                last_login=fields['last_login'],
                is_superuser=fields['is_superuser'],
                username=fields['username'],
                first_name=fields['first_name'],
                last_name=fields['last_name'],
                email=fields['email'],
                is_staff=fields['is_staff'],
                is_active=fields['is_active'],
                date_joined=kst(fields['date_joined']),
                groups=[],
                user_permissions=[],
            ),
            fixture(
                'core.userprofile',
                pk,
                user=pk,
                nickname=fields['nickname'],
                user_type=user_type,
                survey_completed=pk in survey_users,
                created_at=kst(fields['date_joined']),
                updated_at=kst(fields['date_joined']),
            ),
            fixture(
                'core.usersettings',
                pk,
                user=pk,
                push_notifications=True,
                recommendation_notifications=True,
                community_notifications=True,
                marketing_notifications=False,
                distance_unit='km',
                temperature_unit='c',
                profile_visibility='members',
                show_running_records=True,
                updated_at=kst(fields['date_joined']),
            ),
        ])
    return objects


def build_courses(source):
    type_map = {'river': 'river', 'park': 'park', 'city': 'urban', 'mountain': 'trail'}
    difficulty_map = {'beginner': 'easy', 'intermediate': 'normal', 'advanced': 'hard'}
    crowd_map = {'low': '적음', 'medium': '보통', 'high': '많음'}
    image_map = {'river': 'gapcheon-river', 'park': 'hanbat-arboretum', 'city': 'expo-evening', 'mountain': 'hanbat-arboretum'}
    objects = []
    for item in source:
        fields = item['fields']
        recommended_times = ['morning', 'evening']
        if fields['night_recommend']:
            recommended_times.append('night')
        safety_notes = [
            f"보행로 비율 {fields['sidewalk_ratio']}%",
            f"안전 점수 {fields['safety_score']}/5",
        ]
        if fields['toilet']:
            safety_notes.append('코스 인근 화장실 이용 가능')
        if fields['parking']:
            safety_notes.append('주차 공간 이용 가능')
        objects.append(fixture(
            'core.course',
            item['pk'],
            slug=f"daejeon-course-{item['pk']:02d}",
            name=fields['name'],
            summary=fields['subtitle'],
            description=fields['description'],
            district=fields['district'].replace('대전 ', ''),
            course_type=type_map[fields['course_type']],
            difficulty=difficulty_map[fields['level']],
            distance_km=round(fields['distance_km'], 1),
            estimated_minutes=fields['expected_time'],
            elevation_gain_m=0,
            start_latitude=fields['start_lat'],
            start_longitude=fields['start_lng'],
            route_points=route_pairs(fields['route_points']),
            recommended_times=recommended_times,
            crowd_level=crowd_map[fields['crowd_level']],
            image_key=image_map[fields['course_type']],
            tags=[
                fields['location'],
                f"풍경 {fields['scenic_score']}/5",
                f"안전 {fields['safety_score']}/5",
            ],
            safety_notes=safety_notes,
            popularity_score=fields['likes'],
            is_active=fields['is_active'],
            created_at=kst(fields['created_at']),
            updated_at=kst(fields['created_at']),
        ))
    return objects


def build_badges(source):
    condition_map = {
        1: ('first-finish', 'run_count', '#ff6b35'),
        2: ('seven-day-streak', 'attendance_streak', '#ff6b35'),
        3: ('thirty-day-streak', 'attendance_streak', '#7b4ce2'),
        4: ('night-runner-five', 'night_run', '#7257e8'),
        5: ('river-master', 'river_run', '#168fe5'),
        6: ('park-regular', 'park_run', '#43a833'),
        7: ('speed-runner', 'fast_run', '#8a4fff'),
        8: ('ten-kilometer-finish', 'long_run', '#0866ff'),
        9: ('daejeon-explorer', 'distinct_course', '#12a58c'),
        10: ('first-community-post', 'community_post', '#f07a28'),
    }
    return [
        fixture(
            'core.badge',
            item['pk'],
            code=condition_map[item['pk']][0],
            name=item['fields']['name'],
            description=item['fields']['description'],
            icon=item['fields']['icon_type'],
            color=condition_map[item['pk']][2],
            condition_type=condition_map[item['pk']][1],
            condition_value=item['fields']['required_value'],
            sort_order=item['pk'],
        )
        for item in source
    ]


def build_surveys(source):
    objects = []
    for item in source:
        fields = item['fields']
        normalized, profile = survey_profile(fields)
        objects.append(fixture(
            'core.surveyresponse',
            item['pk'],
            user=fields['user'],
            **normalized,
            score_profile=profile,
            completed_at=kst(fields['created_at']),
        ))
    return objects


def build_records(source):
    objects = []
    for item in source:
        fields = item['fields']
        completed_at = parse_datetime(fields['created_at'])
        started_at = completed_at - timedelta(seconds=fields['duration_seconds'])
        pace = pace_seconds(fields['avg_pace'])
        next_distance = round(min(fields['distance_km'] * 1.08, fields['distance_km'] + 0.5), 1)
        feedback = {
            'score': 75,
            'headline': fields['ai_feedback'],
            'summary': (
                f"{fields['distance_km']:.2f}km를 평균 {fields['avg_pace']}/km로 달렸어요. "
                'fixture 기록을 바탕으로 저장된 러닝 분석입니다.'
            ),
            'achievements': [fields['memo']],
            'cautions': ['통증이 느껴지면 기록보다 회복을 먼저 선택하세요.'],
            'next_goal': {
                'distance_km': next_distance,
                'pace_seconds': max(240, round(pace * 0.98)),
                'message': f'다음에는 {next_distance:.1f}km를 편안하게 달려보세요.',
            },
            'comparison': {
                'history_count': 0,
                'distance_change_percent': None,
                'pace_change_percent': None,
            },
            'provider': 'fixture',
        }
        objects.append(fixture(
            'core.runningrecord',
            item['pk'],
            user=fields['user'],
            course=fields['course'],
            custom_course=None,
            status='completed',
            tracking_mode='gps',
            distance_km=fields['distance_km'],
            duration_seconds=fields['duration_seconds'],
            paused_seconds=0,
            average_pace_seconds=pace,
            calories=fields['calories'],
            track_points=track_points(
                fields['route_points'],
                started_at,
                fields['duration_seconds'],
            ),
            ai_feedback=feedback,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            created_at=started_at.isoformat(),
        ))
    return objects


def build_attendance(source):
    return [
        fixture(
            'core.attendance',
            item['pk'],
            user=item['fields']['user'],
            date=item['fields']['date'],
            running_record=item['fields']['record'],
            created_at=f"{item['fields']['date']}T23:00:00+09:00",
        )
        for item in source
    ]


def build_saved_courses(source):
    return [
        fixture(
            'core.favoritecourse',
            item['pk'],
            user=item['fields']['user'],
            course=item['fields']['course'],
            created_at=kst(item['fields']['created_at']),
        )
        for item in source
    ]


def build_user_badges(source):
    return [
        fixture(
            'core.userbadge',
            item['pk'],
            user=item['fields']['user'],
            badge=item['fields']['badge'],
            earned_at=kst(item['fields']['acquired_at']),
        )
        for item in source
    ]


def build_posts(source):
    return [
        fixture(
            'core.communitypost',
            item['pk'],
            author=item['fields']['user'],
            category='tips' if item['fields']['category'] == 'tip' else item['fields']['category'],
            title=item['fields']['title'],
            content=item['fields']['content'],
            related_course=item['fields']['course'],
            running_record=None,
            created_at=kst(item['fields']['created_at']),
            updated_at=kst(item['fields']['updated_at']),
        )
        for item in source
    ]


def build_comments(source):
    return [
        fixture(
            'core.communitycomment',
            item['pk'],
            post=item['fields']['post'],
            author=item['fields']['user'],
            content=item['fields']['content'],
            created_at=kst(item['fields']['created_at']),
            updated_at=kst(item['fields']['created_at']),
        )
        for item in source
    ]


def build_likes(source, post_dates):
    return [
        fixture(
            'core.communitypostlike',
            item['pk'],
            user=item['fields']['user'],
            post=item['fields']['post'],
            created_at=(
                parse_datetime(post_dates[item['fields']['post']])
                + timedelta(minutes=item['pk'])
            ).isoformat(),
        )
        for item in source
    ]


def build_bookmarks(source):
    return [
        fixture(
            'core.savedcommunitypost',
            item['pk'],
            user=item['fields']['user'],
            post=item['fields']['post'],
            created_at=kst(item['fields']['created_at']),
        )
        for item in source
    ]


def build_chat(source):
    user_ids = sorted({item['fields']['user'] for item in source})
    session_ids = {user_id: index for index, user_id in enumerate(user_ids, start=1)}
    sessions = []
    for user_id in user_ids:
        messages = [
            item for item in source if item['fields']['user'] == user_id
        ]
        sessions.append(fixture(
            'core.chatsession',
            session_ids[user_id],
            user=user_id,
            context={},
            is_active=True,
            created_at=kst(messages[0]['fields']['created_at']),
            updated_at=kst(messages[-1]['fields']['created_at']),
        ))
    chat_messages = [
        fixture(
            'core.chatmessage',
            item['pk'],
            session=session_ids[item['fields']['user']],
            role=item['fields']['role'],
            content=item['fields']['content'],
            intent=(
                'course_recommendation'
                if item['fields']['recommended_course']
                else 'small_talk'
            ),
            recommended_course=item['fields']['recommended_course'],
            metadata={
                'provider': 'fixture',
                'reasons': [],
                'context': {},
            },
            created_at=kst(item['fields']['created_at']),
        )
        for item in source
    ]
    return sessions + chat_messages


def build_recommendations(source, record_counts):
    sessions = []
    items = []
    for item in source:
        fields = item['fields']
        source_type = fields['recommend_type']
        count = record_counts[fields['user']]
        if source_type == 'new':
            state, survey, record, safety = 'new', 1.0, 0.0, 0.0
        elif source_type == 'returning':
            state, survey, record, safety = 'returning', 0.5, 0.3, 0.2
        else:
            state = 'active'
            record = round(0.9 * min(count, 20) / 20, 2)
            survey, safety = round(1 - record, 2), 0.0
        sessions.append(fixture(
            'core.recommendationsession',
            item['pk'],
            user=fields['user'],
            user_state=state,
            survey_weight=survey,
            record_weight=record,
            safety_weight=safety,
            record_count=count,
            returning_recent_count=0,
            current_latitude=None,
            current_longitude=None,
            location_priority_weight=0,
            current_index=0,
            is_active=False,
            created_at=kst(fields['created_at']),
            updated_at=kst(fields['created_at']),
        ))
        items.append(fixture(
            'core.recommendationitem',
            item['pk'],
            session=item['pk'],
            course=fields['course'],
            rank=1,
            total_score=fields['score'],
            survey_score=round(fields['score'] * survey, 2),
            record_score=round(fields['score'] * record, 2),
            safety_score=round(fields['score'] * safety, 2),
            location_score=0,
            reasons=[fields['reason']],
            score_details={
                'source': 'fixture',
                'recommend_type': source_type,
            },
        ))
    return sessions + items


def main():
    users = load('01_users.json')
    courses = load('02_courses.json')
    badges = load('03_badges.json')
    surveys = load('04_surveys.json')
    records = load('05_running_records.json')
    attendance = load('06_attendance.json')
    saved_courses = load('07_saved_courses.json')
    user_badges = load('08_user_badges.json')
    posts = load('09_posts.json')
    comments = load('10_comments.json')
    likes = load('11_post_likes.json')
    bookmarks = load('12_post_bookmarks.json')
    chat = load('13_chatbot_history.json')
    recommendations = load('14_recommend_history.json')

    post_dates = {
        item['pk']: item['fields']['created_at'] for item in posts
    }
    record_counts = Counter(item['fields']['user'] for item in records)

    converted = {
        '01_users.json': build_users(users, surveys, records),
        '02_courses.json': build_courses(courses),
        '03_badges.json': build_badges(badges),
        '04_surveys.json': build_surveys(surveys),
        '05_running_records.json': build_records(records),
        '06_attendance.json': build_attendance(attendance),
        '07_saved_courses.json': build_saved_courses(saved_courses),
        '08_user_badges.json': build_user_badges(user_badges),
        '09_posts.json': build_posts(posts),
        '10_comments.json': build_comments(comments),
        '11_post_likes.json': build_likes(likes, post_dates),
        '12_post_bookmarks.json': build_bookmarks(bookmarks),
        '13_chatbot_history.json': build_chat(chat),
        '14_recommend_history.json': build_recommendations(
            recommendations,
            record_counts,
        ),
    }
    for name, objects in converted.items():
        save(name, objects)
        print(f'{name}: {len(objects)} objects')


if __name__ == '__main__':
    main()
