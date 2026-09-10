import hashlib
import re

from .gms_service import check_guardrail, enhance_chat_reply
from .models import Course, RunningRecord
from .recommendations import location_fit


DISTANCE_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:km|킬로|키로|킬로미터)',
    re.IGNORECASE,
)
ASCII_DISTANCE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*k\s*m', re.IGNORECASE)
COURSE_NAME_NOISE_PATTERN = re.compile(
    r'(러닝|조깅|코스|추천|알려|소개|해줘|해 줘|보여|찾아|좀|를|을|이|가|은|는|의|\s+)'
)

KEYWORDS = {
    'night': ('야간', '밤', '저녁', '퇴근', '어두운'),
    'morning': ('아침', '새벽', '오전'),
    'park': ('공원', '수목원', '나무', '초록', '숲'),
    'river': ('강', '하천', '천변', '강변', '갑천', '대전천', '유등천', '호수', '대청호'),
    'urban': ('도심', '시내', '조명', '엑스포', '광장'),
    'trail': ('산', '트레일', '오르막', '언덕', '등산', '보문산', '숲길'),
    'quiet': ('조용', '사람 적', '한적', '차분'),
    'beginner': ('초보', '쉬운', '가볍게', '천천히', '무리 없이', '입문'),
    'intense': ('강도', '힘들게', '훈련', '체력', '빠르게', '인터벌', '오르막', '언덕'),
    'safety': ('안전', '밝', '조명', '무섭지'),
    'tired': ('피곤', '지침', '무릎', '통증', '아파', '회복', '오랜만'),
    'diet': ('식단', '밥', '먹', '메뉴', '음식', '아침밥', '점심', '저녁밥', '간식', '칼로리', '단백질', '다이어트'),
    'weather': ('날씨', '비', '눈', '더워', '추워', '미세먼지', '바람'),
}

GREETING_WORDS = ('안녕', '반가워', '하이', 'hello')
THANKS_WORDS = ('고마워', '감사', '좋아', '오케이')
DAILY_CHAT_WORDS = (
    '식단',
    '밥',
    '먹',
    '메뉴',
    '음식',
    '간식',
    '수분',
    '스트레칭',
    '휴식',
    '잠',
    '수면',
    '컨디션',
    '근육통',
    '날씨',
    '기분',
)
RUN_REQUEST_WORDS = (
    '코스',
    '러닝',
    '달리',
    '뛰',
    '운동',
    '추천',
    'km',
    '킬로',
    '키로',
    '거리',
    '페이스',
)
QUESTION_WORDS = ('어디', '어떤', '추천', '알려', '찾아', '좋을까', '뛸까')
RECOMMENDATION_REQUEST_WORDS = (
    '추천',
    '코스 추천',
    '추천해',
    '알려줘',
    '알려주',
    '찾아줘',
    '찾아주',
    '골라줘',
    '골라주',
)


def contains_any(text, words):
    return any(word in text for word in words)


def normalize_course_name(text):
    normalized = str(text or '').lower()
    normalized = COURSE_NAME_NOISE_PATTERN.sub('', normalized)
    return re.sub(r'[^0-9a-z가-힣]', '', normalized)


def find_named_course(message):
    target = normalize_course_name(message)
    if len(target) < 2:
        return None

    best_course = None
    best_score = 0
    for course in Course.objects.filter(is_active=True):
        names = {
            normalize_course_name(course.name),
            normalize_course_name(course.slug),
        }
        tags = course.tags if isinstance(course.tags, list) else []
        names.update(normalize_course_name(tag) for tag in tags)

        for name in names:
            if len(name) < 2:
                continue
            if name and len(name) >= 3 and name in target:
                score = len(name) + 20
            elif target and len(target) >= 3 and target in name:
                score = len(target) + 10
            else:
                score = len(set(re.findall(r'[가-힣a-z0-9]+', name)) & set(re.findall(r'[가-힣a-z0-9]+', target)))
            if score > best_score:
                best_score = score
                best_course = course

    return best_course if best_score >= 6 else None


