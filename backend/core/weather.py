import os

import requests
from django.core.cache import cache


DAEJEON_COORDINATES = (36.3504, 127.3845)
OPENWEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
KAKAO_COORD_TO_REGION_URL = 'https://dapi.kakao.com/v2/local/geo/coord2regioncode.json'

WEATHER_LABELS = {
    'Thunderstorm': '천둥번개',
    'Drizzle': '이슬비',
    'Rain': '비',
    'Snow': '눈',
    'Mist': '안개',
    'Smoke': '연무',
    'Haze': '실안개',
    'Dust': '먼지',
    'Fog': '안개',
    'Sand': '모래바람',
    'Ash': '화산재',
    'Squall': '돌풍',
    'Tornado': '회오리바람',
    'Clear': '맑음',
    'Clouds': '흐림',
}


def running_condition(temperature, humidity, wind_speed, weather_group):
    if weather_group in {'Thunderstorm', 'Snow', 'Squall', 'Tornado'}:
        return '오늘은 안전을 위해 실내 운동이나 휴식을 추천해요.', 'poor'
    if weather_group in {'Rain', 'Drizzle'}:
        return '노면이 미끄러울 수 있어 짧고 천천히 달려보세요.', 'caution'
    if weather_group in {'Clouds', 'Mist', 'Fog', 'Haze'}:
        return '구름이 많은 날이에요. 시야와 체온을 확인하며 가볍게 달려요.', 'cloudy'
    if wind_speed >= 9 or temperature >= 32 or temperature <= -5:
        return '강도는 낮추고 몸 상태를 자주 확인해 주세요.', 'caution'
    if 8 <= temperature <= 24 and humidity < 75 and wind_speed < 6:
        return '가볍게 페이스를 올리기 좋은 날씨예요.', 'good'
    return '무리하지 말고 편안한 페이스로 몸을 깨워보세요.', 'normal'


def _normalize_coordinates(latitude=None, longitude=None):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return (*DAEJEON_COORDINATES, False)

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return (*DAEJEON_COORDINATES, False)

    return latitude, longitude, True


def _cache_key(latitude, longitude):
    return f'current-weather:{round(latitude, 3)}:{round(longitude, 3)}'


def _location_label(latitude, longitude, default='대전광역시'):
    api_key = os.getenv('KAKAO_REST_API_KEY')
    if not api_key:
        return default

    try:
        response = requests.get(
            KAKAO_COORD_TO_REGION_URL,
            params={'x': longitude, 'y': latitude},
            headers={'Authorization': f'KakaoAK {api_key}'},
            timeout=4,
        )
        response.raise_for_status()
        documents = response.json().get('documents', [])
    except (requests.RequestException, ValueError, TypeError):
        return default

    region = next(
        (document for document in documents if document.get('region_type') == 'H'),
        documents[0] if documents else None,
    )
    if not region:
        return default

    depth_1 = region.get('region_1depth_name')
    depth_2 = region.get('region_2depth_name')
    return ' '.join(part for part in [depth_1, depth_2] if part) or default


def fallback_weather(latitude=None, longitude=None, location_label='대전광역시'):
    latitude, longitude, location_applied = _normalize_coordinates(latitude, longitude)
    return {
        'temperature': 22,
        'apparent_temperature': 22,
        'humidity': 55,
        'wind_speed': 2,
        'precipitation_probability': 10,
        'weather_code': 800,
        'main': 'Clouds',
        'label': '흐림',
        'description': '실시간 날씨를 불러오지 못해 기본값을 표시합니다.',
        'running_message': '구름이 많은 날이에요. 시야와 체온을 확인하며 가볍게 달려요.',
        'running_status': 'cloudy',
        'location_label': location_label,
        'latitude': latitude,
        'longitude': longitude,
        'location_applied': location_applied,
        'source': 'fallback',
    }


def fetch_daejeon_weather(latitude=None, longitude=None):
    latitude, longitude, location_applied = _normalize_coordinates(latitude, longitude)
    cached = cache.get(_cache_key(latitude, longitude))
    if cached:
        return cached

    location_label = _location_label(latitude, longitude)
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        weather = fallback_weather(latitude, longitude, location_label)
        cache.set(_cache_key(latitude, longitude), weather, timeout=60 * 5)
        return weather

    try:
        response = requests.get(
            OPENWEATHER_URL,
            params={
                'lat': latitude,
                'lon': longitude,
                'appid': api_key,
                'units': 'metric',
                'lang': 'kr',
            },
            timeout=4,
        )
        response.raise_for_status()
        payload = response.json()

        current = payload['weather'][0]
        main = payload['main']
        wind = payload.get('wind', {})
        weather_group = current.get('main', 'Clear')
        temperature = round(float(main['temp']))
        apparent_temperature = round(float(main.get('feels_like', temperature)))
        humidity = round(float(main.get('humidity', 0)))
        wind_speed = round(float(wind.get('speed', 0)), 1)
        message, condition = running_condition(
            temperature,
            humidity,
            wind_speed,
            weather_group,
        )

        weather = {
            'temperature': temperature,
            'apparent_temperature': apparent_temperature,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'precipitation_probability': 70 if weather_group in {'Rain', 'Drizzle'} else 10,
            'weather_code': current.get('id'),
            'main': weather_group,
            'label': WEATHER_LABELS.get(weather_group, current.get('description', '날씨 확인')),
            'description': current.get('description', ''),
            'running_message': message,
            'running_status': condition,
            'location_label': location_label,
            'latitude': latitude,
            'longitude': longitude,
            'location_applied': location_applied,
            'source': 'openweathermap',
        }
    except (requests.RequestException, KeyError, TypeError, ValueError):
        weather = fallback_weather(latitude, longitude, location_label)

    cache.set(_cache_key(latitude, longitude), weather, timeout=60 * 10)
    return weather
