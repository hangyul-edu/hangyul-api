# 기능 명세서 — 한귤 한국어 학습 플랫폼

- OpenAPI / Swagger UI: `GET /openapi.json`, `GET /docs`

---

## 1. 제품 개요

한귤(Hangyul)은 비원어민을 위한 모바일 한국어 학습 서비스다. 학습은 **회화(Conversation)**와 **TOPIK** 두 개의 카테고리로 나뉘며, 각 카테고리는 **강의(lectures)**와 **문장 학습(sentences)**이라는 두 개의 독립된 진행 트랙(progression)을 가진다. 각 진행 트랙은 자체 현재 레벨을 관리한다. TOPIK은 추가로 목표 급수(1–6)를 가진다. 여기에 연속 학습일수(streak), 적응형 문장 추천, 영상 강의, 퀴즈, AI 대화 파트너, 소셜 리그가 결합된다.

### 1.1 핵심 사용자 목표

| 목표 | 지원 기능 |
|---|---|
| 일상 회화 수준 한국어 구사 | 문장 학습, 한글AI 대화, 듣기·말하기 레슨 |
| 목표 TOPIK 급수 합격 | TOPIK 트랙, 레벨별 잠금 해제 레슨, 모의 퀴즈 |
| 매일 학습 습관 만들기 | 연속 학습일수, 목표 설정, 리마인더, 푸시 알림 |
| 지속적인 동기 부여 | 리그 티어, 시즌 랭킹, 친구 피드 |
| 문의 및 도움 받기 | FAQ, 1:1 문의, 공지사항 |

---

## 2. 페르소나

| 페르소나 | 설명 | 핵심 플로우 |
|---|---|---|
| **입문자 Bea** | K-문화에 관심이 있고 한국어는 처음. | 온보딩 → 추천 레벨 1 → 연속 학습 |
| **수험생 Eun** | TOPIK 3·4급 목표. | TOPIK 트랙, 일일 퀴즈, 작문 피드백 |
| **바쁜 Ben** | 하루 10분, 출퇴근 중 학습. | 대시보드 목표, 오디오 문장, 리마인더 |
| **사교형 Sora** | 친구 초대로 가입한 기존 학습자. | 친구 코드, 피드, 리그 랭킹 |

---

## 3. 공통 규칙

### 3.1 인증 및 세션

- **플로우:** OAuth2 password 플로우 + JWT 액세스 토큰(30분) + 리프레시 토큰(30일).
- **소셜 공급자:** Google, Apple, Kakao, Facebook, Line — 공급자 `id_token`을 동일한 토큰 응답 구조로 교환.
- **휴대폰 인증**은 (a) 회원가입, (b) 이메일 찾기, (c) 비밀번호 재설정 시 필수. SMS 코드는 5분 TTL, 재발송 쿨다운 60초.
- **회원 탈퇴:** 비밀번호 재입력(또는 소셜 재인증)을 요구하며, 개인정보 처리방침에 따라 데이터 삭제를 예약.
- **Bearer 헤더:** 모든 인증 요청에 `Authorization: Bearer <access_token>` 포함. Swagger "Authorize"는 `/auth/login/oauth2`를 사용.

### 3.2 에러 응답 규격 (RFC 7807)

모든 4xx / 5xx 응답은 `application/problem+json`을 사용:

```json
{
  "type": "about:blank#validation_error",
  "title": "ValidationError",
  "status": 422,
  "code": "validation_error",
  "detail": "One or more fields failed validation.",
  "instance": "/auth/signup/email",
  "errors": [ ... ]
}
```

