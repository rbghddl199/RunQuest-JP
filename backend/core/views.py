from calendar import monthrange
from datetime import date
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Prefetch, Q, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework import serializers as drf_serializers
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .models import (
    Attendance,
    Badge,
    ChatMessage,
    ChatSession,
    CommunityComment,
    CommunityCommentLike,
    CommunityPost,
    CommunityPostLike,
    Course,
    CustomCourse,
    FavoriteCourse,
    Notification,
    RunningRecord,
    SavedCommunityPost,
    SurveyResponse,
    UserProfile,
    UserSettings,
    UserBadge,
)
from .badges import (
    award_eligible_badges,
    badge_progress,
    current_attendance_streak,
)
from .chatbot import build_assistant_reply
from .gpx import GpxValidationError, parse_gpx, validate_route_points
from .missions import build_weekly_mission
from .notifications import create_notification
from .performance import time_block
from .profile_style import build_profile_style, build_running_profile
from .feedback import generate_run_feedback
from .recommendations import (
    advance_item,
    build_home_course_recommendations,
    current_item,
    generate_recommendation_session,
    get_active_session,
)
from .running import calculate_run_stats, normalize_track_points
from .serializers import (
    AttendanceSerializer,
    BadgeSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
    CommunityCommentSerializer,
    CommunityPostSerializer,
    CustomCourseSerializer,
    EmailLoginSerializer,
    CourseSerializer,
    RecommendationItemSerializer,
    RecommendationSessionSerializer,
    NotificationSerializer,
    RunningRecordSerializer,
    SignupSerializer,
    SurveyResponseSerializer,
    UserSerializer,
    UserSettingsSerializer,
    PasswordChangeSerializer,
    get_tokens_for_user,
)
from .survey import SURVEY_QUESTIONS
from .weather import fetch_daejeon_weather

MIN_COMPLETED_RUN_DISTANCE_KM = 0.1


class EmptySerializer(drf_serializers.Serializer):
    pass


class RunQuestAPIView(GenericAPIView):
    serializer_class = EmptySerializer


@extend_schema(responses=EmptySerializer)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response(
        {
            'status': 'ok',
            'service': 'RunQuest API',
            'version': '0.1.0',
        }
    )


class HomeDashboardView(RunQuestAPIView):
    def get(self, request):
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        completed_records = RunningRecord.objects.filter(
            user=request.user,
            status=RunningRecord.Status.COMPLETED,
        ).select_related('course', 'custom_course')
        recent_record = completed_records.first()
        mission = build_weekly_mission(request.user, completed_records, week_start)
        active_run = RunningRecord.objects.filter(
            user=request.user,
            status__in=[
                RunningRecord.Status.ACTIVE,
                RunningRecord.Status.PAUSED,
            ],
        ).select_related('course', 'custom_course').first()

        home_course_items = build_home_course_recommendations(request.user, today=today)
        recommendation_items = [
            {
                **item,
                'course': CourseSerializer(
                    item['course'],
                    context={'request': request},
                ).data,
            }
            for item in home_course_items
        ]
        recommendation = recommendation_items[0] if recommendation_items else None

        return Response({
            'user': UserSerializer(request.user).data,
            'weather': fetch_daejeon_weather(latitude, longitude),
            'recommendation': recommendation,
            'recommendations': recommendation_items,
            'mission': mission,
            'attendance': {
                'checked_today': Attendance.objects.filter(
                    user=request.user,
                    date=today,
                ).exists(),
                'streak_days': current_attendance_streak(request.user),
            },
            'recent_record': (
                RunningRecordSerializer(
                    recent_record,
                    context={'request': request},
                ).data
                if recent_record else None
            ),
            'active_run': (
                RunningRecordSerializer(
                    active_run,
                    context={'request': request},
                ).data
                if active_run else None
            ),
        })


class CurrentWeatherView(RunQuestAPIView):
    def get(self, request):
        return Response(fetch_daejeon_weather(
            request.query_params.get('latitude'),
            request.query_params.get('longitude'),
        ))


