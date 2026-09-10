from core.gpx import haversine_km
from core.models import Course


def route_distance(points):
    return sum(haversine_km(first, second) for first, second in zip(points, points[1:]))


def expected_difficulty(distance_km, elevation_gain_m):
    if elevation_gain_m >= 120 or distance_km >= 8:
        return 'hard'
    if elevation_gain_m >= 40 or distance_km >= 4:
        return 'normal'
    return 'easy'


print('id | name | points | db_km | calc_km | diff | elev | difficulty -> expected | minutes -> expected | issues')
for course in Course.objects.order_by('id'):
    points = course.route_points
    calculated = route_distance(points)
    db_distance = float(course.distance_km)
    expected_minutes = max(1, round(db_distance * 7))
    expected = expected_difficulty(db_distance, int(course.elevation_gain_m or 0))
    issues = []

    if len(points) < 2:
        issues.append('route_points<2')
    if abs(calculated - db_distance) > 0.15:
        issues.append('distance_mismatch')
    if int(course.estimated_minutes) != expected_minutes:
        issues.append('minutes_mismatch')
    if course.difficulty != expected:
        issues.append('difficulty_mismatch')
    if not (36.10 <= float(course.start_latitude) <= 36.55):
        issues.append('start_lat_outside')
    if not (127.20 <= float(course.start_longitude) <= 127.60):
        issues.append('start_lng_outside')
    if points and (
        abs(float(course.start_latitude) - float(points[0][0])) > 0.000001
        or abs(float(course.start_longitude) - float(points[0][1])) > 0.000001
    ):
        issues.append('start_not_first_point')

    print(
        f'{course.id:>2} | {course.name} | {len(points):>3} | '
        f'{db_distance:>4.1f} | {calculated:>5.2f} | '
        f'{calculated - db_distance:+.2f} | {int(course.elevation_gain_m):>3} | '
        f'{course.difficulty} -> {expected} | '
        f'{course.estimated_minutes} -> {expected_minutes} | '
        f'{", ".join(issues) if issues else "OK"}'
    )
