from django.db import transaction

from core.models import Course, RecommendationSession


def expected_difficulty(distance_km, elevation_gain_m):
    if elevation_gain_m >= 120 or distance_km >= 8:
        return Course.Difficulty.HARD
    if elevation_gain_m >= 40 or distance_km >= 4:
        return Course.Difficulty.NORMAL
    return Course.Difficulty.EASY


updated = []
with transaction.atomic():
    for course in Course.objects.select_for_update().order_by('id'):
        distance = float(course.distance_km)
        elevation = int(course.elevation_gain_m or 0)
        expected_minutes = max(1, round(distance * 7))
        expected_level = expected_difficulty(distance, elevation)

        changed_fields = []
        if course.estimated_minutes != expected_minutes:
            course.estimated_minutes = expected_minutes
            changed_fields.append('estimated_minutes')
        if course.difficulty != expected_level:
            course.difficulty = expected_level
            changed_fields.append('difficulty')

        if changed_fields:
            course.save(update_fields=[*changed_fields, 'updated_at'])
            updated.append(
                {
                    'id': course.id,
                    'name': course.name,
                    'fields': changed_fields,
                    'difficulty': course.difficulty,
                    'estimated_minutes': course.estimated_minutes,
                }
            )

    deactivated_sessions = RecommendationSession.objects.filter(is_active=True).update(is_active=False)

print('UPDATED', updated)
print('DEACTIVATED_RECOMMENDATION_SESSIONS', deactivated_sessions)
