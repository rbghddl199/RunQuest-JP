# RunQuest Fixtures

RunQuest fixture pack은 발표와 로컬 테스트를 위해 고정된 JSON 데이터로 구성되어 있습니다. 원본 데이터는 현재 프로젝트의 Django 모델 구조에 맞게 변환되어 로드됩니다.

## 핵심 조건

- 가입일과 설문조사 등록일은 동일합니다.
- 모든 활동은 가입일과 설문조사 등록일 이후에 생성됩니다.
- 게시글 작성 이후에 댓글, 좋아요, 북마크가 생성됩니다.
- 댓글 작성자도 댓글 생성일 이전에 가입을 완료한 사용자입니다.
- 2026년 3월부터 2026년 6월까지 활동 날짜가 다양하게 분포되어 있습니다.
- `pro01@runquest.com` 사용자는 2026-03-14부터 2026-06-21까지 100일 연속 러닝 기록을 보유합니다.
- 복귀 사용자는 최근 30일 러닝 기록이 없도록 구성되어 있습니다.

## Directories

- `source/`: 전달받은 원본 14개 JSON 파일
- `runquest/`: 현재 `auth` 및 `core` 모델 구조로 변환된 로드용 fixture

원본과 현재 프로젝트는 앱 라벨과 필드 구조가 다르므로 `source/` 파일을 직접 `loaddata`하지 않습니다.

## Convert

원본 fixture를 현재 모델 구조로 다시 변환해야 할 때 실행합니다.

```powershell
python scripts/convert_runquest_fixtures.py
```

## Load

권장 로드 방식은 전용 management command입니다.

```powershell
python backend/manage.py load_runquest_fixtures --reset
```

`--reset`은 현재 DB 데이터를 모두 삭제한 뒤 fixture를 다시 로드합니다. 시연 데이터 재설정 용도로만 사용합니다.

전용 command는 내부적으로 `runquest/` fixture를 올바른 순서로 로드한 뒤, `polish_demo_data`를 실행해 대표 계정의 러닝 기록, 커뮤니티 글, 알림을 발표용 흐름에 맞게 보강합니다.

현재 DB를 초기화하지 않고 시연 데이터의 문장과 대표 계정 흐름만 정리하려면 아래 명령을 실행합니다.

```powershell
python backend/manage.py polish_demo_data
```

```powershell
python backend/manage.py loaddata backend/fixtures/runquest/01_users.json
python backend/manage.py loaddata backend/fixtures/runquest/02_courses.json
python backend/manage.py loaddata backend/fixtures/runquest/03_badges.json
python backend/manage.py loaddata backend/fixtures/runquest/04_surveys.json
python backend/manage.py loaddata backend/fixtures/runquest/05_running_records.json
python backend/manage.py loaddata backend/fixtures/runquest/06_attendance.json
python backend/manage.py loaddata backend/fixtures/runquest/07_saved_courses.json
python backend/manage.py loaddata backend/fixtures/runquest/08_user_badges.json
python backend/manage.py loaddata backend/fixtures/runquest/09_posts.json
python backend/manage.py loaddata backend/fixtures/runquest/10_comments.json
python backend/manage.py loaddata backend/fixtures/runquest/11_post_likes.json
python backend/manage.py loaddata backend/fixtures/runquest/12_post_bookmarks.json
python backend/manage.py loaddata backend/fixtures/runquest/13_chatbot_history.json
python backend/manage.py loaddata backend/fixtures/runquest/14_recommend_history.json
```

## Demo Accounts

공통 비밀번호는 `!@1q2w3e4r`입니다.

| 목적 | 이메일 | 설명 |
| --- | --- | --- |
| 신규 사용자 | `new@runquest.com` | 러닝 기록이 거의 없고 설문 기반 추천 확인용 |
| 기존 사용자 | `runner@runquest.com` | 최근 기록을 반영한 추천 확인용 |
| 100일 연속 러너 | `pro01@runquest.com` | 100일 연속 러닝 기록 사용자 |
| 복귀 사용자 | `comeback@runquest.com` | 오래된 기록과 복귀 안전 보정 확인용 |

추가 계정군:

- `new01@runquest.com`부터 `new10@runquest.com`
- `beginner01@runquest.com`부터 `beginner10@runquest.com`
- `pro02@runquest.com`부터 `pro05@runquest.com`
- `comeback01@runquest.com`부터 `comeback07@runquest.com`

## Counts

| 데이터 | 개수 |
| --- | ---: |
| 사용자 | 50 |
| 코스 | 20 |
| 배지 | 10 |
| 설문 | 50 |
| 러닝 기록 | 664 |
| 출석 날짜 | 654 |
| 찜한 코스 | 94 |
| 사용자 배지 | 130 |
| 게시글 | 50 |
| 댓글 | 150 |
| 좋아요 | 400 |
| 게시글 저장 | 70 |
| 챗봇 메시지 | 12 |
| 추천 이력 | 50 |

러닝 기록보다 출석이 10개 적은 것은 같은 사용자에게 같은 날짜의 복수 러닝이 있기 때문입니다. RunQuest는 사용자별 하루 한 번만 출석 처리합니다.

## Validation

원본 fixture 문서 기준 검증 결과:

- status: `PASS`
- violation_count: `0`

모델명이나 필드명이 변경되면 `scripts/convert_runquest_fixtures.py`와 `runquest/` fixture를 함께 갱신해야 합니다.