사용 중인 코드: `validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `rate_limited`, `internal_error`, `http_<status>`.

### 3.3 페이지네이션

커서 기반:

```json
{ "items": [...], "next_cursor": "opaque-string|null", "has_more": true }
```

기본 페이지 크기 20건(최소 1, 최대 100). 클라이언트는 `next_cursor == null`일 때 중단해야 한다.

### 3.4 로케일 및 시간

- API 본문은 UTF-8.
- 타임스탬프는 ISO-8601 UTC.
- UI 언어 코드: `ko`, `en`, `ja`, `zh-CN`, `zh-TW`, `vi`, `th`, `id`.
- 전화번호는 E.164 형식.

### 3.5 비기능 요구사항

| 항목 | 목표치 |
|---|---|
| API p95 응답 시간 (읽기) | ≤ 200 ms |
| API p95 응답 시간 (인증, AI) | ≤ 800 ms |
| 가용성 | 월 99.9 % |
| 요청 제한 (비로그인) | IP당 분당 30회 |
| 요청 제한 (로그인) | 사용자당 분당 120회 |
| JWT 순환 | 액세스 토큰 수명당 1회 리프레시 |
| 비밀번호 규칙 | 8–64자, 대소문자 + 숫자 조합 |

---

## 4. 기능 모듈

아래 각 모듈은 Figma 디자인의 한 섹션, `src/modules/` 하위 모듈, OpenAPI 명세의 태그 그룹에 1:1 대응한다.

### 4.1 인증 (`auth`)

**화면:** 스플래시 / 언어 선택 · 이메일 회원가입 · 소셜 회원가입(5개 공급자) · 휴대폰 인증 · 이메일·비밀번호 찾기 · 가입 완료.

**사용자 스토리**

- 신규 사용자로서 이메일·비밀번호 또는 소셜 공급자로 가입해 즉시 학습을 시작하고 싶다.
- 기존 사용자로서 휴대폰 번호로 이메일이나 비밀번호를 재확인하고 싶다.
- 모든 사용자로서 계정을 탈퇴하고 내 데이터가 삭제되길 원한다.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `POST /auth/signup/email` | 이메일 + 비밀번호 회원가입 |
| `POST /auth/login/email` | 로그인 |
| `POST /auth/login/oauth2` | Swagger UI password-플로우 전용 |
| `POST /auth/login/social` | 소셜 로그인 (Google / Apple / Kakao / Facebook / Line) |
| `POST /auth/phone/verification` | SMS 인증 코드 발송 |
| `POST /auth/phone/verification/confirm` | SMS 코드 확인 → 단기 인증 토큰 발급 |
| `POST /auth/email/recover` | 인증 토큰으로 이메일 찾기 |
| `POST /auth/password/reset` | 휴대폰 인증 후 비밀번호 재설정 |
| `POST /auth/token/refresh` | 액세스 · 리프레시 토큰 갱신 |
| `POST /auth/logout` | 리프레시 토큰 폐기 |
| `DELETE /auth/account` | 회원 탈퇴 |

**비즈니스 규칙**

- 닉네임은 2–20자, 비밀번호는 8–64자.
- 회원가입 시 이용약관 및 개인정보 처리방침 동의 필수.
- 소셜 계정은 (공급자 + subject) 기준으로 중복 제거.
- SMS 코드 발송 제한: 전화번호당 시간당 5회. 초과 시 `rate_limited` 반환.

---

### 4.2 사용자 프로필 및 검색 (`users`)

**화면:** 프로필 편집 · 닉네임 중복 확인 · 아바타 선택 · 친구 검색.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /users/me` | 내 프로필 스냅샷 |
| `PATCH /users/me` | 닉네임 / 아바타 / 언어 변경 |
| `POST /users/me/avatar` | 아바타 이미지 업로드 |
| `POST /users/check-nickname` | 닉네임 중복 확인 |
| `GET /users/search?code=&nickname=` | 친구 코드 또는 닉네임으로 사용자 검색 |
| `GET /users/{user_id}/profile` | 공개 학습 프로필 |
| `POST /users/feedback` | 추천 결과 피드백 신호 |

**비즈니스 규칙**

- 닉네임은 대소문자 구분 없이 유일해야 한다.
- `friend_code`는 사용자당 고유한 6–8자 코드로, 친구 추가에 사용.

---

### 4.3 온보딩 (`onboarding`)

