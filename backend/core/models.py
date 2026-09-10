from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    class UserType(models.TextChoices):
        NEW = 'new', '신규 사용자'
        ACTIVE = 'active', '기존 사용자'
        RETURNING = 'returning', '복귀 사용자'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    nickname = models.CharField(max_length=12, unique=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.NEW,
    )
    survey_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nickname} ({self.user.email})'


class UserSettings(models.Model):
    class DistanceUnit(models.TextChoices):
        KILOMETERS = 'km', '킬로미터'
        MILES = 'mi', '마일'

    class TemperatureUnit(models.TextChoices):
        CELSIUS = 'c', '섭씨'
        FAHRENHEIT = 'f', '화씨'

    class ProfileVisibility(models.TextChoices):
        PUBLIC = 'public', '전체 공개'
        MEMBERS = 'members', 'RunQuest 회원만'
        PRIVATE = 'private', '비공개'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings',
    )
    push_notifications = models.BooleanField(default=True)
    recommendation_notifications = models.BooleanField(default=True)
    community_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)
    distance_unit = models.CharField(
        max_length=2,
        choices=DistanceUnit.choices,
        default=DistanceUnit.KILOMETERS,
    )
    temperature_unit = models.CharField(
        max_length=1,
        choices=TemperatureUnit.choices,
        default=TemperatureUnit.CELSIUS,
    )
    profile_visibility = models.CharField(
        max_length=10,
        choices=ProfileVisibility.choices,
        default=ProfileVisibility.MEMBERS,
    )
    show_running_records = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} settings'


class SurveyResponse(models.Model):
    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'beginner', '초보자'
        INTERMEDIATE = 'intermediate', '중급자'
        ADVANCED = 'advanced', '상급자'

    class DistanceRange(models.TextChoices):
        UNKNOWN = 'unknown', '잘 모르겠어요'
        SHORT = '1_3km', '1~3km'
        MEDIUM = '3_5km', '3~5km'
        LONG = '5_10km', '5~10km'
        EXTRA_LONG = '10km_plus', '10km 이상'

    class CourseType(models.TextChoices):
        RIVER = 'river', '강/하천 코스'
        PARK = 'park', '공원 코스'
        URBAN = 'urban', '도심 코스'
        TRAIL = 'trail', '산/트레킹 코스'
        COAST = 'coast', '해안 코스'
        ANY = 'any', '상관없음'

    class PreferredTime(models.TextChoices):
        MORNING = 'morning', '아침'
        AFTERNOON = 'afternoon', '오후'
        EVENING = 'evening', '저녁'
        NIGHT = 'night', '야간'
        ANY = 'any', '상관없음'

    class RunningStyle(models.TextChoices):
        SOLO = 'solo', '혼자 뛰기'
        SMALL_GROUP = 'small_group', '소규모로 뛰기'
        CREW = 'crew', '크루와 함께 뛰기'
        ANY = 'any', '상관없음'

    class RunningGoal(models.TextChoices):
        HEALTH = 'health', '건강 관리'
        WEIGHT_LOSS = 'weight_loss', '체중 감량'
        ENDURANCE = 'endurance', '체력 향상'
        STRESS_RELIEF = 'stress_relief', '스트레스 해소'
        PERFORMANCE = 'performance', '기록 향상'
        RACE = 'race', '대회 준비'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='survey_response',
    )
    experience_level = models.CharField(
        max_length=16,
        choices=ExperienceLevel.choices,
    )
    distance_range = models.CharField(
        max_length=16,
        choices=DistanceRange.choices,
    )
    course_type = models.CharField(
        max_length=12,
        choices=CourseType.choices,
    )
    preferred_time = models.CharField(
        max_length=12,
        choices=PreferredTime.choices,
    )
    running_style = models.CharField(
        max_length=16,
        choices=RunningStyle.choices,
    )
    running_goal = models.CharField(
        max_length=16,
        choices=RunningGoal.choices,
    )
    score_profile = models.JSONField(default=dict)
    completed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} 맞춤 추천 설문'


class Course(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', '쉬움'
        NORMAL = 'normal', '보통'
        HARD = 'hard', '어려움'

    class CourseType(models.TextChoices):
        RIVER = 'river', '강/하천'
        PARK = 'park', '공원'
        URBAN = 'urban', '도심'
        TRAIL = 'trail', '산/트레킹'
        LAKE = 'lake', '호수'

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=80)
    summary = models.CharField(max_length=160)
    description = models.TextField()
    district = models.CharField(max_length=30)
    course_type = models.CharField(max_length=12, choices=CourseType.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    distance_km = models.DecimalField(max_digits=4, decimal_places=1)
    estimated_minutes = models.PositiveSmallIntegerField()
    elevation_gain_m = models.PositiveSmallIntegerField(default=0)
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    route_points = models.JSONField(default=list)
    recommended_times = models.JSONField(default=list)
    crowd_level = models.CharField(max_length=20, default='보통')
    image_key = models.CharField(max_length=40)
    tags = models.JSONField(default=list)
    safety_notes = models.JSONField(default=list)
    popularity_score = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-popularity_score', 'distance_km']

    def __str__(self):
        return self.name


class FavoriteCourse(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_courses',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course'],
                name='unique_user_favorite_course',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.course.name}'


class CustomCourse(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = 'private', '비공개'
        PUBLIC = 'public', '공개'

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='custom_courses',
    )
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=300, blank=True)
    distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    elevation_gain_m = models.PositiveIntegerField(default=0)
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    route_points = models.JSONField(default=list)
    source = models.CharField(max_length=20, default='gpx')
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.owner.email} - {self.name}'