class SignupView(RunQuestAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                'user': UserSerializer(user).data,
                'tokens': get_tokens_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(RunQuestAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        return Response(
            {
                'user': UserSerializer(user).data,
                'tokens': get_tokens_for_user(user),
            }
        )


class LogoutView(RunQuestAPIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'refresh': ['로그아웃할 refresh 토큰이 필요합니다.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            return Response(
                {'refresh': ['유효하지 않은 refresh 토큰입니다.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserSettingsView(RunQuestAPIView):
    def get_object(self, request):
        settings, _ = UserSettings.objects.get_or_create(user=request.user)
        return settings

    def get(self, request):
        serializer = UserSettingsSerializer(
            self.get_object(request),
            context={'request': request},
        )
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSettingsSerializer(
            self.get_object(request),
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordChangeView(RunQuestAPIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': '비밀번호가 변경되었습니다.'})


class NicknameAvailabilityView(RunQuestAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        nickname = request.query_params.get('nickname', '').strip()
        if not 2 <= len(nickname) <= 12:
            return Response(
                {
                    'available': False,
                    'message': '닉네임은 2~12자로 입력해 주세요.',
                }
            )

        available = not UserProfile.objects.filter(
            nickname__iexact=nickname,
        ).exists()
        message = (
            '사용 가능한 닉네임입니다.'
            if available
            else '이미 사용 중인 닉네임입니다.'
        )

        return Response({'available': available, 'message': message})


class SurveyQuestionsView(RunQuestAPIView):
    def get(self, request):
        return Response({'questions': SURVEY_QUESTIONS})


class SurveyResponseView(RunQuestAPIView):
    def get(self, request):
        try:
            survey_response = request.user.survey_response
        except SurveyResponse.DoesNotExist:
            return Response(
                {'detail': '아직 완료한 설문이 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(SurveyResponseSerializer(survey_response).data)

    def post(self, request):
        serializer = SurveyResponseSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        survey_response = serializer.save()

        return Response(
            {
                'survey': SurveyResponseSerializer(survey_response).data,
                'user': UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


class CourseListView(RunQuestAPIView):
    def get(self, request):
        queryset = Course.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'favorited_by',
                queryset=FavoriteCourse.objects.filter(user=request.user),
                to_attr='user_favorite',
            )
        )

        course_type = request.query_params.get('type')
        difficulty = request.query_params.get('difficulty')
        saved_only = request.query_params.get('saved') == 'true'

        if course_type:
            queryset = queryset.filter(course_type=course_type)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if saved_only:
            queryset = queryset.filter(favorited_by__user=request.user)

        serializer = CourseSerializer(
            queryset.distinct(),
            many=True,
            context={'request': request},
        )
        return Response({'courses': serializer.data})


class CourseDetailView(RunQuestAPIView):
    def get(self, request, slug):
        try:
            course = Course.objects.get(slug=slug, is_active=True)
        except Course.DoesNotExist:
            return Response(
                {'detail': '코스를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            CourseSerializer(course, context={'request': request}).data
        )


class FavoriteCourseView(RunQuestAPIView):
    def post(self, request, slug):
        try:
            course = Course.objects.get(slug=slug, is_active=True)
        except Course.DoesNotExist:
            return Response(
                {'detail': '코스를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        _, created = FavoriteCourse.objects.get_or_create(
            user=request.user,
            course=course,
        )
        return Response(
            {'is_favorite': True},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, slug):
        FavoriteCourse.objects.filter(
            user=request.user,
            course__slug=slug,
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomCourseListCreateView(RunQuestAPIView):
    def get(self, request):
        courses = CustomCourse.objects.filter(
            owner=request.user,
        ).select_related('owner__profile')
        return Response(
            CustomCourseSerializer(courses, many=True).data
        )

    def post(self, request):
        upload = request.FILES.get('gpx_file')
        try:
            if upload:
                parsed = parse_gpx(upload)
                source = 'gpx'
            else:
                parsed = validate_route_points(request.data.get('route_points'))
                source = 'drawn'
        except GpxValidationError as error:
            return Response(
                {'route': [str(error)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = str(request.data.get('name', '')).strip()
        if not 2 <= len(name) <= 80:
            return Response(
                {'name': ['코스 이름은 2~80자로 입력해 주세요.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        visibility = request.data.get(
            'visibility',
            CustomCourse.Visibility.PRIVATE,
        )
        if visibility not in CustomCourse.Visibility.values:
            visibility = CustomCourse.Visibility.PRIVATE

        course = CustomCourse.objects.create(
            owner=request.user,
            name=name,
            description=str(request.data.get('description', '')).strip()[:300],
            visibility=visibility,
            source=source,
            **parsed,
        )
        return Response(
            CustomCourseSerializer(course).data,
            status=status.HTTP_201_CREATED,
        )


class CustomCourseDetailView(RunQuestAPIView):
    def get_object(self, request, course_id):
        try:
            return CustomCourse.objects.select_related(
                'owner__profile'
            ).get(id=course_id, owner=request.user)
        except CustomCourse.DoesNotExist:
            return None

    def get(self, request, course_id):
        course = self.get_object(request, course_id)
        if not course:
            return Response(
                {'detail': '나의 코스를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CustomCourseSerializer(course).data)

    def patch(self, request, course_id):
        course = self.get_object(request, course_id)
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CustomCourseSerializer(
            course,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, course_id):
        course = self.get_object(request, course_id)
        if not course:
            return Response(status=status.HTTP_404_NOT_FOUND)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteCourseListView(RunQuestAPIView):
    def get(self, request):
        courses = Course.objects.filter(
            favorited_by__user=request.user,
            is_active=True,
        ).distinct()
        return Response(
            CourseSerializer(
                courses,
                many=True,
                context={'request': request},
            ).data
        )


def recommendation_response(session, item, request):
    return {
        'session': RecommendationSessionSerializer(session).data,
        'recommendation': RecommendationItemSerializer(
            item,
            context={'request': request},
        ).data,
    }


class RecommendationGenerateView(RunQuestAPIView):
    def post(self, request):
        if not hasattr(request.user, 'survey_response'):
            return Response(
                {'detail': '추천을 받으려면 먼저 맞춤 설문을 완료해 주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if latitude is not None or longitude is not None:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                return Response(
                    {'detail': '현재 위치 좌표 형식이 올바르지 않습니다.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                return Response(
                    {'detail': '현재 위치 좌표 범위를 확인해 주세요.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        session = generate_recommendation_session(
            request.user,
            latitude=latitude,
            longitude=longitude,
        )
        request.user.profile.user_type = session.user_state
        request.user.profile.save(update_fields=['user_type', 'updated_at'])
        item = current_item(session)
        return Response(
            recommendation_response(session, item, request),
            status=status.HTTP_201_CREATED,
        )


class RecommendationCurrentView(RunQuestAPIView):
    def get(self, request):
        session = get_active_session(request.user)
        if not session:
            return Response(
                {'detail': '활성 추천이 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            recommendation_response(
                session,
                current_item(session),
                request,
            )
        )


class RecommendationNextView(RunQuestAPIView):
    def post(self, request):
        session = get_active_session(request.user)
        if not session:
            return Response(
                {'detail': '활성 추천이 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if latitude is not None and longitude is not None:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                latitude = None
                longitude = None
            if (
                latitude is not None
                and longitude is not None
                and -90 <= latitude <= 90
                and -180 <= longitude <= 180
                and (
                    session.current_latitude is None
                    or session.current_longitude is None
                )
            ):
                session = generate_recommendation_session(
                    request.user,
                    latitude=latitude,
                    longitude=longitude,
                )
        item = advance_item(session)
        return Response(recommendation_response(session, item, request))


class RunningStartView(RunQuestAPIView):
    def post(self, request):
        existing = RunningRecord.objects.filter(
            user=request.user,
            status__in=[
                RunningRecord.Status.ACTIVE,
                RunningRecord.Status.PAUSED,
            ],
        ).select_related('course').first()
        if existing:
            return Response(
                RunningRecordSerializer(
                    existing,
                    context={'request': request},
                ).data,
                status=status.HTTP_200_OK,
            )

        serializer = RunningRecordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        running_record = serializer.save(
            user=request.user,
            status=RunningRecord.Status.ACTIVE,
        )
        return Response(
            RunningRecordSerializer(
                running_record,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ActiveRunningView(RunQuestAPIView):
    def get(self, request):
        running_record = RunningRecord.objects.filter(
            user=request.user,
            status__in=[
                RunningRecord.Status.ACTIVE,
                RunningRecord.Status.PAUSED,
            ],
        ).select_related('course', 'custom_course').first()
        if not running_record:
            return Response(
                {'detail': '진행 중인 러닝이 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            RunningRecordSerializer(
                running_record,
                context={'request': request},
            ).data
        )


class RunningProgressView(RunQuestAPIView):
    def patch(self, request, record_id):
        try:
            running_record = RunningRecord.objects.get(
                id=record_id,
                user=request.user,
                status__in=[
                    RunningRecord.Status.ACTIVE,
                    RunningRecord.Status.PAUSED,
                ],
            )
        except RunningRecord.DoesNotExist:
            return Response(
                {'detail': '진행 중인 러닝을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        incoming_points = normalize_track_points(
            request.data.get('track_points', [])
        )
        if incoming_points:
            combined = running_record.track_points + incoming_points
            running_record.track_points = normalize_track_points(combined)

        next_status = request.data.get('status')
        if next_status in {
            RunningRecord.Status.ACTIVE,
            RunningRecord.Status.PAUSED,
        }:
            running_record.status = next_status
        running_record.duration_seconds = max(
            running_record.duration_seconds,
            int(request.data.get('duration_seconds', 0)),
        )
        running_record.paused_seconds = max(
            running_record.paused_seconds,
            int(request.data.get('paused_seconds', 0)),
        )
        running_record.save(
            update_fields=[
                'track_points',
                'status',
                'duration_seconds',
                'paused_seconds',
            ]
        )
        return Response(
            RunningRecordSerializer(
                running_record,
                context={'request': request},
            ).data
        )


class RunningFinishView(RunQuestAPIView):
    def post(self, request, record_id):
        try:
            running_record = RunningRecord.objects.get(
                id=record_id,
                user=request.user,
                status__in=[
                    RunningRecord.Status.ACTIVE,
                    RunningRecord.Status.PAUSED,
                ],
            )
        except RunningRecord.DoesNotExist:
            return Response(
                {'detail': '완료할 러닝을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        all_points = running_record.track_points + request.data.get(
            'track_points',
            [],
        )
        duration_seconds = max(
            running_record.duration_seconds,
            int(request.data.get('duration_seconds', 0)),
        )
        paused_seconds = max(
            running_record.paused_seconds,
            int(request.data.get('paused_seconds', 0)),
        )
        stats = calculate_run_stats(all_points, duration_seconds)

        if stats['distance_km'] < MIN_COMPLETED_RUN_DISTANCE_KM:
            running_record.delete()
            return Response({
                'cancelled': True,
                'detail': '100m 이상 이동한 러닝만 기록으로 저장됩니다.',
                'distance_km': stats['distance_km'],
                'min_distance_km': MIN_COMPLETED_RUN_DISTANCE_KM,
            })

        running_record.status = RunningRecord.Status.COMPLETED
        running_record.duration_seconds = duration_seconds
        running_record.paused_seconds = paused_seconds
        running_record.track_points = stats['track_points']
        running_record.distance_km = stats['distance_km']
        running_record.average_pace_seconds = stats['average_pace_seconds']
        running_record.calories = stats['calories']
        running_record.completed_at = timezone.now()
        running_record.save()
        running_record.ai_feedback = generate_run_feedback(running_record)
        running_record.save(update_fields=['ai_feedback'])

        attendance, _ = Attendance.objects.update_or_create(
            user=request.user,
            date=timezone.localdate(running_record.completed_at),
            defaults={'running_record': running_record},
        )
        new_badges = award_eligible_badges(request.user)
        for user_badge in new_badges:
            create_notification(
                request.user,
                Notification.Type.BADGE,
                '새 배지를 획득했어요',
                f'{user_badge.badge.name} 배지가 컬렉션에 추가됐습니다.',
                f'/my/badges/{user_badge.badge.code}',
                {'badge_code': user_badge.badge.code},
            )
        return Response(
            {
                'record': RunningRecordSerializer(
                    running_record,
                    context={'request': request},
                ).data,
                'attendance': AttendanceSerializer(attendance).data,
                'new_badges': BadgeSerializer(
                    [item.badge for item in new_badges],
                    many=True,
                    context={
                        'earned_map': {
                            item.badge_id: item for item in new_badges
                        },
                    },
                ).data,
            }
        )


class RunningRecordDetailView(RunQuestAPIView):
    def get(self, request, record_id):
        try:
            running_record = RunningRecord.objects.select_related(
                'course',
                'custom_course',
            ).get(id=record_id, user=request.user)
        except RunningRecord.DoesNotExist:
            return Response(
                {'detail': '러닝 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            RunningRecordSerializer(
                running_record,
                context={'request': request},
            ).data
        )

    def delete(self, request, record_id):
        try:
            running_record = RunningRecord.objects.get(
                id=record_id,
                user=request.user,
                status__in=[
                    RunningRecord.Status.ACTIVE,
                    RunningRecord.Status.PAUSED,
                    RunningRecord.Status.COMPLETED,
                ],
            )
        except RunningRecord.DoesNotExist:
            return Response(
                {'detail': '삭제할 러닝 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        running_record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RunningSaveCourseView(RunQuestAPIView):
    def post(self, request, record_id):
        try:
            running_record = RunningRecord.objects.get(
                id=record_id,
                user=request.user,
                status=RunningRecord.Status.COMPLETED,
            )
        except RunningRecord.DoesNotExist:
            return Response(
                {'detail': '코스로 저장할 러닝 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if running_record.custom_course_id:
            return Response(
                {
                    'course': CustomCourseSerializer(running_record.custom_course).data,
                    'record': RunningRecordSerializer(
                        running_record,
                        context={'request': request},
                    ).data,
                }
            )

        if running_record.course_id:
            return Response(
                {'detail': '기본 코스로 완료한 기록은 이미 연결된 코스가 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed = validate_route_points(running_record.track_points)
        except GpxValidationError as error:
            return Response(
                {'route': [str(error)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = str(request.data.get('name', '')).strip()
        if not 2 <= len(name) <= 80:
            return Response(
                {'name': ['코스 이름은 2~80자로 입력해 주세요.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        visibility = request.data.get(
            'visibility',
            CustomCourse.Visibility.PRIVATE,
        )
        if visibility not in CustomCourse.Visibility.values:
            visibility = CustomCourse.Visibility.PRIVATE

        custom_course = CustomCourse.objects.create(
            owner=request.user,
            name=name,
            description=str(request.data.get('description', '')).strip()[:300],
            visibility=visibility,
            source='recorded',
            **parsed,
        )
        running_record.custom_course = custom_course
        running_record.save(update_fields=['custom_course'])

        return Response(
            {
                'course': CustomCourseSerializer(custom_course).data,
                'record': RunningRecordSerializer(
                    running_record,
                    context={'request': request},
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileSummaryView(RunQuestAPIView):
    def get(self, request):
        award_eligible_badges(request.user)
        records = RunningRecord.objects.filter(
            user=request.user,
            status=RunningRecord.Status.COMPLETED,
        )
        aggregate = records.aggregate(
            total_distance=Sum('distance_km'),
            total_duration=Sum('duration_seconds'),
            total_calories=Sum('calories'),
            run_count=Count('id'),
        )
        today = timezone.localdate()
        month_start = today.replace(day=1)
        monthly_distance = records.filter(
            completed_at__date__gte=month_start,
        ).aggregate(total=Sum('distance_km'))['total'] or 0
        return Response({
            'user': UserSerializer(request.user).data,
            'stats': {
                'total_distance': round(float(aggregate['total_distance'] or 0), 2),
                'total_duration': aggregate['total_duration'] or 0,
                'total_calories': aggregate['total_calories'] or 0,
                'run_count': aggregate['run_count'] or 0,
                'streak_days': current_attendance_streak(request.user),
            },
            'monthly_goal': {
                'target_km': 30,
                'current_km': round(float(monthly_distance), 2),
                'progress': min(100, round(float(monthly_distance) / 30 * 100)),
            },
            'running_profile': build_running_profile(request.user),
            'profile_style': build_profile_style(request.user),
            'earned_badge_count': UserBadge.objects.filter(
                user=request.user,
            ).count(),
        })


class NotificationListView(RunQuestAPIView):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)[:50]
        return Response({
            'unread_count': Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count(),
            'notifications': NotificationSerializer(
                notifications,
                many=True,
            ).data,
        })


class NotificationReadView(RunQuestAPIView):
    def post(self, request, notification_id=None):
        notifications = Notification.objects.filter(user=request.user)
        if notification_id is not None:
            notifications = notifications.filter(id=notification_id)
            if not notifications.exists():
                return Response(status=status.HTTP_404_NOT_FOUND)
        notifications.update(is_read=True)
        return Response({'unread_count': 0 if notification_id is None else (
            Notification.objects.filter(user=request.user, is_read=False).count()
        )})


class ProfileRunningRecordsView(RunQuestAPIView):
    def get(self, request):
        records = RunningRecord.objects.filter(
            user=request.user,
            status=RunningRecord.Status.COMPLETED,
        ).select_related('course')
        return Response(
            RunningRecordSerializer(
                records,
                many=True,
                context={'request': request},
            ).data
        )


class ProfileAttendanceView(RunQuestAPIView):
    def get(self, request):
        today = timezone.localdate()
        try:
            year = int(request.query_params.get('year', today.year))
            month = int(request.query_params.get('month', today.month))
            start = date(year, month, 1)
        except (TypeError, ValueError):
            return Response(
                {'detail': '연도와 월을 확인해 주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        end = date(year, month, monthrange(year, month)[1])
        attendances = Attendance.objects.filter(
            user=request.user,
            date__range=(start, end),
        ).select_related('running_record')
        records = RunningRecord.objects.filter(
            user=request.user,
            status=RunningRecord.Status.COMPLETED,
            completed_at__date__range=(start, end),
        ).select_related('course', 'custom_course').order_by('-completed_at')
        records_by_date = {}
        for record in records:
            if not record.completed_at:
                continue
            key = timezone.localtime(record.completed_at).date().isoformat()
            records_by_date.setdefault(key, []).append(
                RunningRecordSerializer(
                    record,
                    context={'request': request},
                ).data
            )
        return Response({
            'year': year,
            'month': month,
            'count': attendances.count(),
            'streak_days': current_attendance_streak(request.user),
            'attendances': AttendanceSerializer(attendances, many=True).data,
            'records_by_date': records_by_date,
        })


class ProfileBadgesView(RunQuestAPIView):
    def get(self, request):
        award_eligible_badges(request.user)
        badges = Badge.objects.all()
        earned_map = {
            item.badge_id: item
            for item in UserBadge.objects.filter(
                user=request.user,
            ).select_related('badge')
        }
        progress_map = {
            badge.id: badge_progress(request.user, badge)
            for badge in badges
        }
        return Response(
            BadgeSerializer(
                badges,
                many=True,
                context={
                    'earned_map': earned_map,
                    'progress_map': progress_map,
                },
            ).data
        )


class ProfileBadgeDetailView(RunQuestAPIView):
    def get(self, request, code):
        award_eligible_badges(request.user)
        try:
            badge = Badge.objects.get(code=code)
        except Badge.DoesNotExist:
            return Response(
                {'detail': '배지를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        earned = UserBadge.objects.filter(
            user=request.user,
            badge=badge,
        ).first()
        return Response(
            BadgeSerializer(
                badge,
                context={
                    'earned_map': {badge.id: earned} if earned else {},
                    'progress_map': {
                        badge.id: badge_progress(request.user, badge),
                    },
                },
            ).data
        )


def community_post_queryset(include_details=True):
    related_fields = [
        'author__profile',
        'author__settings',
    ]
    if include_details:
        related_fields.extend([
            'related_course',
            'running_record__course',
            'running_record__custom_course',
        ])
    return CommunityPost.objects.select_related(*related_fields)


class CommunityPostListCreateView(RunQuestAPIView):
    def get(self, request):
        posts = community_post_queryset(include_details=False).defer('images')
        category = request.query_params.get('category')
        search = request.query_params.get('search', '').strip()
        ordering = request.query_params.get('ordering', 'latest')
        period = request.query_params.get('period')
        region = request.query_params.get('region')
        if category:
            posts = posts.filter(category=category)
        if search:
            posts = posts.filter(
                Q(title__icontains=search)
                | Q(content__icontains=search)
                | Q(author__profile__nickname__icontains=search)
            )
        if period:
            today = timezone.localdate()
            if period == 'today':
                posts = posts.filter(created_at__date=today)
            elif period == 'week':
                posts = posts.filter(created_at__date__gte=today - timedelta(days=7))
            elif period == 'month':
                posts = posts.filter(created_at__date__gte=today - timedelta(days=30))
        if region and region != 'all':
            posts = posts.filter(
                Q(related_course__district__icontains=region)
                | Q(running_record__course__district__icontains=region)
            )
        if request.query_params.get('saved') == 'true':
            posts = posts.filter(saves__user=request.user)
        posts = posts.annotate(
            like_count_value=Count('likes', distinct=True),
            comment_count_value=Count('comments', distinct=True),
            is_liked_value=Exists(
                CommunityPostLike.objects.filter(
                    user=request.user,
                    post=OuterRef('pk'),
                ),
            ),
            is_saved_value=Exists(
                SavedCommunityPost.objects.filter(
                    user=request.user,
                    post=OuterRef('pk'),
                ),
            ),
        )
        if ordering == 'popular':
            posts = posts.annotate(
                popularity=(
                    Count('likes', distinct=True)
                    + Count('comments', distinct=True)
                ),
            ).order_by('-popularity', '-created_at')
        else:
            posts = posts.order_by('-created_at')
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset', 0)
        if limit:
            try:
                limit_value = min(max(int(limit), 1), 30)
                offset_value = max(int(offset), 0)
            except (TypeError, ValueError):
                limit_value = 12
                offset_value = 0

            page_posts = list(posts.distinct()[offset_value:offset_value + limit_value + 1])
            has_more = len(page_posts) > limit_value
            page_posts = page_posts[:limit_value]
            return Response({
                'results': CommunityPostSerializer(
                    page_posts,
                    many=True,
                    context={'request': request, 'list': True},
                ).data,
                'next_offset': offset_value + len(page_posts),
                'has_more': has_more,
            })

        return Response(
            CommunityPostSerializer(
                posts.distinct(),
                many=True,
                context={'request': request, 'list': True},
            ).data
        )

    def post(self, request):
        serializer = CommunityPostSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        return Response(
            CommunityPostSerializer(
                post,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class CommunityPostDetailView(RunQuestAPIView):
    def get_post(self, request, post_id):
        try:
            return community_post_queryset(include_details=True).prefetch_related(
                Prefetch(
                    'comments',
                    queryset=CommunityComment.objects.select_related(
                        'author__profile',
                        'author__settings',
                        'post__author',
                    ).annotate(
                        like_count_value=Count('likes', distinct=True),
                        is_liked_value=Exists(
                            CommunityCommentLike.objects.filter(
                                user=request.user,
                                comment=OuterRef('pk'),
                            ),
                        ),
                    ),
                ),
            ).annotate(
                like_count_value=Count('likes', distinct=True),
                comment_count_value=Count('comments', distinct=True),
                is_liked_value=Exists(
                    CommunityPostLike.objects.filter(
                        user=request.user,
                        post=OuterRef('pk'),
                    ),
                ),
                is_saved_value=Exists(
                    SavedCommunityPost.objects.filter(
                        user=request.user,
                        post=OuterRef('pk'),
                    ),
                ),
            ).get(id=post_id)
        except CommunityPost.DoesNotExist:
            return None

    def get(self, request, post_id):
        post = self.get_post(request, post_id)
        if not post:
            return Response(
                {'detail': '게시글을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            CommunityPostSerializer(
                post,
                context={'request': request},
            ).data
        )

    def patch(self, request, post_id):
        post = self.get_post(request, post_id)
        if not post:
            return Response(
                {'detail': '게시글을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.author != request.user:
            return Response(
                {'detail': '작성자만 수정할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CommunityPostSerializer(
            post,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, post_id):
        post = self.get_post(request, post_id)
        if not post:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if post.author != request.user:
            return Response(
                {'detail': '작성자만 삭제할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityPostLikeView(RunQuestAPIView):
    def post(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        like, created = CommunityPostLike.objects.get_or_create(
            user=request.user,
            post=post,
        )
        if not created:
            like.delete()
        elif post.author_id != request.user.id:
            create_notification(
                post.author,
                Notification.Type.LIKE,
                '게시글에 좋아요가 추가됐어요',
                f'{request.user.profile.nickname}님이 게시글을 좋아합니다.',
                f'/community/{post.id}',
                {'post_id': post.id},
            )
        return Response({
            'is_liked': created,
            'like_count': post.likes.count(),
        })


class CommunityPostSaveView(RunQuestAPIView):
    def post(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        saved, created = SavedCommunityPost.objects.get_or_create(
            user=request.user,
            post=post,
        )
        if not created:
            saved.delete()
        return Response({'is_saved': created})


class CommunityCommentCreateView(RunQuestAPIView):
    def post(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CommunityCommentSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(author=request.user, post=post)
        if post.author_id != request.user.id:
            create_notification(
                post.author,
                Notification.Type.COMMENT,
                '새 댓글이 도착했어요',
                f'{request.user.profile.nickname}님이 댓글을 남겼습니다.',
                f'/community/{post.id}',
                {'post_id': post.id, 'comment_id': comment.id},
            )
        return Response(
            CommunityCommentSerializer(
                comment,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class CommunityCommentDetailView(RunQuestAPIView):
    def get_comment(self, comment_id):
        try:
            return CommunityComment.objects.select_related(
                'author__profile',
                'post__author__profile',
            ).get(id=comment_id)
        except CommunityComment.DoesNotExist:
            return None

    def patch(self, request, comment_id):
        comment = self.get_comment(comment_id)
        if not comment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if comment.author != request.user:
            return Response(
                {'detail': '댓글 작성자만 수정할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CommunityCommentSerializer(
            comment,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, comment_id):
        comment = self.get_comment(comment_id)
        if not comment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if comment.author != request.user and comment.post.author != request.user:
            return Response(
                {'detail': '댓글 작성자 또는 게시글 작성자만 삭제할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityCommentLikeView(RunQuestAPIView):
    def post(self, request, comment_id):
        try:
            comment = CommunityComment.objects.select_related('post').get(
                id=comment_id,
            )
        except CommunityComment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        like, created = CommunityCommentLike.objects.get_or_create(
            user=request.user,
            comment=comment,
        )
        if not created:
            like.delete()
        return Response({
            'is_liked': created,
            'like_count': comment.likes.count(),
        })


class ChatConversationView(RunQuestAPIView):
    def get_session(self, user, prefetch_messages=False):
        sessions = ChatSession.objects.filter(
            user=user,
            is_active=True,
        )
        if prefetch_messages:
            sessions = ChatSession.objects.filter(
                user=user,
                is_active=True,
            ).prefetch_related('messages__recommended_course')
        session = sessions.first()
        if session:
            return session
        return ChatSession.objects.create(user=user)

    def get(self, request):
        session = self.get_session(request.user, prefetch_messages=True)
        return Response(
            ChatSessionSerializer(
                session,
                context={'request': request},
            ).data
        )

    def post(self, request):
        with time_block('chat.post.total', user_id=request.user.id):
            content = str(request.data.get('content', '')).strip()
            if not content:
                return Response(
                    {'content': ['메시지를 입력해 주세요.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(content) > 500:
                return Response(
                    {'content': ['메시지는 500자 이하로 입력해 주세요.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with time_block('chat.session.get', user_id=request.user.id):
                session = self.get_session(request.user)
            request_context = dict(session.context)
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            if latitude is not None and longitude is not None:
                try:
                    latitude = float(latitude)
                    longitude = float(longitude)
                except (TypeError, ValueError):
                    latitude = None
                    longitude = None
                if (
                    latitude is not None
                    and longitude is not None
                    and -90 <= latitude <= 90
                    and -180 <= longitude <= 180
                ):
                    request_context['latitude'] = latitude
                    request_context['longitude'] = longitude
            with time_block('chat.message.create_user', session_id=session.id):
                user_message = ChatMessage.objects.create(
                    session=session,
                    role=ChatMessage.Role.USER,
                    content=content,
                )
            with time_block('chat.messages.recent', session_id=session.id):
                recent_messages = [
                    {
                        'role': message.role,
                        'content': message.content[:500],
                        'intent': message.intent,
                        'recommended_course_id': message.recommended_course_id,
                    }
                    for message in reversed(
                        list(
                            session.messages.exclude(id=user_message.id)
                            .only('id', 'role', 'content', 'intent', 'recommended_course_id', 'created_at')
                            .order_by('-created_at')[:6]
                        )
                    )
                ]
            with time_block('chat.assistant.build', session_id=session.id):
                result = build_assistant_reply(
                    request.user,
                    content,
                    request_context,
                    recent_messages=recent_messages,
                )
            with time_block('chat.message.create_assistant', session_id=session.id):
                session.context = result['context']
                session.save(update_fields=['context', 'updated_at'])
                assistant_message = ChatMessage.objects.create(
                    session=session,
                    role=ChatMessage.Role.ASSISTANT,
                    content=result['content'],
                    intent=result['intent'],
                    recommended_course=result.get('course'),
                    metadata={
                        'score': result.get('score'),
                        'reasons': result.get('reasons', []),
                        'context': result['context'],
                        'provider': result.get('provider', 'local'),
                        'guardrail': result.get('guardrail', {}),
                        'llm_requests': result.get('llm_requests', {}),
                        'location': result.get('location', {}),
                    },
                )
            return Response(
                {
                    'user_message': ChatMessageSerializer(
                        user_message,
                        context={'request': request},
                    ).data,
                    'assistant_message': ChatMessageSerializer(
                        assistant_message,
                        context={'request': request},
                    ).data,
                    'context': session.context,
                },
                status=status.HTTP_201_CREATED,
            )

    def delete(self, request):
        ChatSession.objects.filter(
            user=request.user,
            is_active=True,
        ).update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