def parse_context(message, previous=None):
    text = message.lower().strip()
    has_explicit_signal = (
        DISTANCE_PATTERN.search(text)
        or ASCII_DISTANCE_PATTERN.search(text)
        or any(contains_any(text, words) for words in KEYWORDS.values())
        or contains_any(text, RECOMMENDATION_REQUEST_WORDS)
    )
    if has_explicit_signal:
        previous = previous or {}
        context = {
            key: previous[key]
            for key in ('latitude', 'longitude')
            if key in previous
        }
        if previous.get('safety_adjusted'):
            context['safety_adjusted'] = True
            if previous.get('difficulty') == 'easy':
                context['difficulty'] = 'easy'
    else:
        context = dict(previous or {})
    context.pop('named_course_slug', None)
    distance_match = DISTANCE_PATTERN.search(text) or ASCII_DISTANCE_PATTERN.search(text)
    if distance_match:
        context['distance_km'] = min(15.0, max(1.0, float(distance_match.group(1))))

    matched = set()
    for key, words in KEYWORDS.items():
        if contains_any(text, words):
            matched.add(key)
            context[key] = True

    if 'night' in matched:
        context['preferred_time'] = 'night'
    elif 'morning' in matched:
        context['preferred_time'] = 'morning'

    for course_type in ('park', 'river', 'urban', 'trail'):
        if course_type in matched:
            context['course_type'] = course_type
            break

    if 'tired' in matched:
        context['difficulty'] = 'easy'
        current_distance = context.get('distance_km', 4.0)
        context['distance_km'] = min(current_distance, 4.0)
        context['safety_adjusted'] = True
    elif 'beginner' in matched:
        context['difficulty'] = 'easy'
        context.pop('safety_adjusted', None)
    elif 'intense' in matched:
        context['difficulty'] = 'hard'
        context.pop('safety_adjusted', None)

    return context


def has_specific_running_signal(text):
    return (
        DISTANCE_PATTERN.search(text)
        or ASCII_DISTANCE_PATTERN.search(text)
        or any(contains_any(text, words) for words in KEYWORDS.values())
        or contains_any(text, QUESTION_WORDS)
    )


def wants_course_recommendation(text):
    return contains_any(text, RECOMMENDATION_REQUEST_WORDS)


EXPLICIT_COURSE_REQUEST_WORDS = (
    '추천',
    '추천해',
    '추천해줘',
    '추천해줄래',
    '알려줘',
    '찾아줘',
    '찾아줄래',
    '골라줘',
    '보여줘',
    '제안',
)
COURSE_TOPIC_WORDS = (
    '코스',
    '러닝',
    '달리기',
    '뛰기',
    '뛸',
    '런닝',
    'route',
    'course',
    'km',
)
COURSE_DESIRE_WORDS = (
    '싶',
    '뛰고',
    '달리고',
    '뛸까',
    '달릴까',
    '가볍게',
    '안전',
)
CASUAL_RUNNING_TALK_WORDS = (
    '뛰었',
    '달렸',
    '완료',
    '기록',
    '힘들',
    '피곤',
    '아파',
)


KOREAN_COURSE_TOPIC_WORDS = (
    '코스',
    '러닝',
    '달리',
    '뛰',
    '런닝',
    '운동',
    'km',
)
KOREAN_COURSE_REQUEST_WORDS = (
    '추천',
    '알려줘',
    '알려주',
    '찾아줘',
    '찾아주',
    '골라줘',
    '골라주',
    '보여줘',
)
KOREAN_COURSE_DESIRE_WORDS = (
    '싶',
    '뛰고',
    '달리고',
    '뛸까',
    '달릴까',
    '가볍게',
    '안전',
)