class RunningRecord(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', '러닝 중'
        PAUSED = 'paused', '일시정지'
        COMPLETED = 'completed', '완료'
        CANCELLED = 'cancelled', '취소'

    class TrackingMode(models.TextChoices):
        GPS = 'gps', 'GPS'
        SIMULATION = 'simulation', '시뮬레이션'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='running_records',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        related_name='running_records',
        null=True,
        blank=True,
    )
    custom_course = models.ForeignKey(
        CustomCourse,
        on_delete=models.SET_NULL,
        related_name='running_records',
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    tracking_mode = models.CharField(
        max_length=12,
        choices=TrackingMode.choices,
        default=TrackingMode.GPS,
    )
    distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    paused_seconds = models.PositiveIntegerField(default=0)
    average_pace_seconds = models.PositiveIntegerField(default=0)
    calories = models.PositiveIntegerField(default=0)
    track_points = models.JSONField(default=list)
    ai_feedback = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f'{self.user.email} {self.distance_km}km'


class Attendance(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendances',
    )
    date = models.DateField()
    running_record = models.ForeignKey(
        RunningRecord,
        on_delete=models.SET_NULL,
        related_name='attendance_entries',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'date'],
                name='unique_daily_running_attendance',
            ),
        ]

    def __str__(self):
        return f'{self.user.email} {self.date}'


class Badge(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=160)
    icon = models.CharField(max_length=30)
    color = models.CharField(max_length=16, default='#0866ff')
    condition_type = models.CharField(max_length=30)
    condition_value = models.PositiveIntegerField(default=1)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='earned_badges',
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='earned_by',
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-earned_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'badge'],
                name='unique_user_badge',
            ),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.badge.name}'


class Notification(models.Model):
    class Type(models.TextChoices):
        COMMENT = 'comment', '댓글'
        LIKE = 'like', '좋아요'
        BADGE = 'badge', '배지'
        RECOMMENDATION = 'recommendation', '추천'
        SYSTEM = 'system', '시스템'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=80)
    message = models.CharField(max_length=240)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.title}'


class CommunityPost(models.Model):
    class Category(models.TextChoices):
        COURSE = 'course', '코스'
        TIPS = 'tips', '러닝팁'
        TOGETHER = 'together', '같이 뛰어요'
        LOG = 'log', '러닝로그'
        QUESTION = 'question', '질문'

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='community_posts',
    )
    category = models.CharField(max_length=12, choices=Category.choices)
    title = models.CharField(max_length=60)
    content = models.TextField(max_length=5000)
    images = models.JSONField(default=list, blank=True)
    related_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        related_name='community_posts',
        null=True,
        blank=True,
    )
    running_record = models.ForeignKey(
        RunningRecord,
        on_delete=models.SET_NULL,
        related_name='community_posts',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at'], name='post_category_created_idx'),
            models.Index(fields=['-created_at'], name='post_created_idx'),
            models.Index(fields=['related_course', '-created_at'], name='post_course_created_idx'),
        ]

    def __str__(self):
        return self.title


class CommunityComment(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='community_comments',
    )
    content = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at'], name='comment_post_created_idx'),
        ]

    def __str__(self):
        return f'{self.author.email}: {self.content[:30]}'


class CommunityCommentLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='liked_community_comments',
    )
    comment = models.ForeignKey(
        CommunityComment,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['comment', 'user'], name='comment_like_lookup_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'comment'],
                name='unique_community_comment_like',
            ),
        ]


class CommunityPostLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='liked_community_posts',
    )
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'user'], name='post_like_lookup_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_community_post_like',
            ),
        ]


class SavedCommunityPost(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_community_posts',
    )
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='saves',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'user'], name='saved_post_lookup_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_saved_community_post',
            ),
        ]


class ChatSession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
    )
    context = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.email} chat {self.id}'


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', '사용자'
        ASSISTANT = 'assistant', 'AI'

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField(max_length=2000)
    intent = models.CharField(max_length=30, blank=True)
    recommended_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        related_name='chat_recommendations',
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:30]}'


class RecommendationSession(models.Model):
    class UserState(models.TextChoices):
        NEW = 'new', '신규'
        ACTIVE = 'active', '기존'
        RETURNING = 'returning', '복귀'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendation_sessions',
    )
    user_state = models.CharField(max_length=10, choices=UserState.choices)
    survey_weight = models.DecimalField(max_digits=4, decimal_places=2)
    record_weight = models.DecimalField(max_digits=4, decimal_places=2)
    safety_weight = models.DecimalField(max_digits=4, decimal_places=2)
    record_count = models.PositiveIntegerField(default=0)
    returning_recent_count = models.PositiveSmallIntegerField(default=0)
    current_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    current_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    location_priority_weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
    )
    current_index = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} 추천 {self.created_at:%Y-%m-%d}'


class RecommendationItem(models.Model):
    session = models.ForeignKey(
        RecommendationSession,
        on_delete=models.CASCADE,
        related_name='items',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='recommendation_items',
    )
    rank = models.PositiveSmallIntegerField()
    total_score = models.DecimalField(max_digits=6, decimal_places=2)
    survey_score = models.DecimalField(max_digits=6, decimal_places=2)
    record_score = models.DecimalField(max_digits=6, decimal_places=2)
    safety_score = models.DecimalField(max_digits=6, decimal_places=2)
    location_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    reasons = models.JSONField(default=list)
    score_details = models.JSONField(default=dict)

    class Meta:
        ordering = ['rank']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'rank'],
                name='unique_recommendation_rank_per_session',
            ),
            models.UniqueConstraint(
                fields=['session', 'course'],
                name='unique_course_per_recommendation_session',
            ),
        ]

    def __str__(self):
        return f'{self.session_id} #{self.rank} {self.course.name}'
