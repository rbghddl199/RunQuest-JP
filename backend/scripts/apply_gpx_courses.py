from decimal import Decimal
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from core.gpx import parse_gpx
from core.models import Course, RecommendationSession


GPX_DIR = Path(r'C:\Users\USER\Desktop\GPX')
KEEP_IDS = {
    int(path.stem[2:])
    for path in GPX_DIR.glob('pk*.gpx')
    if path.stem[2:].isdigit()
}


def parsed_gpx(path):
    upload = SimpleUploadedFile(
        path.name,
        path.read_bytes(),
        content_type='application/gpx+xml',
    )
    return parse_gpx(upload)


with transaction.atomic():
    before_ids = set(Course.objects.values_list('id', flat=True))
    matched_ids = sorted(before_ids & KEEP_IDS)
    missing_ids = sorted(KEEP_IDS - before_ids)
    delete_ids = sorted(before_ids - KEEP_IDS)

    updated = []
    for course_id in matched_ids:
        path = GPX_DIR / f'pk{course_id}.gpx'
        parsed = parsed_gpx(path)
        course = Course.objects.select_for_update().get(pk=course_id)
        course.route_points = parsed['route_points']
        course.distance_km = Decimal(str(round(parsed['distance_km'], 1)))
        course.elevation_gain_m = parsed['elevation_gain_m']
        course.start_latitude = Decimal(str(parsed['start_latitude']))
        course.start_longitude = Decimal(str(parsed['start_longitude']))
        course.estimated_minutes = max(1, round(float(parsed['distance_km']) * 7))
        course.is_active = True
        course.save(
            update_fields=[
                'route_points',
                'distance_km',
                'elevation_gain_m',
                'start_latitude',
                'start_longitude',
                'estimated_minutes',
                'is_active',
                'updated_at',
            ]
        )
        updated.append(
            {
                'id': course.id,
                'name': course.name,
                'points': len(parsed['route_points']),
                'distance_km': parsed['distance_km'],
            }
        )

    deleted_names = list(
        Course.objects.filter(id__in=delete_ids)
        .order_by('id')
        .values_list('id', 'name')
    )
    deleted_count = Course.objects.filter(id__in=delete_ids).delete()[0]
    deactivated_sessions = RecommendationSession.objects.filter(
        is_active=True
    ).update(is_active=False)

    after_ids = set(Course.objects.values_list('id', flat=True))

print('UPDATED', updated)
print('DELETED_IDS', deleted_names)
print('DELETED_OBJECT_COUNT', deleted_count)
print('MISSING_GPX_IDS_WITHOUT_DB_COURSE', missing_ids)
print('DEACTIVATED_RECOMMENDATION_SESSIONS', deactivated_sessions)
print('COURSE_IDS_AFTER', sorted(after_ids))
print('COURSE_COUNT_AFTER', Course.objects.count())
