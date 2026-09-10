from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.models import (
    Attendance,
    Badge,
    CommunityComment,
    CommunityPost,
    CommunityPostLike,
    Course,
    FavoriteCourse,
    Notification,
    RecommendationItem,
    RecommendationSession,
    RunningRecord,
    SavedCommunityPost,
    SurveyResponse,
    UserBadge,
)


PASSWORD_HINT = '!@1q2w3e4r'


def aware(days_ago=0, hour=7, minute=30):
    today = timezone.localdate()
    value = timezone.datetime.combine(
        today - timedelta(days=days_ago),
        timezone.datetime.min.time(),
    ).replace(hour=hour, minute=minute)
    return timezone.make_aware(value)


def get_user(email):
    return User.objects.select_related('profile').get(username=email)


COURSE_ALIASES = {
    'gapcheon-river': ('daejeon-course-01', '갑천 러닝 코스'),
    'hanbat-arboretum': ('daejeon-course-03', '한밭수목원 힐링 코스'),
    'expo-evening': ('daejeon-course-04', '엑스포 시민광장 야간 코스'),
    'daejeoncheon-bridge': ('daejeon-course-11', '대전천 가벼운 코스'),
    'yuseong-stream': ('daejeon-course-08', '유성온천 도심 루프'),
}


def route_loop(latitude, longitude, lat_radius, lon_radius, count=20, wobble=0.0):
    import math

    points = []
    for index in range(count):
        phase = index / count
        angle = 2 * math.pi * phase
        wobble_lat = wobble * ((index % 3) - 1)
        wobble_lon = wobble * (((index + 1) % 3) - 1)
        points.append([
            round(latitude + lat_radius * math.sin(angle) + wobble_lat, 6),
            round(longitude + lon_radius * math.cos(angle) + wobble_lon, 6),
        ])
    points.append(points[0])
    return points


def route_line(latitude, longitude, steps):
    points = [[round(latitude, 6), round(longitude, 6)]]
    current_latitude = latitude
    current_longitude = longitude
    for lat_delta, lon_delta in steps:
        current_latitude += lat_delta
        current_longitude += lon_delta
        points.append([round(current_latitude, 6), round(current_longitude, 6)])
    return points