def is_explicit_course_request(text):
    has_topic = contains_any(text, COURSE_TOPIC_WORDS) or contains_any(text, KOREAN_COURSE_TOPIC_WORDS)
    has_request = (
        wants_course_recommendation(text)
        or contains_any(text, EXPLICIT_COURSE_REQUEST_WORDS)
        or contains_any(text, KOREAN_COURSE_REQUEST_WORDS)
    )
    has_desire = contains_any(text, COURSE_DESIRE_WORDS) or contains_any(text, KOREAN_COURSE_DESIRE_WORDS)
    has_distance = DISTANCE_PATTERN.search(text) or ASCII_DISTANCE_PATTERN.search(text)

    if contains_any(text, CASUAL_RUNNING_TALK_WORDS) and not has_request:
        return False
    if has_request and (has_topic or has_specific_running_signal(text)):
        return True
    if has_request and (has_topic or has_distance):
        return True
    if has_distance and has_topic and has_desire:
        return True
    if has_topic and has_desire and has_specific_running_signal(text):
        return True
    return False


def infer_intent(message):
    text = message.lower().strip()
    has_run_word = contains_any(text, RUN_REQUEST_WORDS) or contains_any(text, KOREAN_COURSE_TOPIC_WORDS)
    has_daily_word = contains_any(text, DAILY_CHAT_WORDS)
    if contains_any(text, GREETING_WORDS) and not has_run_word:
        return 'greeting'
    if contains_any(text, THANKS_WORDS) and not has_run_word:
        return 'thanks'
    if has_daily_word and not is_explicit_course_request(text):
        return 'daily_chat'
    if has_run_word and contains_any(text, CASUAL_RUNNING_TALK_WORDS) and not is_explicit_course_request(text):
        return 'daily_chat'
    if has_run_word and is_explicit_course_request(text):
        return 'course_recommendation'
    if has_run_word:
        return 'needs_detail'
    if has_daily_word:
        return 'daily_chat'
    return 'small_talk'


def user_preferences(user):
    survey = getattr(user, 'survey_response', None)
    records = RunningRecord.objects.filter(
        user=user,
        status=RunningRecord.Status.COMPLETED,
    ).select_related('course')
    course_types = [
        record.course.course_type for record in records if record.course_id
    ]
    preferred_type = None
    if course_types:
        preferred_type = max(set(course_types), key=course_types.count)
    return {
        'survey_type': getattr(survey, 'course_type', None),
        'survey_time': getattr(survey, 'preferred_time', None),
        'experience': getattr(survey, 'experience_level', None),
        'record_type': preferred_type,
    }


def course_score(course, context, preferences, recent_course_ids=None):
    score = float(course.popularity_score) * 0.12
    reasons = []
    location_distance_km = None
    recent_course_ids = recent_course_ids or set()
    target_distance = context.get('distance_km')
    if target_distance:
        gap = abs(float(course.distance_km) - target_distance)
        score += max(0, 45 - gap * 12)
        if gap <= 1:
            reasons.append(f'원하는 {target_distance:g}km와 가까운 거리')

    course_type = context.get('course_type')
    if course_type:
        if course.course_type == course_type:
            score += 58
            reasons.append(f'{course.get_course_type_display()} 선호 반영')
        else:
            score -= 24
    elif course.course_type in {
        preferences.get('survey_type'),
        preferences.get('record_type'),
    }:
        score += 10
        reasons.append('기록과 선호도에 맞는 코스 유형')

    preferred_time = context.get('preferred_time')
    if preferred_time:
        if preferred_time in course.recommended_times:
            score += 24
            reasons.append('원하는 시간대에 적합')
        else:
            score -= 12

    difficulty = context.get('difficulty')
    if difficulty == 'easy':
        score += 22 if course.difficulty == 'easy' else -25
        if course.difficulty == 'easy':
            reasons.append('부담이 적은 쉬운 난이도')
    elif difficulty == 'hard':
        score += 25 if course.difficulty == 'hard' else 4
        if course.difficulty == 'hard':
            reasons.append('운동 강도를 높이기 좋은 난이도')

    if context.get('safety') and (
        'night' in course.recommended_times
        or 'evening' in course.recommended_times
        or course.course_type in {'urban', 'river'}
    ):
        score += 28
        reasons.append('야간 조명과 접근성 고려')
    if context.get('quiet'):
        score += 18 if course.course_type in {'park', 'lake', 'trail'} else 0
        reasons.append('차분한 러닝 환경')
    if context.get('safety_adjusted') and float(course.distance_km) > 4:
        score -= 35
    if course.id in recent_course_ids:
        score -= 18

    latitude = context.get('latitude')
    longitude = context.get('longitude')
    if latitude is not None and longitude is not None:
        location_score, location_distance_km = location_fit(
            course,
            latitude,
            longitude,
        )
        score += location_score * 0.35
        if location_distance_km is not None:
            reasons.append(f'현재 위치에서 약 {location_distance_km:g}km 떨어진 코스')

    return score, reasons[:3], location_distance_km


