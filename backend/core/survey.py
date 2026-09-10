SURVEY_QUESTIONS = [
    {
        'key': 'experience_level',
        'number': 1,
        'title': '러닝 경험 수준을 선택해 주세요.',
        'options': [
            {'value': 'beginner', 'label': '초보자', 'icon': 'sprout'},
            {'value': 'intermediate', 'label': '중급자', 'icon': 'runner'},
            {'value': 'advanced', 'label': '상급자', 'icon': 'medal'},
        ],
    },
    {
        'key': 'distance_range',
        'number': 2,
        'title': '한 번에 보통 얼마나 뛰시나요?',
        'options': [
            {'value': 'unknown', 'label': '잘 모르겠어요'},
            {'value': '1_3km', 'label': '1~3km'},
            {'value': '3_5km', 'label': '3~5km'},
            {'value': '5_10km', 'label': '5~10km'},
            {'value': '10km_plus', 'label': '10km 이상'},
        ],
    },
    {
        'key': 'course_type',
        'number': 3,
        'title': '선호하는 코스 타입은 무엇인가요?',
        'options': [
            {'value': 'river', 'label': '강/하천 코스'},
            {'value': 'park', 'label': '공원 코스'},
            {'value': 'urban', 'label': '도심 코스'},
            {'value': 'trail', 'label': '산/트레킹 코스'},
            {'value': 'coast', 'label': '해안 코스'},
            {'value': 'any', 'label': '상관없음'},
        ],
    },
    {
        'key': 'preferred_time',
        'number': 4,
        'title': '선호하는 러닝 시간대는 언제인가요?',
        'options': [
            {'value': 'morning', 'label': '아침'},
            {'value': 'afternoon', 'label': '오후'},
            {'value': 'evening', 'label': '저녁'},
            {'value': 'night', 'label': '야간'},
            {'value': 'any', 'label': '상관없음'},
        ],
    },
    {
        'key': 'running_style',
        'number': 5,
        'title': '선호하는 러닝 방식은 무엇인가요?',
        'options': [
            {'value': 'solo', 'label': '혼자 뛰기'},
            {'value': 'small_group', 'label': '소규모로 뛰기'},
            {'value': 'crew', 'label': '크루와 함께 뛰기'},
            {'value': 'any', 'label': '상관없음'},
        ],
    },
    {
        'key': 'running_goal',
        'number': 6,
        'title': '러닝을 하는 목적은 무엇인가요?',
        'options': [
            {'value': 'health', 'label': '건강 관리', 'icon': 'heart'},
            {'value': 'weight_loss', 'label': '체중 감량', 'icon': 'scale'},
            {'value': 'endurance', 'label': '체력 향상', 'icon': 'dumbbell'},
            {'value': 'stress_relief', 'label': '스트레스 해소', 'icon': 'smile'},
            {'value': 'performance', 'label': '기록 향상', 'icon': 'chart'},
            {'value': 'race', 'label': '대회 준비', 'icon': 'trophy'},
        ],
    },
]


DISTANCE_TARGETS = {
    'unknown': 3.0,
    '1_3km': 2.0,
    '3_5km': 4.0,
    '5_10km': 7.5,
    '10km_plus': 12.0,
}

EXPERIENCE_SCORES = {
    'beginner': 1,
    'intermediate': 2,
    'advanced': 3,
}

GOAL_PROFILES = {
    'health': {'intensity': 1, 'pace_focus': 0.3, 'recovery_focus': 0.8},
    'weight_loss': {'intensity': 2, 'pace_focus': 0.4, 'recovery_focus': 0.5},
    'endurance': {'intensity': 2, 'pace_focus': 0.6, 'recovery_focus': 0.4},
    'stress_relief': {'intensity': 1, 'pace_focus': 0.2, 'recovery_focus': 1.0},
    'performance': {'intensity': 3, 'pace_focus': 1.0, 'recovery_focus': 0.3},
    'race': {'intensity': 3, 'pace_focus': 0.9, 'recovery_focus': 0.4},
}


def build_score_profile(validated_data):
    experience = validated_data['experience_level']
    goal = validated_data['running_goal']
    course_type = validated_data['course_type']
    preferred_time = validated_data['preferred_time']
    running_style = validated_data['running_style']

    safety_adjustment = 0.85 if experience == 'beginner' else 1.0
    if goal in {'performance', 'race'} and experience == 'advanced':
        safety_adjustment = 1.05

    return {
        'experience_score': EXPERIENCE_SCORES[experience],
        'target_distance_km': DISTANCE_TARGETS[validated_data['distance_range']],
        'preferred_course_types': (
            ['river', 'park', 'urban', 'trail']
            if course_type in {'any', 'coast'}
            else [course_type]
        ),
        'preferred_time': preferred_time,
        'social_preference': running_style,
        'goal': goal,
        'goal_profile': GOAL_PROFILES[goal],
        'safety_adjustment': safety_adjustment,
        'survey_weight': 1.0,
        'record_weight': 0.0,
    }