ENHANCED_COURSES = {
    'daejeon-course-01': {
        'name': '갑천 리버사이드 5K',
        'summary': '엑스포다리와 갑천변을 잇는 평탄한 대표 러닝 코스',
        'description': '갑천 산책로를 따라 달리는 5km 코스입니다. 경사가 거의 없어 초보자와 회복 러닝에 적합하고, 저녁 시간대에도 시야가 넓어 시연용 대표 코스로 쓰기 좋습니다.',
        'difficulty': Course.Difficulty.EASY,
        'elevation_gain_m': 18,
        'tags': ['갑천', '평탄', '초보자', '리버사이드', '저녁 러닝'],
        'safety_notes': ['자전거 통행이 많은 시간대에는 우측 주행을 유지해 주세요.', '교량 아래 구간은 속도를 낮춰 주변을 확인해 주세요.'],
        'route_points': route_loop(36.3566, 127.3591, 0.0030, 0.0032, count=22, wobble=0.00008),
    },
    'daejeon-course-03': {
        'name': '한밭수목원 힐링 루프',
        'summary': '수목원 외곽을 부드럽게 도는 초보자 친화 코스',
        'description': '한밭수목원 주변의 평탄한 보행로를 중심으로 구성한 루프 코스입니다. 상승 고도가 낮고 중간에 쉬어가기 좋아 첫 러닝이나 가벼운 아침 러닝에 잘 맞습니다.',
        'difficulty': Course.Difficulty.EASY,
        'elevation_gain_m': 12,
        'tags': ['한밭수목원', '공원', '초보자', '아침 러닝', '평탄'],
        'safety_notes': ['주말 오전에는 보행자가 많아 추월 시 간격을 확보해 주세요.', '수목원 출입구 주변에서는 속도를 낮춰 주세요.'],
        'route_points': route_loop(36.3695, 127.3896, 0.0024, 0.0028, count=18, wobble=0.00006),
    },
    'daejeon-course-04': {
        'name': '엑스포 시민광장 야간 코스',
        'summary': '조명이 밝고 길 찾기가 쉬운 도심 야간 러닝 코스',
        'description': '엑스포 시민광장과 주변 보행로를 연결한 코스입니다. 고도 변화가 작고 야간 조명이 좋아 퇴근 후 짧은 러닝이나 시뮬레이션 발표에 적합합니다.',
        'difficulty': Course.Difficulty.EASY,
        'elevation_gain_m': 8,
        'tags': ['엑스포', '야간', '도심', '조명', '짧은 코스'],
        'safety_notes': ['행사일에는 광장 일부가 혼잡할 수 있어 우회가 필요합니다.', '횡단 구간에서는 신호를 확인해 주세요.'],
        'route_points': route_loop(36.3761, 127.3918, 0.0021, 0.0022, count=16, wobble=0.00005),
    },
    'daejeon-course-05': {
        'name': '대청호 장거리 빌드업 코스',
        'summary': '완만한 오르내림이 이어지는 장거리 훈련 코스',
        'description': '대청호 주변 도로와 산책 구간을 연결한 장거리 코스입니다. 거리 자체가 길고 완만한 고도 변화가 누적되어 지구력 훈련에 적합합니다.',
        'difficulty': Course.Difficulty.HARD,
        'elevation_gain_m': 72,
        'tags': ['대청호', '장거리', '지구력', '완만한 업다운', '훈련'],
        'safety_notes': ['급수 지점을 미리 확인하고 출발해 주세요.', '일부 구간은 차량 통행과 가까워 밝은 복장이 좋습니다.'],
        'route_points': route_loop(36.4404, 127.4802, 0.0031, 0.0030, count=20, wobble=0.00009),
    },
    'daejeon-course-06': {
        'name': '보문산 업힐 트레이닝',
        'summary': '상승 고도가 큰 상급자용 트레일 훈련 코스',
        'description': '보문산 초입부터 완만한 등산로와 업힐 구간을 연결한 고강도 코스입니다. 상승 고도가 높아 페이스보다 호흡 조절과 안전한 완주가 중요합니다.',
        'difficulty': Course.Difficulty.HARD,
        'elevation_gain_m': 230,
        'tags': ['보문산', '업힐', '트레일', '상급자', '고도 훈련'],
        'safety_notes': ['야간 러닝은 피하고 접지력 좋은 신발을 착용해 주세요.', '내리막에서는 보폭을 줄이고 무릎 부담을 낮춰 주세요.'],
        'route_points': route_line(36.3084, 127.4275, [
            (0.00055, -0.00036), (0.00058, -0.00045), (0.00052, -0.00056),
            (0.00044, -0.00066), (0.00032, -0.00076), (0.00016, -0.00082),
            (-0.00004, -0.00080), (-0.00024, -0.00070), (-0.00042, -0.00055),
            (-0.00058, -0.00036), (-0.00070, -0.00012), (-0.00078, 0.00018),
            (-0.00070, 0.00042), (-0.00054, 0.00060), (-0.00032, 0.00072),
            (-0.00006, 0.00082), (0.00022, 0.00092), (0.00046, 0.00102),
        ]),
    },
    'daejeon-course-07': {
        'name': '월평공원 숲길 러닝',
        'summary': '숲길의 잔잔한 고도 변화가 있는 중급 공원 코스',
        'description': '월평공원 숲길과 외곽 보행로를 연결한 코스입니다. 평지 코스보다 고도 변화가 있어 초보자에게는 살짝 도전적이고, 중급자에게는 안정적인 훈련 코스입니다.',
        'difficulty': Course.Difficulty.NORMAL,
        'elevation_gain_m': 58,
        'tags': ['월평공원', '숲길', '중급', '완만한 경사', '공원'],
        'safety_notes': ['비 온 뒤에는 흙길 구간이 미끄러울 수 있습니다.', '숲길 구간에서는 이어폰 볼륨을 낮춰 주변 소리를 확인해 주세요.'],
        'route_points': route_loop(36.3565, 127.3622, 0.0026, 0.0030, count=20, wobble=0.00008),
    },
    'daejeon-course-11': {
        'name': '대전천 회복 조깅 코스',
        'summary': '짧고 평탄해 복귀 러너에게 적합한 하천 코스',
        'description': '대전천변을 따라 짧게 왕복하는 회복 조깅 코스입니다. 상승 고도가 낮아 오랜만에 다시 뛰는 사용자에게 안전하게 추천하기 좋습니다.',
        'difficulty': Course.Difficulty.EASY,
        'elevation_gain_m': 14,
        'tags': ['대전천', '회복 조깅', '복귀 러너', '짧은 코스', '평탄'],
        'safety_notes': ['비가 온 뒤 하천변 일부가 젖어 있을 수 있습니다.', '교량 진입부에서는 자전거와 보행자를 확인해 주세요.'],
        'route_points': route_loop(36.3343, 127.4286, 0.0020, 0.0028, count=18, wobble=0.00005),
    },
    'daejeon-course-14': {
        'name': '대동하늘공원 전망 업힐',
        'summary': '전망은 좋지만 상승 고도가 뚜렷한 도전 코스',
        'description': '대동하늘공원 방향으로 올라가는 업힐 코스입니다. 거리는 중간 정도지만 상승 고도가 높아 난이도는 어렵게 분류하는 것이 자연스럽습니다.',
        'difficulty': Course.Difficulty.HARD,
        'elevation_gain_m': 118,
        'tags': ['대동하늘공원', '전망', '업힐', '고도 상승', '도전'],
        'safety_notes': ['초반부터 무리하지 말고 업힐 구간에서는 페이스를 낮춰 주세요.', '해가 진 뒤에는 조도가 낮은 구간을 피하는 것이 좋습니다.'],
        'route_points': route_line(36.3292, 127.4536, [
            (0.00042, 0.00036), (0.00045, 0.00044), (0.00042, 0.00052),
            (0.00034, 0.00062), (0.00022, 0.00072), (0.00008, 0.00078),
            (-0.00010, 0.00078), (-0.00028, 0.00070), (-0.00042, 0.00058),
            (-0.00052, 0.00042), (-0.00058, 0.00022), (-0.00052, -0.00010),
            (-0.00040, -0.00036), (-0.00022, -0.00058), (0.00004, -0.00076),
            (0.00030, -0.00086), (0.00048, -0.00092),
        ]),
    },
    'daejeon-course-19': {
        'name': '갑천 장거리 확장 코스',
        'summary': '갑천변을 길게 이어 달리는 중급 장거리 코스',
        'description': '갑천 리버사이드 코스를 더 길게 확장한 중급 코스입니다. 고도 부담은 크지 않지만 거리가 길어 일정한 페이스 유지가 중요합니다.',
        'difficulty': Course.Difficulty.NORMAL,
        'elevation_gain_m': 34,
        'tags': ['갑천', '장거리', '중급', '페이스 유지', '리버사이드'],
        'safety_notes': ['긴 코스이므로 출발 전 급수 계획을 세워 주세요.', '자전거 도로와 가까운 구간에서는 방향 전환에 주의해 주세요.'],
        'route_points': route_loop(36.3568, 127.3576, 0.0040, 0.0047, count=24, wobble=0.00010),
    },
}