**화면:** 학습 목적 (회화 / TOPIK) · 회화 수준 · 목표 TOPIK 급수 · 일일 목표 · 푸시 동의.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /onboarding/questions` | 온보딩 캐러셀용 질문 세트 |
| `POST /onboarding/responses` | 응답 저장 → 추천 트랙·레벨 반환 |
| `GET /onboarding/status` | 온보딩 완료 여부 확인 |

**비즈니스 규칙**

- `purpose`가 주 학습 카테고리를 결정한다.
  - `conversation`: 회화 카테고리의 강의·문장 진행 `current_level`을 `speaking_level` 응답으로 초기화한다.
  - `topik`: TOPIK의 두 진행 모두 `current_level = 1`로 시작하고, `topik_target`을 TOPIK `target_grade`(1–6)로 저장한다.
- 위에서 초기화된 값은 이후 설정 화면에서 모두 변경 가능하다.
- 일일 목표 기본값은 10분, 허용 범위는 5–120분.

---

### 4.4 구독 (`subscriptions`)

**화면:** 대시보드 페이월 · 요금제 비교 ($7.99 / 프로모션 $5.99 / 연 $54) · 결제 확인 · 구매 복원 · 구매 내역.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /subscriptions/plans` | 요금제 목록(프로모션 가격 포함) |
| `GET /subscriptions/me` | 내 구독 상태 |
| `POST /subscriptions/checkout` | 결제 세션 생성 (Stripe / Apple / Google) |
| `POST /subscriptions/cancel` | 현재 주기 종료 시 해지 |
| `POST /subscriptions/restore` | 구매 복원 (모바일) |
| `GET /subscriptions/purchases` | 구매 내역 |

**비즈니스 규칙**

- 체험판: 월간 요금제 최초 결제 시 7일 제공(사용자당 1회).
- 주기 말 해지 → `current_period_end`까지 이용 유지.
- Apple / Google 결제는 영수증으로 서버 검증, Stripe는 웹훅으로 검증 (명세 범위 외이나 소비자 API는 고정).

---

### 4.5 대시보드 (`dashboard`)

**화면:** 연속 학습일수 · 학습 트랙 2개 · 오늘의 목표 · 페이월 배너 · 하단 탭 네비게이션.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /dashboard/summary` | 홈 화면 종합 스냅샷 |
| `GET /dashboard/streak` | 연속 학습일수 상세 |

**비즈니스 규칙**

- `today_minutes_goal`(기본 10분)을 달성하면 `streak_days`가 증가.
- `freeze_tokens`(0 이상)는 하루를 빼먹어도 연속 학습일수를 보호.
- 다음 레슨이 구독 필요 콘텐츠일 때 `paywall_required=true`.

---

### 4.6 학습 카테고리 및 진행 트랙 (`learning`)

학습은 **두 개의 최상위 카테고리**로 나뉘고, 각 카테고리는 서로 독립적으로 진행되는 **두 개의 진행 트랙(progression)**을 가진다:

| 카테고리 | Track ID | 진행 트랙 |
|---|---|---|
| 회화(Conversation) | `trk_conversation` | 강의(lectures) · 문장 학습(sentences) |
| TOPIK | `trk_topik` | 강의(lectures) · 문장 학습(sentences) |

(사용자, 카테고리, 진행 트랙) 단위로 서버는 **`current_level`**을 관리한다. 사용자가 콘텐츠를 완료하면 자동으로 증가한다.

TOPIK은 카테고리 단위로 **`target_grade`**(목표 급수 1–6)를 추가로 가진다. 온보딩에서 수집되며 언제든 변경할 수 있다.

**기본값**

- **TOPIK:** 강의·문장 모두 `current_level = 1`로 시작. `target_grade`는 온보딩의 `topik_target`(1–6).
- **회화:** 강의·문장 모두 `current_level`을 온보딩의 `speaking_level`로 초기화.

사용자는 설정 화면에서 언제든 진행 트랙별 `current_level`과 TOPIK `target_grade`를 직접 변경할 수 있다(4.17 참조).

**화면:** 카테고리 / 진행 트랙 선택 · 레벨 목록(학습 레벨 1–N) · 캘린더 · 통계 차트 · 영상 플레이어 · 문장 목록.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /tracks` | 두 카테고리 목록 및 각 진행 트랙 메타데이터 |
| `GET /tracks/{track_id}` | 카테고리 상세 |
| `GET /tracks/{track_id}/progressions/{kind}/levels` | 진행 트랙의 레벨 목록. `kind` ∈ `lectures`, `sentences`. |
| `GET /me/learning` | 내 (카테고리, 진행)별 `current_level` 및 TOPIK `target_grade` |
| `PATCH /me/learning/{track_id}/{kind}` | 특정 진행 트랙의 `current_level` 변경 |
| `PATCH /me/learning/trk_topik` | TOPIK `target_grade`(1–6) 변경 |
| `GET /learning/calendar?from=&to=` | 일일 학습 캘린더 (카테고리 전체 집계) |
| `GET /learning/stats?range=week\|month\|year\|all` | 차트용 집계 통계 |
| `GET /lectures?track_id=&level=` | 특정 (카테고리, 레벨)의 강의 목록 — 강의 진행 트랙 기준 |
| `GET /lectures/{id}` | 강의 상세 |
| `GET /lectures/{id}/video` | 서명된 영상 URL (HLS, TTL ≤ 1시간) |
| `POST /lectures/{id}/progress` | 재생 하트비트 및 완료 신호 |

