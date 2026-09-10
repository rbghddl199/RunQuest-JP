from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Course,
    Attendance,
    Badge,
    ChatMessage,
    ChatSession,
    CommunityComment,
    CommunityCommentLike,
    CommunityPost,
    CommunityPostLike,
    CustomCourse,
    FavoriteCourse,
    Notification,
    RecommendationItem,
    RecommendationSession,
    RunningRecord,
    SavedCommunityPost,
    SurveyResponse,
    UserProfile,
    UserSettings,
    UserBadge,
)
from .survey import build_score_profile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('nickname', 'user_type', 'survey_completed')


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'profile')


class UserSettingsSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    nickname = serializers.CharField(
        source='user.profile.nickname',
        min_length=2,
        max_length=12,
    )

    class Meta:
        model = UserSettings
        fields = (
            'email',
            'nickname',
            'push_notifications',
            'recommendation_notifications',
            'community_notifications',
            'marketing_notifications',
            'distance_unit',
            'temperature_unit',
            'profile_visibility',
            'show_running_records',
            'updated_at',
        )
        read_only_fields = ('email', 'updated_at')

    def validate_nickname(self, value):
        nickname = value.strip()
        user = self.context['request'].user
        duplicate = UserProfile.objects.filter(
            nickname__iexact=nickname,
        ).exclude(user=user)
        if duplicate.exists():
            raise serializers.ValidationError('이미 사용 중인 닉네임입니다.')
        return nickname

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        profile_data = user_data.get('profile', {})
        nickname = profile_data.get('nickname')
        if nickname:
            instance.user.profile.nickname = nickname
            instance.user.profile.save(update_fields=['nickname', 'updated_at'])
        return super().update(instance, validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('현재 비밀번호가 올바르지 않습니다.')
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(list(error.messages)) from error
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'notification_type',
            'title',
            'message',
            'link',
            'is_read',
            'metadata',
            'created_at',
        )
        read_only_fields = fields


class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = (
            'experience_level',
            'distance_range',
            'course_type',
            'preferred_time',
            'running_style',
            'running_goal',
            'score_profile',
            'completed_at',
        )
        read_only_fields = ('score_profile', 'completed_at')

    def create(self, validated_data):
        user = self.context['request'].user
        score_profile = build_score_profile(validated_data)
        response, _ = SurveyResponse.objects.update_or_create(
            user=user,
            defaults={
                **validated_data,
                'score_profile': score_profile,
            },
        )
        user.profile.survey_completed = True
        user.profile.save(update_fields=['survey_completed', 'updated_at'])
        return response


class CourseSerializer(serializers.ModelSerializer):
    difficulty_label = serializers.CharField(
        source='get_difficulty_display',
        read_only=True,
    )
    course_type_label = serializers.CharField(
        source='get_course_type_display',
        read_only=True,
    )
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id',
            'slug',
            'name',
            'summary',
            'description',
            'district',
            'course_type',
            'course_type_label',
            'difficulty',
            'difficulty_label',
            'distance_km',
            'estimated_minutes',
            'elevation_gain_m',
            'start_latitude',
            'start_longitude',
            'route_points',
            'recommended_times',
            'crowd_level',
            'image_key',
            'tags',
            'safety_notes',
            'popularity_score',
            'is_favorite',
        )

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        prefetched = getattr(obj, 'user_favorite', None)
        if prefetched is not None:
            return bool(prefetched)
        return FavoriteCourse.objects.filter(
            user=request.user,
            course=obj,
        ).exists()


class CustomCourseSerializer(serializers.ModelSerializer):
    owner_nickname = serializers.CharField(
        source='owner.profile.nickname',
        read_only=True,
    )
    estimated_minutes = serializers.SerializerMethodField()
    difficulty_label = serializers.SerializerMethodField()
    course_type_label = serializers.CharField(default='사용자 코스', read_only=True)
    district = serializers.CharField(default='대전', read_only=True)

    class Meta:
        model = CustomCourse
        fields = (
            'id',
            'owner_nickname',
            'name',
            'description',
            'distance_km',
            'estimated_minutes',
            'difficulty_label',
            'course_type_label',
            'district',
            'elevation_gain_m',
            'start_latitude',
            'start_longitude',
            'route_points',
            'source',
            'visibility',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'owner_nickname',
            'distance_km',
            'elevation_gain_m',
            'start_latitude',
            'start_longitude',
            'route_points',
            'source',
            'created_at',
            'updated_at',
        )

    def get_estimated_minutes(self, obj):
        return max(1, round(float(obj.distance_km) * 7))

    def get_difficulty_label(self, obj):
        if obj.elevation_gain_m >= 150:
            return '어려움'
        if obj.elevation_gain_m >= 60:
            return '보통'
        return '쉬움'


class RecommendationItemSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)

    class Meta:
        model = RecommendationItem
        fields = (
            'rank',
            'total_score',
            'survey_score',
            'record_score',
            'safety_score',
            'location_score',
            'reasons',
            'score_details',
            'course',
        )


class RecommendationSessionSerializer(serializers.ModelSerializer):
    current_position = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    weights = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = RecommendationSession
        fields = (
            'id',
            'user_state',
            'record_count',
            'returning_recent_count',
            'current_position',
            'total_items',
            'weights',
            'location',
            'created_at',
        )

    def get_current_position(self, obj):
        return obj.current_index + 1

    def get_total_items(self, obj):
        return obj.items.count()

    def get_weights(self, obj):
        return {
            'survey': float(obj.survey_weight),
            'record': float(obj.record_weight),
            'safety': float(obj.safety_weight),
        }

    def get_location(self, obj):
        applied = obj.current_latitude is not None and obj.current_longitude is not None
        return {
            'applied': applied,
            'latitude': float(obj.current_latitude) if applied else None,
            'longitude': float(obj.current_longitude) if applied else None,
            'priority_weight': float(obj.location_priority_weight),
        }


class RunningRecordSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    custom_course = CustomCourseSerializer(read_only=True)
    course_slug = serializers.SlugRelatedField(
        source='course',
        slug_field='slug',
        queryset=Course.objects.filter(is_active=True),
        write_only=True,
        required=False,
        allow_null=True,
    )
    custom_course_id = serializers.PrimaryKeyRelatedField(
        source='custom_course',
        queryset=CustomCourse.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = RunningRecord
        fields = (
            'id',
            'course',
            'course_slug',
            'custom_course',
            'custom_course_id',
            'status',
            'tracking_mode',
            'distance_km',
            'duration_seconds',
            'paused_seconds',
            'average_pace_seconds',
            'calories',
            'track_points',
            'ai_feedback',
            'started_at',
            'completed_at',
        )
        read_only_fields = (
            'distance_km',
            'average_pace_seconds',
            'calories',
            'ai_feedback',
            'started_at',
            'completed_at',
        )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            fields['custom_course_id'].queryset = CustomCourse.objects.filter(
                owner=request.user,
            )
        return fields

    def validate(self, attrs):
        if attrs.get('course') and attrs.get('custom_course'):
            raise serializers.ValidationError(
                '기본 코스와 나의 코스를 동시에 선택할 수 없습니다.'
            )
        return attrs


class AttendanceSerializer(serializers.ModelSerializer):
    running_record_id = serializers.IntegerField(
        source='running_record.id',
        read_only=True,
    )

    class Meta:
        model = Attendance
        fields = ('date', 'running_record_id')


class BadgeSerializer(serializers.ModelSerializer):
    earned = serializers.SerializerMethodField()
    earned_at = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = (
            'code',
            'name',
            'description',
            'icon',
            'color',
            'condition_type',
            'condition_value',
            'earned',
            'earned_at',
            'progress',
            'current_value',
        )

    def get_user_badge(self, obj):
        earned_map = self.context.get('earned_map', {})
        return earned_map.get(obj.id)

    def get_earned(self, obj):
        return self.get_user_badge(obj) is not None

    def get_earned_at(self, obj):
        user_badge = self.get_user_badge(obj)
        return user_badge.earned_at if user_badge else None

    def get_progress(self, obj):
        return self.context.get('progress_map', {}).get(obj.id, (0, 0))[0]

    def get_current_value(self, obj):
        return self.context.get('progress_map', {}).get(obj.id, (0, 0))[1]


class CommunityAuthorSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    profile_visible = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'nickname', 'profile_visible')

    def is_visible(self, obj):
        request = self.context.get('request')
        if request and request.user == obj:
            return True
        settings = getattr(obj, 'settings', None)
        if not settings:
            return True
        return settings.profile_visibility != UserSettings.ProfileVisibility.PRIVATE

    def get_nickname(self, obj):
        return obj.profile.nickname if self.is_visible(obj) else '비공개 러너'

    def get_profile_visible(self, obj):
        return self.is_visible(obj)


class CommunityCommentSerializer(serializers.ModelSerializer):
    author = CommunityAuthorSerializer(read_only=True)
    is_mine = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityComment
        fields = (
            'id',
            'author',
            'content',
            'is_mine',
            'can_delete',
            'like_count',
            'is_liked',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'author',
            'is_mine',
            'can_delete',
            'like_count',
            'is_liked',
            'created_at',
            'updated_at',
        )

    def get_is_mine(self, obj):
        request = self.context.get('request')
        return bool(request and request.user == obj.author)

    def get_can_delete(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and (
                request.user == obj.author
                or request.user == obj.post.author
            )
        )

    def get_like_count(self, obj):
        if hasattr(obj, 'like_count_value'):
            return obj.like_count_value
        return obj.likes.count()

    def get_is_liked(self, obj):
        if hasattr(obj, 'is_liked_value'):
            return obj.is_liked_value
        request = self.context.get('request')
        return bool(
            request
            and CommunityCommentLike.objects.filter(
                user=request.user,
                comment=obj,
            ).exists()
        )


