from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.test import APIClient

from core.models import Course, RecommendationSession, RunningRecord


KEEP_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 33, 34]

if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

actual_ids = list(Course.objects.order_by('id').values_list('id', flat=True))
assert actual_ids == KEEP_IDS, actual_ids
assert Course.objects.filter(is_active=True).count() == 22
RecommendationSession.objects.filter(is_active=True).update(is_active=False)
assert not RunningRecord.objects.filter(course_id__isnull=False).exclude(course_id__in=KEEP_IDS).exists()

for course in Course.objects.order_by('id'):
    assert len(course.route_points) >= 2, (course.id, course.name)
    assert float(course.distance_km) >= 0.1, (course.id, course.name)
    assert abs(float(course.start_latitude) - float(course.route_points[0][0])) < 0.000001, (course.id, course.name)
    assert abs(float(course.start_longitude) - float(course.route_points[0][1])) < 0.000001, (course.id, course.name)

user = (
    User.objects.filter(profile__survey_completed=True).first()
    or User.objects.first()
)
assert user is not None, 'No user available for API smoke test'

client = APIClient()
client.force_authenticate(user=user)

course_list = client.get('/api/courses/')
assert course_list.status_code == 200, course_list.status_code
course_payload = course_list.json()['courses']
assert len(course_payload) == 22, len(course_payload)
assert all(len(item['route_points']) >= 2 for item in course_payload)

first_slug = course_payload[0]['slug']
detail = client.get(f'/api/courses/{first_slug}/')
assert detail.status_code == 200, detail.status_code
assert len(detail.json()['route_points']) >= 2

home = client.get('/api/home/')
assert home.status_code == 200, home.status_code
assert 'recommendations' in home.json()

recommendation = client.post(
    '/api/recommendations/generate/',
    {'latitude': 36.35, 'longitude': 127.38},
    format='json',
)
assert recommendation.status_code == 201, recommendation.status_code
recommendation_payload = recommendation.json()
recommended_course = recommendation_payload['recommendation']['course']
assert recommended_course['id'] in KEEP_IDS
assert len(recommended_course['route_points']) >= 2

print('SMOKE_OK')
print('COURSE_COUNT', len(course_payload))
print('FIRST_DETAIL_SLUG', first_slug)
print('RECOMMENDED_COURSE_ID', recommended_course['id'])
print('DEACTIVATED_AFTER_SMOKE', RecommendationSession.objects.filter(is_active=True).update(is_active=False))