**비즈니스 규칙**

- 강의와 문장 학습은 **독립적으로 진행된다**. 강의를 완료해도 문장 학습의 `current_level`은 변하지 않으며, 그 반대도 성립한다.
- 각 진행 트랙 내에서 레벨은 순차적으로 해금된다(레벨 N 해금 조건은 N-1 레벨의 모든 학습 완료).
- 영상 URL은 서명되어 만료되므로, 클라이언트는 만료 시 재요청.
- `completed=true`일 때 (사용자, 강의)당 한 번만 XP 지급.

---

### 4.7 문장 학습 (`sentences`)

문장 학습은 각 카테고리에 속한 두 진행 트랙 중 하나다(4.6 참조). 학습 피드는 사용자의 활성 카테고리와 문장 진행 트랙의 `current_level`을 기준으로 제공되며, 강의 진행 트랙과는 독립적으로 진전된다.

**화면:** 오디오·북마크·문법 포인트 포함 문장 목록 · 북마크한 문장 · 최근 학습한 문장.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /sentences?track_id=&level=&topic=&cursor=` | 학습 피드 — 미지정 시 사용자의 활성 카테고리 및 문장 진행 `current_level` 기준 |
| `GET /sentences/bookmarks` | 북마크한 문장 |
| `GET /sentences/recently-studied` | 최근 학습 목록 |
| `GET /sentences/{id}` | 예문·설명 포함 문장 상세 |
| `POST /sentences/{id}/bookmark` | 북마크 추가 |
| `DELETE /sentences/{id}/bookmark` | 북마크 해제 |
| `POST /sentences/{id}/listen` | 오디오 재생 이벤트 기록 |
| `GET /sentences/{id}/audio` | 서명된 오디오 URL |

**비즈니스 규칙**

- 문장 `status`는 퀴즈·노출 신호에 따라 `new → learning → mastered`로 이동.
- 오디오 URL TTL은 15분 이하.

---

### 4.8 퀴즈 (`quizzes`)

**화면:** 객관식(덕분에 / 동안 / 처럼 / 만큼) · 한글 키보드 입력형 퀴즈 · 정답 축하 / 다시 풀기.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /quizzes?type=&level=` | 퀴즈 뱅크 |
| `GET /quizzes/daily` | 오늘의 퀴즈 세트 |
| `GET /quizzes/{id}` | 단일 문항 |
| `POST /quizzes/{id}/attempts` | 답안 제출 |
| `GET /quizzes/{id}/attempts/{attempt_id}` | 과거 풀이 상세 |
| `GET /quizzes/attempts/me` | 내 풀이 이력 |

**비즈니스 규칙**

- 풀이 XP: 정답 +10, 오답 0. 5문제 연속 정답 시 보너스 +5.
- 일일 세트는 (사용자, 날짜) 기준 결정적(deterministic)이며 재요청해도 동일.
- 해설은 `language` 쿼리 또는 프로필 기본 언어로 현지화.

---

### 4.9 작문 연습 (`writing`)

