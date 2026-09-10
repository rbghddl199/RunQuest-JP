from django.contrib import admin

from .models import (
    Course,
    Attendance,
    Badge,
    ChatMessage,
    ChatSession,
    CommunityComment,
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


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__email', 'title', 'message')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'distance_unit',
        'temperature_unit',
        'profile_visibility',
        'updated_at',
    )
    list_filter = (
        'distance_unit',
        'temperature_unit',
        'profile_visibility',
    )
    search_fields = ('user__email', 'user__profile__nickname')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'nickname',
        'email',
        'user_type',
        'survey_completed',
        'created_at',
    )
    list_filter = ('user_type', 'survey_completed')
    search_fields = ('nickname', 'user__email')

    @admin.display(description='이메일')
    def email(self, obj):
        return obj.user.email


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'experience_level',
        'distance_range',
        'course_type',
        'running_goal',
        'completed_at',
    )
    list_filter = (
        'experience_level',
        'course_type',
        'preferred_time',
        'running_goal',
    )
    search_fields = ('user__email', 'user__profile__nickname')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'district',
        'course_type',
        'difficulty',
        'distance_km',
        'is_active',
    )
    list_filter = ('district', 'course_type', 'difficulty', 'is_active')
    search_fields = ('name', 'summary', 'district')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(FavoriteCourse)
class FavoriteCourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at')
    search_fields = ('user__email', 'course__name')


@admin.register(RunningRecord)
class RunningRecordAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'course',
        'distance_km',
        'average_pace_seconds',
        'completed_at',
    )
    search_fields = ('user__email', 'course__name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'running_record', 'created_at')
    search_fields = ('user__email',)
    list_filter = ('date',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'condition_type', 'condition_value')
    ordering = ('sort_order',)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    search_fields = ('user__email', 'badge__name')


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'content', 'author__profile__nickname')


@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    search_fields = ('content', 'author__profile__nickname')


admin.site.register(CommunityPostLike)
admin.site.register(SavedCommunityPost)


@admin.register(CustomCourse)
class CustomCourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'distance_km', 'visibility', 'created_at')
    list_filter = ('visibility', 'source')
    search_fields = ('name', 'owner__email', 'owner__profile__nickname')


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'intent', 'recommended_course', 'created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    inlines = [ChatMessageInline]


class RecommendationItemInline(admin.TabularInline):
    model = RecommendationItem
    extra = 0
    readonly_fields = (
        'rank',
        'course',
        'total_score',
        'survey_score',
        'record_score',
        'safety_score',
    )


@admin.register(RecommendationSession)
class RecommendationSessionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'user_state',
        'record_count',
        'current_index',
        'is_active',
        'created_at',
    )
    list_filter = ('user_state', 'is_active')
    inlines = [RecommendationItemInline]
