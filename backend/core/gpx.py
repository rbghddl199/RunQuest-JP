from math import asin, cos, radians, sin, sqrt
from xml.etree import ElementTree


DAEJEON_BOUNDS = {
    'min_latitude': 36.10,
    'max_latitude': 36.55,
    'min_longitude': 127.20,
    'max_longitude': 127.60,
}
MAX_GPX_SIZE = 2 * 1024 * 1024
MAX_TRACK_POINTS = 5000


class GpxValidationError(ValueError):
    pass


def haversine_km(first, second):
    lat1, lon1 = map(radians, first)
    lat2, lon2 = map(radians, second)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return 6371.0 * 2 * asin(sqrt(value))


def is_in_daejeon(latitude, longitude):
    return (
        DAEJEON_BOUNDS['min_latitude']
        <= latitude
        <= DAEJEON_BOUNDS['max_latitude']
        and DAEJEON_BOUNDS['min_longitude']
        <= longitude
        <= DAEJEON_BOUNDS['max_longitude']
    )


def parse_gpx(upload):
    if upload.size > MAX_GPX_SIZE:
        raise GpxValidationError('GPX 파일은 2MB 이하만 업로드할 수 있습니다.')
    if not upload.name.lower().endswith('.gpx'):
        raise GpxValidationError('GPX 확장자 파일을 선택해 주세요.')

    try:
        root = ElementTree.fromstring(upload.read())
    except ElementTree.ParseError as error:
        raise GpxValidationError('올바른 GPX XML 파일이 아닙니다.') from error

    points = []
    elevations = []
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] != 'trkpt':
            continue
        try:
            latitude = float(element.attrib['lat'])
            longitude = float(element.attrib['lon'])
        except (KeyError, TypeError, ValueError) as error:
            raise GpxValidationError('GPX 좌표 형식을 확인해 주세요.') from error
        if not is_in_daejeon(latitude, longitude):
            raise GpxValidationError('대전 지역 안의 코스만 저장할 수 있습니다.')
        points.append([round(latitude, 6), round(longitude, 6)])
        for child in element:
            if child.tag.rsplit('}', 1)[-1] == 'ele' and child.text:
                try:
                    elevations.append(float(child.text))
                except ValueError:
                    elevations.append(None)
                break
        else:
            elevations.append(None)
        if len(points) > MAX_TRACK_POINTS:
            raise GpxValidationError('트랙 포인트는 5,000개 이하만 지원합니다.')

    if len(points) < 2:
        raise GpxValidationError('GPX 파일에 최소 2개의 트랙 포인트가 필요합니다.')

    distance = sum(
        haversine_km(first, second)
        for first, second in zip(points, points[1:])
    )
    if distance < 0.1:
        raise GpxValidationError('코스 거리는 100m 이상이어야 합니다.')

    elevation_gain = 0
    for first, second in zip(elevations, elevations[1:]):
        if first is not None and second is not None and second > first:
            elevation_gain += second - first

    return {
        'route_points': points,
        'distance_km': round(distance, 2),
        'elevation_gain_m': round(elevation_gain),
        'start_latitude': points[0][0],
        'start_longitude': points[0][1],
    }


def validate_route_points(raw_points):
    if not isinstance(raw_points, list) or not 2 <= len(raw_points) <= MAX_TRACK_POINTS:
        raise GpxValidationError('경로는 2~5,000개의 지점으로 구성해 주세요.')

    points = []
    for raw in raw_points:
        try:
            if isinstance(raw, dict):
                latitude = float(raw['latitude'])
                longitude = float(raw['longitude'])
            else:
                latitude = float(raw[0])
                longitude = float(raw[1])
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise GpxValidationError('경로 좌표 형식을 확인해 주세요.') from error
        if not is_in_daejeon(latitude, longitude):
            raise GpxValidationError('대전 지역 안의 경로만 저장할 수 있습니다.')
        points.append([round(latitude, 6), round(longitude, 6)])

    distance = sum(
        haversine_km(first, second)
        for first, second in zip(points, points[1:])
    )
    if distance < 0.1:
        raise GpxValidationError('코스 거리는 100m 이상이어야 합니다.')
    return {
        'route_points': points,
        'distance_km': round(distance, 2),
        'elevation_gain_m': 0,
        'start_latitude': points[0][0],
        'start_longitude': points[0][1],
    }