**화면:** 주제 목록 · 자유 작문 입력 · AI 채점 피드백.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /writing/prompts` | 작문 주제 목록 |
| `POST /writing/prompts/{id}/submissions` | 작문 제출 |
| `GET /writing/submissions/me` | 내 제출 이력 |
| `GET /writing/submissions/{id}` | 제출물 + AI 피드백 |

**비즈니스 규칙**

- 입력 글자 수는 1–2000자.
- 피드백 필드: `score 0–100`, 문법 이슈, 개선 제안, 교정된 문장. 비동기 채점으로 상태는 `pending → graded | failed`.

---

### 4.10 한글AI 대화 (`ai-chat`)

**화면:** "물어보기" 대화창 (말풍선 + 제안 칩).

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `POST /ai/conversations` | 새 대화 시작 |
| `GET /ai/conversations` | 대화 목록 |
| `GET /ai/conversations/{id}/messages` | 메시지 기록(페이지네이션) |
| `POST /ai/conversations/{id}/messages` | 사용자 메시지 전송 및 AI 응답 수신 |

**비즈니스 규칙**

- 콘텐츠 모더레이션: 요청과 응답 모두 필터링 후 반환.
- 무료 플랜: 하루 AI 메시지 10건 제한. 구독 사용자는 무제한(초과 시 429 `rate_limited`).
- 제안 칩은 모델이 제공하는 선택적 후속 발화.

---

### 4.11 게이미피케이션 — 포인트, 리그, 시즌 (`gamification`)

**화면:** 포인트 잔액 · 리그 티어 (Green → Lime → Yellow → Orange) · 2026 Spring Season 리더보드 · 과거 시즌.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /points/me` | 잔액 (누적 / 주간 / 시즌) |
| `GET /points/history` | 포인트 적립 이력 |
| `GET /leagues/me` | 현재 티어, 순위, 승급 기준 |
| `GET /leagues/current` | 진행 중인 시즌 메타데이터 |
| `GET /leagues/current/rankings` | 실시간 리더보드 |
| `GET /leagues/seasons` | 과거 시즌 목록 |
| `GET /leagues/seasons/{id}/rankings` | 종료된 시즌 리더보드 |

**비즈니스 규칙**

- 시즌은 약 3개월 주기(설정 가능).
- `season_points >= promotion_threshold`이면 승급, 시즌 종료 시 `demotion_threshold` 미만이면 강등.
- 리더보드는 최종 일관성(eventual consistency) 기준이며 최대 60초 지연 허용.

---

### 4.12 소셜 — 친구 및 피드 (`social`)

**화면:** 친구 코드로 추가 · 받은/보낸 요청 · 친구 목록 · 친구 활동 피드 · 반응.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /friends` | 내 친구 목록 |
| `POST /friends` | 친구 요청 전송(코드 또는 user_id) |
| `DELETE /friends/{user_id}` | 친구 삭제 |
| `GET /friends/requests` | 받은 / 보낸 요청 |
| `POST /friends/requests/{id}/accept` | 수락 |
| `POST /friends/requests/{id}/decline` | 거절 |
| `GET /feed` | 친구 활동 피드 |
| `POST /feed/{id}/reactions` | 이모지 반응 |

**비즈니스 규칙**

- 친구 최대 300명.
- 피드 아이템 타입: `level_up`, `streak`, `badge`, `league_promotion`, `friend_join`.
- 반응은 이모지 shortcode 사용, 사용자당 분당 30회 제한.

---

### 4.13 알림 (`notifications`)

**화면:** 알림 인박스 · 알림 상세 · 푸시 · 이메일 설정.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /notifications` | 알림 목록(페이지네이션) |
| `POST /notifications/{id}/read` | 개별 읽음 처리 |
| `POST /notifications/read-all` | 모두 읽음 처리 |
| `GET /notifications/settings` | 현재 알림 환경설정 |
| `PUT /notifications/settings` | 알림 환경설정 변경 |

**비즈니스 규칙**

- 카테고리: `learning_reminder`, `streak`, `friend`, `league`, `announcement`, `marketing`, `system`.
- 방해 금지 시간(quiet hours)은 기기 타임존 기준. 서버는 지연 발송 플래그를 설정.
- 푸시 토큰 등록은 별도 디바이스 등록 엔드포인트에서 처리(추후 추가 예정).

---

### 4.14 공지사항 (`announcements`)

**화면:** 공지 목록 · 상단 고정 배너 · 공지 상세.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /announcements` | 목록 |
| `GET /announcements/{id}` | 상세 |

**비즈니스 규칙**

- 카테고리: `notice`, `event`, `update`, `maintenance`.
- 상단 고정(pin) 항목은 항상 최상위 노출.

---

### 4.15 고객 지원 — FAQ & 1:1 문의 (`support`)

**화면:** FAQ 카테고리 · FAQ 상세 · 1:1 문의 작성 · 내 문의 내역.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /support/faqs?category=` | FAQ 브라우징 |
| `GET /support/faqs/{id}` | FAQ 상세 |
| `POST /support/inquiries` | 문의 접수 |
| `GET /support/inquiries/me` | 내 문의 목록 |
| `GET /support/inquiries/{id}` | 단건 문의 및 관리자 답변 |