def get_course(slug):
    aliases = (slug, *COURSE_ALIASES.get(slug, ()))
    course = Course.objects.filter(slug__in=aliases).first()
    if course:
        return course

    names = [value for value in COURSE_ALIASES.get(slug, ()) if not value.startswith('daejeon-course-')]
    course = Course.objects.filter(name__in=names).first()
    if course:
        return course

    return Course.objects.get(slug=slug)


class Command(BaseCommand):
    help = '발표용 계정의 데이터 흐름을 자연스럽게 보강하고 테스트 문자열을 정리합니다.'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.enhance_representative_courses()
            self.clean_noisy_posts()
            self.polish_main_accounts()
            self.polish_recent_community()
            self.polish_notifications()

        self.stdout.write(self.style.SUCCESS('시연용 데이터 현실감 보강을 완료했습니다.'))
        self.stdout.write(f'대표 로그인: runner@runquest.com / {PASSWORD_HINT}')

    def enhance_representative_courses(self):
        for slug, data in ENHANCED_COURSES.items():
            route_points = data['route_points']
            Course.objects.filter(slug=slug).update(
                name=data['name'],
                summary=data['summary'],
                description=data['description'],
                difficulty=data['difficulty'],
                elevation_gain_m=data['elevation_gain_m'],
                start_latitude=route_points[0][0],
                start_longitude=route_points[0][1],
                route_points=route_points,
                tags=data['tags'],
                safety_notes=data['safety_notes'],
            )

    def clean_noisy_posts(self):
        noisy_posts = CommunityPost.objects.filter(
            Q(title__regex=r'[ㄱ-ㅎㅏ-ㅣ]{2,}')
            | Q(content__regex=r'[ㄱ-ㅎㅏ-ㅣ]{4,}')
            | Q(title__icontains='테스트')
            | Q(content__icontains='테스트')
            | Q(title__icontains='싸피')
        )
        replacements = [
            (
                '갑천 저녁 러닝, 바람이 조금 강했어요',
                '퇴근 후 갑천 쪽으로 30분 정도 뛰었습니다. 바람은 있었지만 길이 넓고 조명이 밝아서 페이스 조절하기 좋았어요.',
            ),
            (
                '한밭수목원 아침 코스 추천합니다',
                '초보자라면 한밭수목원에서 걷기와 조깅을 섞어 시작하기 좋아요. 화장실과 벤치가 가까운 것도 장점입니다.',
            ),
            (
                '오늘은 기록보다 완주에 집중했어요',
                '컨디션이 아주 좋진 않아서 속도를 낮췄습니다. 그래도 미션 하나를 채웠다는 느낌이 있어서 만족스럽네요.',
            ),
        ]
        for index, post in enumerate(noisy_posts.order_by('-created_at'), start=1):
            title, content = replacements[(index - 1) % len(replacements)]
            post.category = CommunityPost.Category.LOG
            post.title = title
            post.content = content
            post.related_course = get_course('gapcheon-river')
            post.updated_at = aware(days_ago=index, hour=21, minute=10)
            post.save(update_fields=['category', 'title', 'content', 'related_course', 'updated_at'])

    def polish_main_accounts(self):
        runner = get_user('runner@runquest.com')
        new_user = get_user('new@runquest.com')
        comeback = get_user('comeback@runquest.com')

        profiles = {
            runner: ('꾸준러너', 'active'),
            new_user: ('새싹러너', 'new'),
            comeback: ('다시러너', 'returning'),
        }
        for user, (nickname, user_type) in profiles.items():
            user.profile.nickname = nickname
            user.profile.user_type = user_type
            user.profile.survey_completed = True
            user.profile.save(update_fields=['nickname', 'user_type', 'survey_completed', 'updated_at'])

        self.ensure_runner_week(runner)
        self.ensure_new_user_story(new_user)
        self.ensure_comeback_story(comeback)

    def ensure_runner_week(self, user):
        courses = [
            ('hanbat-arboretum', 5, Decimal('4.20'), 28 * 60 + 40, 258, 246),
            ('gapcheon-river', 4, Decimal('5.10'), 34 * 60 + 20, 262, 318),
            ('expo-evening', 2, Decimal('3.40'), 23 * 60 + 30, 414, 214),
            ('yuseong-stream', 1, Decimal('6.20'), 41 * 60 + 10, 398, 391),
        ]
        for slug, days_ago, distance, duration, calories, pace in courses:
            course = get_course(slug)
            started_at = aware(days_ago=days_ago, hour=7 if days_ago != 2 else 20, minute=10)
            completed_at = started_at + timedelta(seconds=duration)
            record, _ = RunningRecord.objects.update_or_create(
                user=user,
                course=course,
                completed_at=completed_at,
                defaults={
                    'status': RunningRecord.Status.COMPLETED,
                    'tracking_mode': RunningRecord.TrackingMode.SIMULATION,
                    'distance_km': distance,
                    'duration_seconds': duration,
                    'average_pace_seconds': pace,
                    'calories': calories,
                    'started_at': started_at,
                    'track_points': course.route_points[:18],
                    'ai_feedback': {
                        'summary': '페이스가 안정적으로 유지됐어요.',
                        'highlights': ['초반 오버페이스 없이 출발', '마지막 1km까지 일정한 리듬 유지'],
                        'next_tip': '다음 러닝에서는 5분 워밍업 후 1km만 살짝 빠르게 달려보세요.',
                    },
                },
            )
            Attendance.objects.update_or_create(
                user=user,
                date=completed_at.date(),
                defaults={'running_record': record},
            )

        for slug in ['hanbat-arboretum', 'gapcheon-river', 'expo-evening']:
            FavoriteCourse.objects.get_or_create(user=user, course=get_course(slug))

        for badge in Badge.objects.filter(code__in=['first-run', 'week-streak', 'river-runner']):
            UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={'earned_at': aware(days_ago=3, hour=8, minute=20)},
            )

    def ensure_new_user_story(self, user):
        course = get_course('hanbat-arboretum')
        FavoriteCourse.objects.get_or_create(user=user, course=course)
        SurveyResponse.objects.filter(user=user).update(
            experience_level=SurveyResponse.ExperienceLevel.BEGINNER,
            distance_range=SurveyResponse.DistanceRange.SHORT,
            course_type=SurveyResponse.CourseType.PARK,
            preferred_time=SurveyResponse.PreferredTime.MORNING,
            running_style=SurveyResponse.RunningStyle.SOLO,
            running_goal=SurveyResponse.RunningGoal.HEALTH,
        )

    def ensure_comeback_story(self, user):
        course = get_course('daejeoncheon-bridge')
        old_started = aware(days_ago=44, hour=19, minute=30)
        old_completed = old_started + timedelta(minutes=27, seconds=20)
        RunningRecord.objects.update_or_create(
            user=user,
            course=course,
            completed_at=old_completed,
            defaults={
                'status': RunningRecord.Status.COMPLETED,
                'tracking_mode': RunningRecord.TrackingMode.SIMULATION,
                'distance_km': Decimal('3.10'),
                'duration_seconds': 1640,
                'average_pace_seconds': 529,
                'calories': 188,
                'started_at': old_started,
                'track_points': course.route_points[:14],
                'ai_feedback': {
                    'summary': '복귀 러닝으로 무리 없이 마무리했어요.',
                    'highlights': ['짧은 거리로 안전하게 재시작', '후반 페이스 급락 없음'],
                    'next_tip': '이번 주는 3km 안팎으로 2회만 뛰어도 충분합니다.',
                },
            },
        )

    def polish_recent_community(self):
        runner = get_user('runner@runquest.com')
        new_user = get_user('new@runquest.com')
        comeback = get_user('comeback@runquest.com')

        post_specs = [
            (
                runner,
                CommunityPost.Category.LOG,
                '이번 주는 갑천 5km까지 무리 없이 왔어요',
                '월요일에는 3km도 조금 버거웠는데 오늘은 호흡이 훨씬 안정적이었습니다. '
                '미션을 하나씩 채우는 느낌이라 계속 뛰게 되네요.',
                'gapcheon-river',
                1,
                20,
            ),
            (
                new_user,
                CommunityPost.Category.QUESTION,
                '초보자는 한밭수목원 몇 바퀴부터 시작하면 좋을까요?',
                '아침에 20분 정도만 뛰어보려고 합니다. 걷기랑 섞어서 시작해도 괜찮을지 궁금해요.',
                'hanbat-arboretum',
                2,
                10,
            ),
            (
                comeback,
                CommunityPost.Category.TIPS,
                '한 달 쉬고 다시 뛸 때 도움 됐던 방법',
                '첫 주는 기록 욕심을 버리고 짧은 코스만 골랐습니다. '
                'RunQuest가 회복 조깅 위주로 추천해줘서 부담이 덜했어요.',
                'daejeoncheon-bridge',
                3,
                9,
            ),
        ]

        for author, category, title, content, slug, days_ago, hour in post_specs:
            course = get_course(slug)
            post, _ = CommunityPost.objects.update_or_create(
                author=author,
                title=title,
                defaults={
                    'category': category,
                    'content': content,
                    'related_course': course,
                    'created_at': aware(days_ago=days_ago, hour=hour, minute=15),
                    'updated_at': aware(days_ago=days_ago, hour=hour, minute=15),
                },
            )
            CommunityPost.objects.filter(pk=post.pk).update(
                created_at=aware(days_ago=days_ago, hour=hour, minute=15),
                updated_at=aware(days_ago=days_ago, hour=hour, minute=15),
            )

        self.ensure_comments_and_reactions()

    def ensure_comments_and_reactions(self):
        runner = get_user('runner@runquest.com')
        new_user = get_user('new@runquest.com')
        comeback = get_user('comeback@runquest.com')
        posts = CommunityPost.objects.filter(
            title__in=[
                '이번 주는 갑천 5km까지 무리 없이 왔어요',
                '초보자는 한밭수목원 몇 바퀴부터 시작하면 좋을까요?',
                '한 달 쉬고 다시 뛸 때 도움 됐던 방법',
            ],
        )
        comment_specs = {
            '이번 주는 갑천 5km까지 무리 없이 왔어요': [
                (new_user, '저도 이번 주부터 3km 미션 시작했어요. 페이스보다 꾸준함이 먼저네요.'),
                (comeback, '복귀할 때 이런 기록 보면 동기부여 됩니다. 무리 없이 가는 게 제일 좋더라구요.'),
            ],
            '초보자는 한밭수목원 몇 바퀴부터 시작하면 좋을까요?': [
                (runner, '처음이면 한 바퀴를 걷기 2분, 달리기 3분으로 나눠도 충분해요.'),
                (comeback, '아침 시간대가 덜 붐벼서 시작하기 좋아요.'),
            ],
            '한 달 쉬고 다시 뛸 때 도움 됐던 방법': [
                (runner, '저도 쉬었다가 돌아올 때 짧은 코스부터 다시 잡는 게 제일 도움 됐어요.'),
            ],
        }
        for post in posts:
            for author, content in comment_specs.get(post.title, []):
                CommunityComment.objects.get_or_create(
                    post=post,
                    author=author,
                    content=content,
                )
            for user in [runner, new_user, comeback]:
                if user != post.author:
                    CommunityPostLike.objects.get_or_create(user=user, post=post)
                    SavedCommunityPost.objects.get_or_create(user=user, post=post)

    def polish_notifications(self):
        runner = get_user('runner@runquest.com')
        notifications = [
            (
                Notification.Type.RECOMMENDATION,
                '오늘은 갑천 리버사이드가 잘 맞아요',
                '최근 페이스와 선호도를 반영해 5km 강변 코스를 추천했어요.',
                '/recommendations',
                False,
                0,
                8,
            ),
            (
                Notification.Type.COMMENT,
                '게시글에 새 댓글이 달렸어요',
                '새싹러너님이 “이번 주는 갑천 5km까지 무리 없이 왔어요”에 댓글을 남겼습니다.',
                '/community',
                False,
                1,
                21,
            ),
            (
                Notification.Type.BADGE,
                '공원 루틴러 배지를 획득했어요',
                '최근 공원 코스 러닝 기록이 쌓여 새 배지가 열렸습니다.',
                '/my/badges',
                True,
                3,
                8,
            ),
            (
                Notification.Type.SYSTEM,
                '이번 주 미션이 갱신됐어요',
                '짧은 러닝, 추천 코스, 커뮤니티 공유 미션을 이번 주 안에 완료해 보세요.',
                '/home',
                True,
                4,
                9,
            ),
        ]

        Notification.objects.filter(user=runner).delete()
        for notification_type, title, message, link, is_read, days_ago, hour in notifications:
            item = Notification.objects.create(
                user=runner,
                notification_type=notification_type,
                title=title,
                message=message,
                link=link,
                is_read=is_read,
                metadata={'demo': True},
            )
            Notification.objects.filter(pk=item.pk).update(
                created_at=aware(days_ago=days_ago, hour=hour, minute=25),
            )

        session = RecommendationSession.objects.filter(user=runner).first()
        if session:
            session.user_state = RecommendationSession.UserState.ACTIVE
            session.record_count = RunningRecord.objects.filter(
                user=runner,
                status=RunningRecord.Status.COMPLETED,
            ).count()
            session.current_latitude = Decimal('36.362320')
            session.current_longitude = Decimal('127.344850')
            session.location_priority_weight = Decimal('0.18')
            session.save(update_fields=[
                'user_state',
                'record_count',
                'current_latitude',
                'current_longitude',
                'location_priority_weight',
                'updated_at',
            ])
            first_item = RecommendationItem.objects.filter(session=session).first()
            if first_item:
                first_item.reasons = [
                    '최근 5km 안팎의 강변 러닝을 꾸준히 완료했어요.',
                    '아침과 저녁 모두 접근성이 좋은 코스라 이번 주 미션과 잘 맞아요.',
                    '현재 위치 기준으로 이동 부담이 낮은 편입니다.',
                ]
                first_item.score_details = {
                    **(first_item.score_details or {}),
                    'demo_note': '시연용 대표 사용자 흐름에 맞춰 보강된 추천 이유입니다.',
                }
                first_item.save(update_fields=['reasons', 'score_details'])
