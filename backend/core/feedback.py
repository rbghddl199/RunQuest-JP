from statistics import mean

from .models import RunningRecord
from .openai_service import enhance_feedback


def _pace_label(pace_seconds):
    if not pace_seconds:
        return '측정 전'
    minutes, seconds = divmod(round(pace_seconds), 60)
    return f"{minutes}'{seconds:02d}\"/km"


def generate_run_feedback(record):
    history = list(
        RunningRecord.objects.filter(
            user=record.user,
            status=RunningRecord.Status.COMPLETED,
        )
        .exclude(id=record.id)
        .order_by('-completed_at')[:10]
    )
    valid_history = [
        item for item in history
        if float(item.distance_km) > 0 and item.average_pace_seconds > 0
    ]

    distance = float(record.distance_km)
    pace = record.average_pace_seconds
    active_seconds = max(1, record.duration_seconds)
    pause_ratio = record.paused_seconds / active_seconds
    previous_distance = mean(
        float(item.distance_km) for item in valid_history
    ) if valid_history else 0
    previous_pace = mean(
        item.average_pace_seconds for item in valid_history
    ) if valid_history else 0

    if distance <= 0 or pace <= 0:
        return enhance_feedback({
            'score': 40,
            'headline': '첫 기록을 남긴 것부터 좋은 시작이에요',
            'summary': (
                '이동 거리가 충분히 측정되지 않아 페이스 비교는 생략했어요. '
                '다음 러닝에서는 GPS 권한과 위치 정확도를 확인해 주세요.'
            ),
            'achievements': ['러닝 세션을 끝까지 완료했어요.'],
            'cautions': ['출발 전 GPS 신호가 안정될 때까지 잠시 기다려 주세요.'],
            'next_goal': {
                'distance_km': 1.0,
                'pace_seconds': 0,
                'message': '다음에는 1km를 편안하게 기록해 보세요.',
            },
            'comparison': {
                'history_count': len(valid_history),
                'distance_change_percent': None,
                'pace_change_percent': None,
            },
        })

    distance_change = (
        round(((distance - previous_distance) / previous_distance) * 100)
        if previous_distance else None
    )
    pace_change = (
        round(((previous_pace - pace) / previous_pace) * 100)
        if previous_pace else None
    )

    achievements = []
    cautions = []
    score = 70

    if not valid_history:
        achievements.append(f'{distance:.2f}km의 기준 기록을 만들었어요.')
        score += 5
    else:
        if distance_change is not None and distance_change >= 5:
            achievements.append(f'최근 평균보다 거리를 {distance_change}% 늘렸어요.')
            score += min(12, distance_change // 3)
        elif distance_change is not None and distance_change <= -20:
            achievements.append('오늘 컨디션에 맞춰 거리를 안정적으로 조절했어요.')
        else:
            achievements.append('최근 러닝과 비슷한 거리를 꾸준히 유지했어요.')

        if pace_change is not None and pace_change >= 3:
            achievements.append(f'평균 페이스가 최근 기록보다 {pace_change}% 빨라졌어요.')
            score += min(12, pace_change)
        elif pace_change is not None and pace_change <= -10:
            cautions.append('최근보다 페이스가 느렸어요. 피로가 남았다면 회복을 우선하세요.')
            score -= 5
        else:
            achievements.append('페이스 변동을 크게 만들지 않고 안정적으로 달렸어요.')

    if pause_ratio <= 0.05:
        achievements.append('멈춤 시간을 5% 이내로 관리했어요.')
        score += 5
    elif pause_ratio >= 0.2:
        cautions.append('정지 시간이 길었어요. 다음에는 초반 속도를 조금 낮춰보세요.')
        score -= 7

    if pace < 300:
        cautions.append('강도 높은 러닝이었어요. 수분 보충과 충분한 회복이 필요해요.')
    elif pace > 600:
        achievements.append('무리하지 않는 회복 페이스로 몸을 잘 관리했어요.')

    if not cautions:
        cautions.append('통증이 느껴지면 기록보다 회복을 먼저 선택하세요.')

    score = max(40, min(98, score))
    next_distance = round(min(distance * 1.08, distance + 0.5), 1)
    next_pace = max(240, round(pace * 0.98))
    headline = (
        '최근 흐름보다 한 단계 성장했어요'
        if (distance_change or 0) >= 5 or (pace_change or 0) >= 3
        else '안정적인 리듬으로 오늘의 러닝을 완성했어요'
    )

    return enhance_feedback({
        'score': score,
        'headline': headline,
        'summary': (
            f'{distance:.2f}km를 평균 {_pace_label(pace)}로 달렸어요. '
            f'최근 {len(valid_history)}회 기록과 비교해 다음 러닝 목표를 계산했습니다.'
        ),
        'achievements': achievements[:3],
        'cautions': cautions[:2],
        'next_goal': {
            'distance_km': next_distance,
            'pace_seconds': next_pace,
            'message': (
                f'다음에는 {next_distance:.1f}km를 '
                f'{_pace_label(next_pace)} 안팎으로 편안하게 달려보세요.'
            ),
        },
        'comparison': {
            'history_count': len(valid_history),
            'distance_change_percent': distance_change,
            'pace_change_percent': pace_change,
        },
    })