**비즈니스 규칙**

- 문의 상태: `open → in_progress → answered | closed`.
- 첨부파일은 S3 pre-signed URL로 업로드.

---

### 4.16 법적 문서 (`legal`)

**화면:** 이용약관 · 개인정보 처리방침 · 마케팅 수신 동의.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /legal/terms?locale=` | 이용약관 |
| `GET /legal/privacy?locale=` | 개인정보 처리방침 |
| `GET /legal/marketing-consent?locale=` | 마케팅 수신 동의 문구 |

**비즈니스 규칙**

- 문서마다 `version`과 `effective_date`를 보유. 버전이 갱신되면 앱이 재동의를 요구.

---

### 4.17 앱 설정 (`settings`)

**화면:** 언어 · 테마 · 오디오 · 진동 · 로마자 표기 · 일일 목표 · 활성 카테고리 · 진행 트랙별 현재 레벨 · TOPIK 목표 급수.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /settings/me` | UI 환경설정 조회 |
| `PUT /settings/me` | UI 환경설정 변경 |
| `GET /me/learning` | 4.6 참조 — 진행 트랙별 `current_level` 및 TOPIK `target_grade` 조회 |
| `PATCH /me/learning/{track_id}/{kind}` | 4.6 참조 — 진행 트랙의 `current_level` 변경 |
| `PATCH /me/learning/trk_topik` | 4.6 참조 — TOPIK `target_grade` 변경 |

**비즈니스 규칙**

- 언어 변경은 `users.language`에 자동 반영.
- `daily_goal_minutes` 범위는 5–120분.
- 현재 레벨 변경은 `PATCH /me/learning/{track_id}/{kind}`, TOPIK 목표 급수 변경은 `PATCH /me/learning/trk_topik`로 위임된다.

---

### 4.18 추천 엔진 (내부용, `recommendations`)

기존에 존재하는 추천 엔진 모듈. 대시보드와 문장 피드에서 다음 학습 콘텐츠 선정에 사용된다.

---

## 5. 상태 머신 (요약)

### 5.1 문장 마스터리

```
new ──정답──▶ learning ──3회 연속 정답──▶ mastered
      ▲                                   │
      └──────────── 오답 ─────────────────┘
```

### 5.2 작문 제출

```
pending ──채점 성공──▶ graded
pending ──채점 실패──▶ failed
```

### 5.3 구독

```
none → trialing → active → past_due → canceled / expired
                           │
                           └── 주기 말 해지 예약 → canceled
```

### 5.4 친구 요청

```
pending ──수락──▶ accepted
pending ──거절──▶ declined
pending ──취소──▶ canceled
```

---

## 6. 도메인 용어집

| 용어 | 의미 |
|---|---|
| **Category (카테고리)** | 최상위 학습 분류: 회화(Conversation) 또는 TOPIK. |
| **Track (트랙)** | API 경로에서 Category와 동의어(`/tracks`, `trk_conversation`, `trk_topik`). |
| **Progression (진행 트랙)** | 카테고리 내에서 독립적으로 진전되는 레벨 시퀀스: `lectures` 또는 `sentences`. |
| **Level (레벨)** | 진행 트랙 내 순차 단위(학습 레벨 1–N). |
| **Lecture (강의)** | 강의 진행 트랙 안에 포함된 영상 / 읽기 / 듣기 단위. |
| **Sentence (문장)** | 오디오와 문법 태그를 갖춘 최소 학습 단위. |
| **Quiz (퀴즈)** | 객관식 / 빈칸 채우기 / 입력형 / 순서 맞추기 / 듣기. |
| **Attempt (풀이)** | 퀴즈에 제출된 단일 답안. |
| **Streak (연속 학습일수)** | 일일 목표를 달성한 연속 일수. |
| **Tier (티어)** | 리그 내 위치: Green → Lime → Yellow → Orange. |
| **Season (시즌)** | 분기 단위 주기로 종료 시 순위가 고정됨. |
| **한글AI (HangulAI)** | 온디맨드 AI 대화 파트너. |