def recommend_course(user, context, recent_messages=None):
    preferences = user_preferences(user)
    recent_course_ids = set()
    for message in recent_messages or []:
        course_id = message.get('recommended_course_id')
        if course_id:
            recent_course_ids.add(course_id)

    ranked = []
    for course in Course.objects.filter(is_active=True):
        score, reasons, location_distance_km = course_score(
            course,
            context,
            preferences,
            recent_course_ids=recent_course_ids,
        )
        ranked.append((score, course, reasons, location_distance_km))

    target_distance = context.get('distance_km')
    if target_distance:
        tolerance = max(0.8, float(target_distance) * 0.2)
        distance_matched = [
            item for item in ranked
            if abs(float(item[1].distance_km) - float(target_distance)) <= tolerance
        ]
        if distance_matched:
            ranked = distance_matched

    if context.get('difficulty') == 'easy':
        easy_ranked = [item for item in ranked if item[1].difficulty == 'easy']
        if easy_ranked:
            ranked = easy_ranked

    ranked.sort(key=lambda item: item[0], reverse=True)
    candidate_pool = ranked[: min(4, len(ranked))]
    if not candidate_pool:
        return ranked[0]
    seed_text = f"{user.id}:{context.get('distance_km')}:{context.get('course_type')}:{context.get('difficulty')}:{context.get('preferred_time')}:{len(recent_course_ids)}"
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:8], 16)
    return candidate_pool[seed % len(candidate_pool)]


def build_daily_reply(message):
    text = message.lower().strip()
    if '기분' in text or '컨디션' in text:
        return (
            '그런 날은 바로 강도를 정하기보다 몸 상태를 한 번 나눠서 보는 게 좋아요. '
            '피로감, 다리 무거움, 수면 상태를 먼저 확인해보고 괜찮다면 짧게 걷거나 가볍게 조깅하는 정도로 시작해보세요.'
        )
    if contains_any(text, CASUAL_RUNNING_TALK_WORDS):
        return (
            '오늘 러닝 얘기 들려줘서 좋아요. 힘들게 느껴졌다면 기록보다 회복을 먼저 챙기는 게 좋아요. '
            '물 한두 잔을 나눠 마시고, 종아리와 허벅지를 가볍게 풀어준 뒤 컨디션을 다시 확인해보세요.'
        )
    if contains_any(text, KEYWORDS['diet']):
        return (
            '러닝 전에는 바나나, 토스트처럼 부담 적은 탄수화물을 가볍게 먹고, '
            '러닝 후에는 단백질과 수분을 챙겨 회복을 도와주세요.'
        )
    if '수면' in text or '잠' in text:
        return '수면이 부족한 날은 기록보다 회복이 먼저예요. 오늘은 짧은 조깅이나 산책 강도로 낮춰보세요.'
    if '스트레칭' in text or '근육통' in text:
        return '근육통이 있으면 동적 스트레칭으로 몸을 데우고, 통증이 sharp하게 느껴지면 러닝은 쉬는 편이 좋아요.'
    if contains_any(text, KEYWORDS['weather']):
        return '날씨가 애매한 날은 강도를 낮추고 노면, 바람, 체감온도를 먼저 확인해 주세요. 안전하면 짧게 시작해도 충분해요.'
    return '좋아요. 러닝, 식단, 회복, 컨디션처럼 일상적인 운동 루틴도 편하게 물어봐 주세요.'


