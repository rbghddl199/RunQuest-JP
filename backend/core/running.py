from math import asin, cos, radians, sin, sqrt


def haversine_meters(point_a, point_b):
    latitude_a, longitude_a = point_a['latitude'], point_a['longitude']
    latitude_b, longitude_b = point_b['latitude'], point_b['longitude']
    earth_radius = 6_371_000

    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    value = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude_a))
        * cos(radians(latitude_b))
        * sin(longitude_delta / 2) ** 2
    )
    return 2 * earth_radius * asin(sqrt(value))


def normalize_track_points(points):
    accepted = []
    for point in points:
        try:
            normalized = {
                'latitude': float(point['latitude']),
                'longitude': float(point['longitude']),
                'accuracy': float(point.get('accuracy', 0)),
                'timestamp': int(point.get('timestamp', 0)),
            }
        except (KeyError, TypeError, ValueError):
            continue

        if normalized['accuracy'] > 50:
            continue
        if accepted:
            distance = haversine_meters(accepted[-1], normalized)
            time_delta = max(
                1,
                (normalized['timestamp'] - accepted[-1]['timestamp']) / 1000,
            )
            speed_mps = distance / time_delta
            if speed_mps > 12:
                continue
        accepted.append(normalized)
    return accepted


def calculate_distance_km(points):
    if len(points) < 2:
        return 0.0
    meters = sum(
        haversine_meters(points[index - 1], points[index])
        for index in range(1, len(points))
    )
    return round(meters / 1000, 2)


def calculate_run_stats(points, duration_seconds):
    normalized = normalize_track_points(points)
    distance_km = calculate_distance_km(normalized)
    pace_seconds = (
        round(duration_seconds / distance_km)
        if distance_km > 0 and duration_seconds > 0
        else 0
    )
    calories = round(distance_km * 65)
    return {
        'track_points': normalized,
        'distance_km': distance_km,
        'average_pace_seconds': pace_seconds,
        'calories': calories,
    }