class CommunityPostSerializer(serializers.ModelSerializer):
    author = CommunityAuthorSerializer(read_only=True)
    category_label = serializers.CharField(
        source='get_category_display',
        read_only=True,
    )
    related_course = CourseSerializer(read_only=True)
    related_course_slug = serializers.SlugRelatedField(
        source='related_course',
        slug_field='slug',
        queryset=Course.objects.filter(is_active=True),
        write_only=True,
        required=False,
        allow_null=True,
    )
    running_record = RunningRecordSerializer(read_only=True)
    running_record_id = serializers.PrimaryKeyRelatedField(
        source='running_record',
        queryset=RunningRecord.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    comments = CommunityCommentSerializer(many=True, read_only=True)
    images = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        max_length=8,
    )

    class Meta:
        model = CommunityPost
        fields = (
            'id',
            'author',
            'category',
            'category_label',
            'title',
            'content',
            'images',
            'related_course',
            'related_course_slug',
            'running_record',
            'running_record_id',
            'like_count',
            'comment_count',
            'is_liked',
            'is_saved',
            'is_mine',
            'comments',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'author',
            'like_count',
            'comment_count',
            'is_liked',
            'is_saved',
            'is_mine',
            'comments',
            'created_at',
            'updated_at',
        )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if self.context.get('list'):
            fields.pop('comments', None)
            fields.pop('related_course', None)
            fields.pop('running_record', None)
            fields.pop('images', None)
        if request and request.user.is_authenticated:
            fields['running_record_id'].queryset = RunningRecord.objects.filter(
                user=request.user,
                status=RunningRecord.Status.COMPLETED,
            )
        return fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    def get_like_count(self, obj):
        if hasattr(obj, 'like_count_value'):
            return obj.like_count_value
        return obj.likes.count()

    def get_comment_count(self, obj):
        if hasattr(obj, 'comment_count_value'):
            return obj.comment_count_value
        return obj.comments.count()

    def get_is_liked(self, obj):
        if hasattr(obj, 'is_liked_value'):
            return obj.is_liked_value
        request = self.context.get('request')
        return bool(
            request
            and CommunityPostLike.objects.filter(
                user=request.user,
                post=obj,
            ).exists()
        )

    def get_is_saved(self, obj):
        if hasattr(obj, 'is_saved_value'):
            return obj.is_saved_value
        request = self.context.get('request')
        return bool(
            request
            and SavedCommunityPost.objects.filter(
                user=request.user,
                post=obj,
            ).exists()
        )

    def get_is_mine(self, obj):
        request = self.context.get('request')
        return bool(request and request.user == obj.author)

    def validate(self, attrs):
        record = attrs.get('running_record')
        course = attrs.get('related_course')
        if record and course and record.course_id != course.id:
            raise serializers.ValidationError(
                {'running_record_id': '러닝 기록과 연결 코스가 일치하지 않습니다.'}
            )
        if record and not course:
            attrs['related_course'] = record.course
        return attrs


class ChatMessageSerializer(serializers.ModelSerializer):
    recommended_course = CourseSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            'id',
            'role',
            'content',
            'intent',
            'recommended_course',
            'metadata',
            'created_at',
        )


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ('id', 'context', 'messages', 'created_at', 'updated_at')


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    nickname = serializers.CharField(max_length=12)
    terms_agreed = serializers.BooleanField(write_only=True)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError('이미 가입된 이메일입니다.')
        return email

    def validate_nickname(self, value):
        nickname = value.strip()
        if not 2 <= len(nickname) <= 12:
            raise serializers.ValidationError('닉네임은 2~12자로 입력해 주세요.')
        if UserProfile.objects.filter(nickname__iexact=nickname).exists():
            raise serializers.ValidationError('이미 사용 중인 닉네임입니다.')
        return nickname

    def validate_terms_agreed(self, value):
        if not value:
            raise serializers.ValidationError('이용약관과 개인정보 처리방침에 동의해 주세요.')
        return value

    def validate(self, attrs):
        candidate = User(username=attrs.get('email'), email=attrs.get('email'))
        try:
            validate_password(attrs.get('password'), user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'password': list(error.messages)}) from error
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('terms_agreed')
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
        )
        UserProfile.objects.create(
            user=user,
            nickname=validated_data['nickname'],
        )
        return user


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=attrs['password'],
        )

        if user is None:
            raise serializers.ValidationError('이메일 또는 비밀번호가 올바르지 않습니다.')
        if not user.is_active:
            raise serializers.ValidationError('비활성화된 계정입니다.')

        attrs['user'] = user
        return attrs


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