def build_assistant_reply(user, message, previous_context=None, recent_messages=None):
    guardrail = check_guardrail(message)
    if not guardrail['result']:
        return {
            'intent': 'blocked',
            'context': dict(previous_context or {}),
            'content': (
                '이 요청은 안전한 대화를 위해 처리할 수 없어요. '
                '러닝 코스, 운동 기록, 커뮤니티와 관련된 질문으로 다시 물어봐 주세요. '
                f"({guardrail['reason']})"
            ),
            'provider': 'gms_guardrail',
            'guardrail': guardrail,
            'gms_requests': {
                'guardrail': guardrail.get('request'),
                'answer': None,
            },
            'course': None,
            'score': None,
            'reasons': [],
        }

    intent = infer_intent(message)
    context = parse_context(message, previous_context)
    named_course = find_named_course(message)
    if named_course and is_explicit_course_request(message.lower().strip()):
        intent = 'course_recommendation'
        context = {
            key: value
            for key, value in context.items()
            if key in {'latitude', 'longitude'}
        }
        context['named_course_slug'] = named_course.slug
    course = None
    reasons = []
    score = None
    location_distance_km = None

    if intent == 'greeting':
        local_content = (
            f'{user.profile.nickname}님, 반가워요! '
            '원하는 거리, 시간대, 분위기만 알려주면 딱 맞는 러닝 코스를 찾아드릴게요.'
        )
    elif intent == 'thanks':
        local_content = '천만에요. 오늘 컨디션에 맞춰 안전하고 즐거운 러닝 하세요!'
    elif intent == 'needs_detail':
        local_content = (
            '코스를 추천하려면 조금만 더 알려주세요. '
            '예를 들면 “야간에도 안전한 5km 코스”, “초보자에게 쉬운 공원 코스”처럼요.'
        )
    elif intent == 'daily_chat':
        local_content = build_daily_reply(message)
    elif intent == '__legacy_small_talk__':
        local_content = (
            '편하게 이야기해도 좋아요. 러닝 코스뿐 아니라 식단, 회복, 컨디션 관리도 같이 도와드릴게요.'
        )
    elif intent == 'small_talk':
        local_content = (
            '편하게 이야기해도 좋아요. 오늘 컨디션이나 기분을 들려주면 러닝을 해야 할지, '
            '쉬어도 괜찮을지 같이 정리해볼게요. 코스 추천이 필요할 때는 원하는 거리나 '
            '분위기를 말해주면 그때 맞춰서 찾아드릴게요.'
        )
    else:
        if named_course:
            course = named_course
            score = None
            reasons = ['요청한 코스명을 직접 확인했어요']
        else:
            score, course, reasons, location_distance_km = recommend_course(
                user,
                context,
                recent_messages=recent_messages,
            )
        safety_text = (
            '현재 컨디션을 고려해서 평소보다 짧고 쉬운 코스로 보정했어요. '
            if context.get('safety_adjusted')
            else ''
        )
        reason_text = ', '.join(reasons) if reasons else '최근 기록과 코스 인기도'
        local_content = (
            f'{safety_text}{course.name}를 추천할게요. '
            f'{course.distance_km}km, 약 {course.estimated_minutes}분 코스이고 '
            f'{reason_text} 때문에 잘 맞아요. 상세 페이지에서 지도를 확인한 뒤 적용해보세요.'
        )

    content, provider, answer_request = enhance_chat_reply(
        message,
        context,
        course,
        local_content,
        intent,
        recent_messages=recent_messages,
    )
    return {
        'intent': intent,
        'context': context,
        'content': content,
        'provider': provider,
        'guardrail': guardrail,
        'gms_requests': {
            'guardrail': guardrail.get('request'),
            'answer': answer_request,
        },
        'course': course,
        'score': round(score, 2) if score is not None else None,
        'reasons': reasons,
        'location': {
            'applied': context.get('latitude') is not None and context.get('longitude') is not None,
            'distance_km': location_distance_km,
        },
    }
