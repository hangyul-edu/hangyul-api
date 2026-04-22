# 기능 명세서 — 한귤 한국어 학습 플랫폼

- OpenAPI / Swagger UI: `GET /openapi.json`, `GET /docs`

---

## 1. 제품 개요

한귤(Hangyul)은 비원어민을 위한 모바일 한국어 학습 서비스다. 학습은 추천 콘텐츠의 종류로 구분되는 두 개의 트랙으로 구성된다:

- **회화(Conversation) 트랙** → **문장**을 추천해 학습·연습한다.
- **TOPIK 트랙** → 사용자가 풀 **문제**를 추천한다.

각 트랙은 **`current_level`** 하나만 보유하며, 이는 사용자가 원하는 추천 난이도를 의미한다. 목표 레벨 개념은 없다. 트랙별 기준을 충족하면 `current_level`이 **자동 승급**된다. 사용자는 자유 입력 프롬프트로도 추천을 요청할 수 있다(예: "식당에서 주문할 때 쓰는 문장 추천해줘"). 추천된 TOPIK 문제를 틀리면 AI 챗봇이 자동으로 호출되어 풀이·해설을 제공한다.

여기에 연속 학습일수(streak), 적응형 추천, 영상 강의, 퀴즈, AI 대화 파트너, 소셜 리그가 결합된다.

### 1.1 핵심 사용자 목표

| 목표 | 지원 기능 |
|---|---|
| 자신 있게 일상 한국어 말하기 | 회화 트랙 — 사용자의 현재 레벨에 맞춰 AI가 문장을 생성(필요 시 프롬프트로 주제 세분화, 예: "식당에서 주문할 때 쓰는 문장"), 한글AI 대화, 오디오 재생 |
| 내 수준에서 TOPIK 연습하고 오답에서 배우기 | TOPIK 트랙 — 사용자의 현재 레벨에 맞춰 AI가 문제를 생성(필요 시 프롬프트로 주제 세분화); 오답 시 AI 챗봇이 자동으로 해설 |
| 지금 내게 맞는 난이도로 학습 | 트랙별 기준 충족 시 자동 승급, 설정에서 언제든 `current_level`을 위·아래로 자유롭게 변경 가능(변경 시 진행도 초기화) |
| 친구와 함께 주간 페이스 유지 | 연속 학습일수, 일일 목표, 리마인더, 30명 주간 리그(US Eastern, 승급 / 유지 / 강등), 활동 피드 |
| 막혔을 때 스스로 해결 | FAQ, 1:1 문의, 앱 내 공지사항 |

---

## 2. 페르소나

| 페르소나 | 설명 | 핵심 플로우 |
|---|---|---|
| **입문자 Bea** | K-콘텐츠 팬으로 한국어를 처음 배움. | 온보딩(`purpose=conversation`, `speaking_level=beginner`) → 회화 레벨 1 문장 피드 → 연속 학습 + 오디오 |
| **수험생 Eun** | 직장 병행하며 TOPIK 3~4급 준비. | 온보딩(`purpose=topik`, `topik_target=4`) → 내 레벨의 TOPIK 문제 추천 → 오답마다 AI 챗봇 해설 확인 |
| **프롬프트 세분화자 Paul** | 상황별 목적이 뚜렷한 중급 학습자. | 학습 화면의 프롬프트 입력창으로 레벨 기반 피드를 세분화(예: "면접에서 쓸 문장", "피동 문법 문제") → 서버가 현재 레벨과 프롬프트로 `POST /recommendations/...` 재호출 → 마음에 드는 항목 북마크 |
| **바쁜 Ben** | 10분 출퇴근 시간에 짧고 오디오 중심 세션. | 대시보드 일일 목표 → 오디오 중심 문장 → 프리즈 토큰으로 연속 학습일수 보호 |
| **경쟁형 Chris** | 랭킹과 사회적 동기에 강하게 반응. | 주간 30명 그룹 리더보드(US Eastern) → 상위 20% 승급 → 친구 피드 반응 |

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

### 3.5 메타 엔드포인트

- `GET /health` — 인증 불필요. `{"status": "ok"}`를 반환하는 liveness probe. 로드 밸런서 및 모니터링 용도.
- `GET /openapi.json`과 `GET /docs`(Swagger UI)는 FastAPI가 제공하며 인증이 필요 없다.

### 3.6 비기능 요구사항

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

**화면:** 프로필 편집 · 닉네임 중복 확인 · 아바타 선택(사진 업로드 + 기본 캐릭터 갤러리) · 친구 검색.

**아바타 선택**

프로필 이미지는 두 가지 방법 중 하나로 등록한다:

1. **사진 업로드** — 휴대폰에서 촬영 또는 선택한 이미지를 멀티파트로 업로드.
2. **기본 캐릭터 선택** — 앱이 제공하는 캐릭터 카탈로그에서 하나를 선택해 `default_avatar_id`를 전송.

두 방식 모두 응답 스키마는 동일한 `AvatarResponse`이며, `source ∈ {"uploaded", "default"}`와 최종 `avatar_url`을 포함한다.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /users/me` | 내 프로필 스냅샷 |
| `PATCH /users/me` | 닉네임 / 언어 변경(avatar_url 직접 설정도 가능하나 아래 전용 엔드포인트를 권장) |
| `GET /users/avatars/defaults` | 기본 캐릭터 아바타 카탈로그 조회 |
| `POST /users/me/avatar` | 휴대폰 사진을 멀티파트로 업로드 |
| `POST /users/me/avatar/default` | `default_avatar_id`로 기본 캐릭터 선택 |
| `POST /users/check-nickname` | 닉네임 중복 확인 |
| `GET /users/search?code=&nickname=` | 친구 코드 또는 닉네임으로 사용자 검색 |
| `GET /users/{user_id}/profile` | 공개 학습 프로필 |
| `POST /users/feedback` | 추천 결과 피드백 신호 |

**비즈니스 규칙**

- 닉네임은 대소문자 구분 없이 유일해야 한다.
- `friend_code`는 사용자당 고유한 6–8자 코드로, 친구 추가에 사용.
- 사진 업로드는 JPEG / PNG / WebP / HEIC 최대 5 MB를 허용하며, `file`이 없으면 `422 validation_error` 반환.
- `POST /users/me/avatar/default`는 알 수 없는 `default_avatar_id`에 대해 `404 not_found`를 반환.
- 두 아바타 설정 엔드포인트는 모두 `AvatarResponse`를 반환하며, 서버는 `avatar_url`과 함께 `source`(및 `default_avatar_id`)를 저장해 추후 카탈로그 갱신 시 최신 이미지를 다시 해석할 수 있게 한다.

---

### 4.3 온보딩 (`onboarding`)

**화면 순서:**
1. 학습 목적 (회화 / TOPIK).
2. 회화 수준 (5단계 — 아래 참조).
3. 일일 목표 — 목적이 회화이면 **하루 학습 문장 수**, TOPIK이면 **하루 풀이 문제 수**. 옵션: `5 / 10 / 20 / 30 / 40`.
4. 목표 TOPIK 급수 (목적이 TOPIK일 때만 표시).
5. 푸시 알림 동의.

5단계 회화 수준 옵션(`SpeakingLevel` 코드, 표시 순):

| 코드 | 설명 |
|---|---|
| `beginner` | 완전 초보 — 아직 한국어를 거의 모름 |
| `elementary` | 단어 몇 개 정도 아는 수준 |
| `intermediate` | 간단한 문장을 말할 수 있음 |
| `advanced` | 일상 대화는 할 수 있음 |
| `fluent` | 유창함 |

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /onboarding/questions` | 온보딩 캐러셀용 질문 세트 |
| `POST /onboarding/responses` | 응답 저장 → 추천 트랙·레벨 반환 |
| `GET /onboarding/status` | 온보딩 완료 여부 확인 |

**비즈니스 규칙**

- `purpose`가 주 트랙을 결정한다.
  - `conversation`: `speaking_level` 응답이 회화 트랙의 초기 `current_level`을 설정한다.
  - `topik`: `topik_target` 응답이 TOPIK 트랙의 초기 `current_level`(1..6, 급수 기준)을 설정한다.
- 두 트랙 모두 모든 사용자에게 존재하며, `purpose`는 기본으로 열리는 트랙을 결정할 뿐이다. 레벨은 설정 화면에서 직접 변경할 수 있고, 시간이 지나면서 자동 승급된다(4.6 참조).
- 온보딩에서 묻는 일일 목표는 `purpose`에 따라 하나만 채운다 — 회화이면 `daily_sentence_goal`, TOPIK이면 `daily_question_goal`. 선택하지 않은 반대 쪽 목표는 10으로 시작하고 이후 설정(§4.17)에서 조정한다. 허용 값은 `5 / 10 / 20 / 30 / 40`이며, 그 외 값은 `422 validation_error`.

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

- `streak_days`는 사용자가 일일 목표 중 하나(`daily_sentence_goal` 또는 `daily_question_goal`)라도 달성한 날마다 증가한다.
- `freeze_tokens`(0 이상)는 하루를 빼먹어도 연속 학습일수를 보호.
- 다음 레슨이 구독 필요 콘텐츠일 때 `paywall_required=true`.
- `goals[]`는 설정(§4.17)에서 지정한 항목 개수 목표 두 개의 진행도를 담는다: `daily_sentences`(`track_id=trk_conversation`), `daily_questions`(`track_id=trk_topik`). 각 항목은 `current`, `target`(5/10/20/30/40 중 하나), `achieved`를 포함하며, 클라이언트는 이를 바탕으로 링/프로그레스바와 마일스톤 달성 표시를 그린다. 카운터는 사용자의 로컬 일자 경계에서 초기화된다.
- `today_minutes`는 표시 전용이다 — 학습 시간은 **목표 대상이 아니다**.

---

### 4.6 학습 트랙 (`learning`)

두 트랙은 추천하는 콘텐츠의 종류로 구분된다:

| 트랙 | Track ID | 추천 콘텐츠 | 레벨 범위 |
|---|---|---|---|
| 회화(Conversation) | `trk_conversation` | 학습·연습용 문장 | 1..10 |
| TOPIK | `trk_topik` | 풀이용 문제 | 1..6 (급수) |

각 트랙은 사용자당 **`current_level`** 하나를 저장하며, 이는 사용자가 원하는 추천 난이도다. 목표 레벨 개념은 없다.

**자동 승급**

- 트랙별 기준을 충족하면 `current_level`이 자동으로 증가한다. 기준은 서버에서 설정하며 트랙마다 다를 수 있다(예: 해당 레벨에서 연속 학습일수 달성, 완료한 문장 수 임계치, 최근 정답률 등).
- 승급 발생 시 서버는 `LevelUpEvent`를 생성한다(대시보드 / 알림에 노출).

**수동 변경**

설정 화면에서 `current_level`을 직접 변경할 수도 있다(4.17 참조) — 초보 이상에서 시작하거나, 복습을 위해 한 단계 내려갈 때 유용하다.

**기본값**

- **회화:** 온보딩의 `speaking_level`로 초기화.
- **TOPIK:** 온보딩의 `topik_target`(1..6 = 급수)으로 초기화.

**화면:** 트랙 선택 · 레벨 배지 · 자동 승급 축하 화면 · 캘린더 · 통계 차트 · 영상 플레이어 · 문장 목록 · TOPIK 문제 목록.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /tracks` | 두 트랙 목록 및 메타데이터 |
| `GET /tracks/{track_id}` | 트랙 상세 |
| `GET /tracks/{track_id}/levels` | 트랙이 제공하는 레벨 목록(1..N)과 라벨 |
| `GET /me/learning` | 내 트랙별 `current_level` |
| `PATCH /me/learning/{track_id}` | 트랙의 `current_level`을 수동으로 변경 |
| `GET /me/learning/events?type=level_up&cursor=` | 자동 승급 이력 |
| `GET /learning/calendar?from=&to=` | 일일 학습 캘린더 |
| `GET /learning/stats?range=week\|month\|year\|all` | 차트용 집계 통계 |
| `GET /lectures?track_id=&level=` | 특정 (트랙, 레벨)의 강의 목록 — 주로 TOPIK 보조 콘텐츠 |
| `GET /lectures/{lecture_id}` | 강의 상세 |
| `GET /lectures/{lecture_id}/video` | 서명된 영상 URL (HLS, TTL ≤ 1시간) |
| `POST /lectures/{lecture_id}/progress` | 재생 하트비트 및 완료 신호 |

**비즈니스 규칙**

- 회화 레벨과 TOPIK 레벨은 독립적이다. 한쪽이 올라가도 다른 쪽에는 영향이 없다.
- 자동 승급은 기준 기반이며 학습 이벤트(퀴즈 풀이, 문장 완료 등)에서 평가된다. 자동 강등은 없다.
- 사용자는 `current_level`을 **자유롭게 위·아래로** 변경할 수 있으며, 이미 지나온 레벨로 되돌아가는 것도 가능하다(예: `1 → 2 → 3 → 2`). 이때 **해당 트랙의 진행 중인 승급 진행도는 초기화된다** — 새 레벨에서 다시 승급 평가를 받으려면 필요한 학습량을 처음부터 누적해야 한다.
- 강의는 보조 콘텐츠이며 자동 승급에는 영향을 주지 않는다.

---

### 4.7 문장 학습 (`sentences`)

문장은 회화 트랙의 추천 콘텐츠 타입이며, 모든 추천은 **사용자의 회화 `current_level` 기준으로 AI가 생성**한다(4.18 참조). 북마크, 오디오 재생, 복습 완료 등의 이벤트는 회화 자동 승급 기준으로 사용된다.

**모든 추천 문장은 해당 문장의 AI 생성 발음 오디오를 함께 포함한다.** 응답 페이로드에 중첩 `audio` 객체(서명된 CDN URL + 포맷 + 길이 + voice + `expires_at`)가 들어 있다. 클라이언트는 파일을 로컬에 캐시하고, 앱 내 재생(replay) 버튼은 캐시된 파일을 재생하므로 추가 API 호출이 없다.

**모든 추천 문장에는 사용자의 기본 언어로 번역된 의미도 함께 포함된다.** 각 `Sentence`는 `translation`(번역문)과 `translation_language`(BCP-47, `users.language`와 일치 — 예: `en`, `ja`, `zh-CN`)를 가진다. 사용자가 `users.language`를 변경하면 이후의 추천은 새 언어로 재생성된다.

**읽기 플로우**

1. 문장이 도착하면 클라이언트가 `audio`를 한 번 자동 재생한다.
2. (선택) 사용자가 재생 버튼을 누르면 캐시된 파일을 다시 재생한다.
3. 사용자가 마이크 버튼을 누르고 화면의 문장(빈칸 포함)을 소리 내어 읽으면, 클라이언트가 녹음한 오디오를 `POST /sentences/{sentence_id}/speech-attempts`로 업로드한다.
4. 서버가 ASR + 발음 평가를 기준 `korean` 텍스트와 비교해 다음을 반환한다:
   - `correct: bool`
   - `transcription: str` — 사용자가 실제로 발화한 내용
   - `pronunciation_score: int` (0–100)
   - `feedback_code: "correct" | "missed_words" | "bad_pronunciation" | "unclear_audio"`
5. 클라이언트 UI:
   - `correct=true` → 파란색 "정답" 메시지
   - `correct=false` → 빨간색 "다시 생각해보고 한 번 더 시도해보세요" 메시지

**빈칸**

빈칸 채우기 문제인 경우 `display_text`에는 빈칸 형태(예: `덕분에 잘 ___ 있어요`)가 들어가고, `korean`에는 TTS · 평가용 완성 문장이 들어간다. `blanks[]`에는 예상 정답이 담긴다.

문장 화면에는 **서로 다른 두 개의 UI**가 배치된다:

1. **프롬프트 입력창(추천 세분화용)** — 콘텐츠 카드 근처의 입력 필드 + 전송 버튼. 예: "면접에서 쓸 문장 추천"을 입력하고 전송하면 클라이언트가 현재 레벨과 프롬프트로 `POST /recommendations/sentences`를 재호출하고, 응답이 기존 피드를 교체한다.
2. **챗봇 아이콘(컨텍스트 대화용)** — 우측 상단의 별도 아이콘. 탭 시 `POST /ai/conversations`에 `context.kind="sentence"`, `sentence_id=...`를 실어 호출하며, 사전 CTA 칩에서 진입한 경우에는 `auto_assistant_reply=true`도 함께 보낸다(4.10 참조).

**화면:** 오디오·북마크·문법 포인트 포함 문장 목록 · 북마크한 문장 · 최근 학습한 문장.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /sentences?level=&topic=&cursor=` | 학습 피드 — 미지정 시 사용자의 회화 `current_level` 기준 |
| `GET /sentences/bookmarks` | 북마크한 문장 |
| `GET /sentences/recently-studied` | 최근 학습 목록 |
| `GET /sentences/{sentence_id}` | 예문·설명 포함 문장 상세 |
| `POST /sentences/{sentence_id}/bookmark` | 북마크 추가 |
| `DELETE /sentences/{sentence_id}/bookmark` | 북마크 해제 |
| `POST /sentences/{sentence_id}/listen` | 오디오 재생 이벤트 기록(분석 + 자동 승급 신호) |
| `GET /sentences/{sentence_id}/audio` | 서명된 오디오 URL 재발급(`expires_at` 이후용, 일반 재생은 캐시 사용) |
| `POST /sentences/{sentence_id}/speech-attempts` | 사용자의 읽기 녹음을 멀티파트 업로드 → 정오 판정·ASR 전사·발음 점수 반환 |

**비즈니스 규칙**

- 문장 `status`는 읽기 시도·노출 신호에 따라 `new → learning → mastered`로 이동.
- 추천 문장에는 항상 `audio`(AI TTS)가 포함된다. 서명 URL TTL은 15분 이하이며, 클라이언트는 첫 수신 시 파일을 로컬에 캐시하고 재생 버튼은 캐시된 파일을 재사용한다. `expires_at` 이후에는 `GET /sentences/{sentence_id}/audio`로 새 URL을 재발급받는다.
- `POST /sentences/{sentence_id}/speech-attempts`는 최대 2 MB, 15초 이하의 오디오만 허용한다. `audio` 파일이 없으면 `422 validation_error`를 반환한다. 모든 시도는 `attempt_id`로 기록되어 분석 / 자동 승급에 사용된다.
- 클라이언트 UI는 `correct=true`일 때 파란 정답 메시지를, 그 외에는 빨간 "다시 생각해보고 재시도" 메시지와 재시도 버튼을 렌더링한다.

---

### 4.8 퀴즈 (`quizzes`)

퀴즈는 TOPIK 트랙의 추천 콘텐츠 타입이다. 모든 문제는 **사용자의 TOPIK `current_level` 기준으로 AI가 생성**한다(4.18 참조). 문제 카드 옆의 프롬프트 입력창을 통해 생성 요청을 세분화할 수 있으며(예: "피동 문법 문제"), 전송 시 클라이언트가 현재 레벨과 프롬프트로 `POST /recommendations/questions`를 재호출한다. **오답을 제출해도** 서버가 대화를 미리 만들지는 않는다. 대신 챗봇 아이콘에 해설 제안 CTA가 노출되고, 사용자가 CTA를 눌렀을 때에만 클라이언트가 풀이 정보를 컨텍스트로 삼아 AI 챗 대화를 시작하고 해설을 받는다(4.10 참조).

**화면:** 객관식(덕분에 / 동안 / 처럼 / 만큼) · 한글 키보드 입력형 퀴즈 · 정답 축하 / 다시 풀기 · "AI가 오답을 해설" 진입.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /quizzes?type=&level=` | 퀴즈 뱅크 |
| `GET /quizzes/daily` | 오늘의 퀴즈 세트 |
| `GET /quizzes/{quiz_id}` | 단일 문항 |
| `POST /quizzes/{quiz_id}/attempts` | 답안 제출 |
| `GET /quizzes/{quiz_id}/attempts/{attempt_id}` | 과거 풀이 상세 |
| `GET /quizzes/attempts/me` | 내 풀이 이력 |

**비즈니스 규칙**

- 풀이 XP: 정답 +10, 오답 0. 5문제 연속 정답 시 보너스 +5.
- 일일 세트는 (사용자, 날짜) 기준 결정적(deterministic)이며 재요청해도 동일.
- 해설은 `language` 쿼리 또는 프로필 기본 언어로 현지화.
- 추천 TOPIK 문제를 틀려도 풀이 응답에는 사전 생성된 대화가 포함되지 않는다. 클라이언트는 챗봇 아이콘에 "왜 틀렸는지, 어떤 부분이 헷갈리셨는지 설명해드릴까요?" 같은 CTA를 노출한다. **사용자가 CTA를 눌렀을 때에만** 클라이언트가 `POST /ai/conversations`에 `context.kind="quiz_attempt"`, `attempt_id=…`, `reason="explain_mistake"`, `auto_assistant_reply=true`를 담아 호출하고, 서버는 그 시점에 첫 assistant 메시지로 해설을 생성해 돌려준다. 클라이언트는 사용자를 바로 그 대화 화면으로 이동시킨다.
- TOPIK 정답 풀이는 학습 모듈의 TOPIK 자동 승급 기준으로 사용된다.

---

### 4.9 작문 연습 (`writing`)

**화면:** 주제 목록 · 자유 작문 입력 · AI 채점 피드백.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /writing/prompts` | 작문 주제 목록 |
| `POST /writing/prompts/{prompt_id}/submissions` | 작문 제출 |
| `GET /writing/submissions/me` | 내 제출 이력 |
| `GET /writing/submissions/{submission_id}` | 제출물 + AI 피드백 |

**비즈니스 규칙**

- 입력 글자 수는 1–2000자.
- 피드백 필드: `score 0–100`, 문법 이슈, 개선 제안, 교정된 문장. 비동기 채점으로 상태는 `pending → graded | failed`.

---

### 4.10 한글AI 대화 (`ai-chat`)

**화면:** "물어보기" 대화창(말풍선 + 제안 칩) · 모든 학습 화면 우측 상단 챗봇 아이콘 · TOPIK 오답에서 진입하는 "AI 오답 해설" 대화(4.8 참조).

> **학습 화면의 추천 프롬프트 입력창과는 별개다.** 학습 화면에는 추천 피드를 갱신하는 프롬프트 입력창이 따로 존재한다(4.7, 4.8, 4.18 참조). 우측 상단 챗봇 아이콘은 본 모듈(콘텐츠에 대한 대화형 Q&A)을 연다. 두 UI는 동시에 노출될 수 있으며 서로 독립적이다.

**컨텍스트 기반 대화 시작**

모든 학습 화면 — 문장 상세(4.7), 퀴즈 문제(4.8), 강의 플레이어(4.6) — 우측 상단에 챗봇 아이콘이 노출된다. 사용자가 아이콘을 누르면 클라이언트가 **구조화된 컨텍스트와 함께** 대화를 시작하므로, AI는 사용자가 보고 있는 항목을 이미 알고 있고 사용자는 아무것도 다시 입력할 필요가 없다.

컨텍스트 객체:

```json
{
  "kind": "sentence" | "quiz" | "quiz_attempt" | "lecture",
  "sentence_id": "sen_…",
  "quiz_id":     "quz_…",
  "attempt_id":  "att_…",
  "lecture_id":  "lec_…",
  "reason": "explain_mistake" | "explain_item" | "grammar_help" | "vocabulary_help" | "custom"
}
```

`kind`에 해당하는 필드만 채워서 전달한다.

**입력 없이 AI가 먼저 답하는 모드**

`POST /ai/conversations`는 `auto_assistant_reply: true`를 받는다. 이 값이 참이면 서버가 `context`만으로 첫 assistant 메시지를 생성해 `first_assistant_message` 필드로 함께 반환한다. 다음과 같은 UI CTA를 지원한다:

- TOPIK 오답 → 챗봇 아이콘에 "왜 틀렸는지, 어떤 부분이 헷갈리셨는지 설명해드릴까요?" CTA 노출 → 탭 → `context.kind="quiz_attempt"` + `reason="explain_mistake"` + `auto_assistant_reply=true`로 대화가 생성되고, 첫 assistant 메시지(해설)가 즉시 보인다.
- 문장 학습 → "반말과 존댓말로 바꾸면 어떻게 달라지나요?" → 탭 → `context.kind="sentence"` + `auto_assistant_reply=true`로 대화가 생성되고, 첫 assistant 메시지가 이미 준비되어 있다.

모든 플로우는 서버가 사전 대화 생성을 **하지 않는다**는 원칙을 공유한다. 대화는 사용자 액션(챗봇 아이콘 또는 CTA 칩 탭) 시 생성되며, `auto_assistant_reply=true`가 서버로 하여금 같은 응답에 바로 보여줄 assistant 메시지를 포함하도록 한다.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `POST /ai/conversations` | 새 대화 시작 |
| `GET /ai/conversations` | 대화 목록 |
| `GET /ai/conversations/{conversation_id}/messages` | 메시지 기록(페이지네이션) |
| `POST /ai/conversations/{conversation_id}/messages` | 사용자 메시지 전송 및 AI 응답 수신 |

**비즈니스 규칙**

- 콘텐츠 모더레이션: 요청과 응답 모두 필터링 후 반환.
- 무료 플랜: 하루 AI 메시지 10건 제한. 구독 사용자는 무제한(초과 시 429 `rate_limited`).
- 제안 칩은 모델이 제공하는 선택적 후속 발화.
- TOPIK 오답으로부터 생성된 해설 대화는 서버가 (문제, 사용자의 답, 정답, 해설 요청)으로 사전 시드하며, 첫 번째 assistant 응답이 해설이다.

---

### 4.11 게이미피케이션 — 포인트, 리그, 시즌 (`gamification`)

**화면:** 포인트 잔액 · 포인트 적립 이력 · 내 그룹 리더보드(30명) · 내 리그 티어 · 과거 시즌 · 시즌 종료 결과 배너(승급 / 유지 / 강등).

**티어**

5개 티어가 순서대로 구성된다: **Green → Lime → Yellow → Orange → Golden**. 각 티어는 활동량이 비슷한 유저끼리 **30명 단위 그룹**으로 자동 분할된다(예: 300명이 있는 티어는 10개 그룹). 순위는 **그룹 단위**로 산정된다.

| 티어 | 그룹 인원 | 승급 | 강등 |
|---|---|---|---|
| Green | 30 | ✓ | ✗ (최하위) |
| Lime | 30 | ✓ | ✓ |
| Yellow | 30 | ✓ | ✓ |
| Orange | 30 | ✓ | ✓ |
| Golden | 30 | ✗ (최상위) | ✓ |

**시즌**

- 시즌은 **미국 동부 표준시(US Eastern Time, America/New_York — 워싱턴 D.C. 기준)**의 **1주일** 단위 — 월요일 00:00 ET ~ 일요일 21:00 ET. 일광절약시간(EST/EDT) 전환은 자동으로 따른다.
- `season_id`는 America/New_York 기준으로 계산한 ISO 주차 라벨을 사용(예: `2026-W17`).
- 시즌 종료 시 순서: (1) 최종 순위 확정, (2) 승급 / 유지 / 강등 처리, (3) 새 시즌 시작 시 포인트 0으로 초기화.
- 클라이언트는 기기 타임존에 맞춰 시즌 기간을 현지화해 표시할 수 있으나, 서버의 모든 판정(시즌 경계, 스케줄 작업, 동점 기준 시각)은 America/New_York을 기준으로 한다.

**승급 / 강등 구간 (30명 그룹 기준)**

- **상위 20 %** — 1~6위 → 승급
- **중간 60 %** — 7~24위 → 유지
- **하위 20 %** — 25~30위 → 강등
- Green은 강등 없음, Golden은 승급 없음.

**포인트 적립**

| 활동 | 포인트 |
|---|---|
| 일일 출석 | 5 |
| 연속 출석 7일 보너스 | +10 |
| 문장 완료 | 문장당 10 (예: 5문장 코스 → 50, 20문장 코스 → 200) |
| 강의 완료 | 100 |
| 저장 문장 복습 완료 | 5 |

- 점수는 주간 단위로 누적되며 시즌 시작 시 초기화된다.
- 동점 시 최근 활동 시간이 앞선 사용자가 상위(`last_activity_at` 기준).

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /points/me` | 잔액 (누적 / 주간 / 시즌) |
| `GET /points/history` | 포인트 적립 이력 |
| `GET /leagues/me` | 현재 티어, 그룹, 순위, 승급·강등 기준 |
| `GET /leagues/current` | 진행 중인 주간 시즌 메타데이터 |
| `GET /leagues/current/rankings` | 내 현재 그룹의 실시간 리더보드 |
| `GET /leagues/current/groups/{group_id}/rankings` | 특정 그룹(예: 친구의 그룹) 리더보드 |
| `GET /leagues/seasons` | 과거 시즌 목록 |
| `GET /leagues/seasons/{season_id}/rankings` | 해당 시즌의 내 그룹 최종 순위 |

**비즈니스 규칙**

- 순위는 실시간으로 갱신된다(수 초 단위 지연은 허용).
- 시즌이 종료되면 `RankingEntry.outcome`이 위 구간 기준으로 `promote` / `maintain` / `demote` 중 하나로 설정된다.
- 그룹 배정은 시즌 내에서 고정되며, 시즌 시작 시점에 재계산된다.

---

### 4.12 소셜 — 친구 및 피드 (`social`)

**화면:** 친구 코드로 추가 · 받은/보낸 요청 · 친구 목록 · 친구 활동 피드 · 반응.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /friends` | 내 친구 목록 |
| `POST /friends` | 친구 요청 전송(코드 또는 user_id) |
| `DELETE /friends/{friend_user_id}` | 친구 삭제 |
| `GET /friends/requests` | 받은 / 보낸 요청 |
| `POST /friends/requests/{request_id}/accept` | 수락 |
| `POST /friends/requests/{request_id}/decline` | 거절 |
| `GET /feed` | 친구 활동 피드 |
| `POST /feed/{feed_id}/reactions` | 이모지 반응 |

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
| `POST /notifications/{notification_id}/read` | 개별 읽음 처리 |
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
| `GET /announcements/{announcement_id}` | 상세 |

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
| `GET /support/faqs/{faq_id}` | FAQ 상세 |
| `POST /support/inquiries` | 문의 접수 |
| `GET /support/inquiries/me` | 내 문의 목록 |
| `GET /support/inquiries/{inquiry_id}` | 단건 문의 및 관리자 답변 |

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

**화면:** 언어 · 테마 · 오디오 · 진동 · 로마자 표기 · 일일 목표(회화 문장 수 + TOPIK 문제 수) · 활성 트랙 · 트랙별 현재 레벨.

**일일 목표**

`AppSettings`에는 항목 개수 단위의 일일 목표 두 개가 있다. 각각 **5 / 10 / 20 / 30 / 40** 중 하나를 선택하며, 기본값은 10이다. 사용자가 목표 이상으로 학습하는 것은 언제나 가능하고 실제 수행량은 그대로 기록되지만, 목표 **달성 여부**는 이 마일스톤 기준으로만 판정한다.

| 필드 | 범위 | 허용 값 | 기본값 |
|---|---|---|---|
| `daily_sentence_goal` | 회화 트랙 — 오늘 학습한 문장 수 | `5 \| 10 \| 20 \| 30 \| 40` | 10 |
| `daily_question_goal` | TOPIK 트랙 — 오늘 풀이한 문제 수 | `5 \| 10 \| 20 \| 30 \| 40` | 10 |

학습 시간은 **목표 대상이 아니다**. 대시보드의 `today_minutes`는 단순 표시용이다(4.5 참조).

사용자는 `GET /dashboard/summary`에서 진행도를 확인한다. `goals[]`는 `current`, `target`, `achieved`, 해당 `track_id`를 포함한다.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `GET /settings/me` | UI 환경설정과 일일 목표 조회 |
| `PUT /settings/me` | UI 환경설정 또는 일일 목표 변경 |
| `GET /me/learning` | 4.6 참조 — 트랙별 `current_level` 조회 |
| `PATCH /me/learning/{track_id}` | 4.6 참조 — 트랙의 `current_level` 변경 |

**비즈니스 규칙**

- 언어 변경은 `users.language`에 자동 반영.
- `daily_sentence_goal`, `daily_question_goal`은 `5 / 10 / 20 / 30 / 40` 중 하나여야 한다. 그 외 값은 `422 validation_error`.
- `achieved=true`는 `current >= target`일 때 래치되며, 이후 같은 날에 재조회해도 다시 false로 돌아가지 않는다.
- 레벨 수동 변경은 `PATCH /me/learning/{track_id}`로 위임된다. 사용자는 자유롭게 위·아래로 변경할 수 있으며, 변경 시 **해당 트랙의 진행 중인 승급 진행도가 초기화**되어 자동 승급이 새 레벨에서 처음부터 재평가된다(4.6 참조).

---

### 4.18 추천 엔진 (`recommendations`)

트랙 콘텐츠의 주된 진입 지점이다. **문장과 TOPIK 문제 모두 AI가 요청 시점에 생성**하며, 정적 카탈로그에서 꺼내오지 않는다. 모든 추천은 항상 **사용자의 `current_level`을 기반**으로 하며, 별도의 "프롬프트 기반 모드"는 존재하지 않는다. 클라이언트는 해당 레벨 안에서 주제·상황·문법 포커스를 **세분화**할 자유 입력 `prompt`를 선택적으로 덧붙일 수 있다.

**학습 화면의 프롬프트 입력창**

학습 화면의 콘텐츠 카드 옆에는 전송 버튼이 달린 프롬프트 입력창이 존재한다(우측 상단의 챗봇 아이콘과는 시각적·기능적으로 구분 — 챗봇 아이콘은 AI 대화를 연다, 4.10 참조). 사용자가 요청을 입력하고(예: "식당에서 쓸 문장 추천해줘") 전송하면 클라이언트가 사용자의 `current_level`과 입력 `prompt`를 함께 실어 `POST /recommendations/sentences`(회화) 또는 `POST /recommendations/questions`(TOPIK)를 재호출하며, 응답이 기존 피드를 교체한다.

프롬프트를 비운 채 전송하면 서버가 추가 조건 없이 `current_level` 기준으로 다시 생성한다.

**엔드포인트**

| 메서드 & 경로 | 용도 |
|---|---|
| `POST /recommendations/sentences` | 회화 트랙 추천 — 문장 반환 (body: `{level?, prompt?, count?}`) |
| `POST /recommendations/questions` | TOPIK 트랙 추천 — 퀴즈 문제 반환 (body: `{level?, prompt?, count?}`) |
| `GET /recommendations/history?kind=sentences\|questions&cursor=` | 최근 추천된 항목 (재요청·유사 항목 조회용) |
| `POST /recommendations` | 초기 프로젝트 셋업과의 하위 호환을 위해 남겨둔 레거시 내부 추천 엔드포인트. 새 클라이언트는 위 sentences / questions 엔드포인트를 사용해야 한다. |

**비즈니스 규칙**

- `level`은 항상 적용된다. 생략 시 서버가 해당 트랙의 `current_level`을 대입한다. 사용자의 현재 레벨과 다른 값을 의도적으로 보내는 경우는 다른 난이도를 미리보기할 때로 한정한다.
- `prompt`는 선택적 세분화 입력이다. 제공되면 AI가 해당 조건을 만족하는 항목을 생성하되 **항상 `level`을 유지**하며, 생략 시 최근 활동을 신호로 삼아 레벨에 맞는 항목을 생성한다.
- `prompt`는 최대 500자, LLM 전송 전에 모더레이션을 거친다.
- `count` 기본값 5, 최대 20.
- `/recommendations/questions` 결과 항목은 §4.8의 `QuizQuestion`과 동일 구조를 사용하며, 풀이는 퀴즈 풀이 엔드포인트로 제출한다.
- `/recommendations/sentences` 결과 항목은 §4.7의 `Sentence`와 동일 구조를 사용하며 다음을 항상 포함한다:
  - 중첩 `audio` 객체(AI TTS — 서명 URL + 포맷 + 길이 + `expires_at`). 클라이언트는 파일을 로컬에 캐시해 재생 버튼에서 재사용하며, 만료된 경우에만 `GET /sentences/{sentence_id}/audio`를 호출한다.
  - 사용자의 `users.language`로 번역된 `translation` + `translation_language`. 덕분에 UI는 한국어 문장과 번역을 추가 API 없이 같이 보여줄 수 있다.
- 북마크·재생·읽기 시도 이벤트는 문장 엔드포인트로 전송된다.

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

### 5.5 트랙 레벨 자동 승급

```
current_level N ──트랙 기준 충족──▶         current_level N+1   (LevelUpEvent 발생)
current_level N ──설정에서 수동 변경──▶     current_level M     (1..max 중 임의; level_progress 초기화)
```

수동 변경은 위·아래 모두 가능하다. 자동 강등은 없지만, **수동 변경 시 방향과 무관하게** 해당 트랙의 승급 진행도가 0으로 초기화된다(`level_progress_ratio` = 0).

---

## 6. 도메인 용어집

| 용어 | 의미 |
|---|---|
| **Track (트랙)** | 최상위 학습 분류: 회화(Conversation) 또는 TOPIK. 각 트랙마다 `current_level`을 보유한다. |
| **Current level (현재 레벨)** | 트랙 추천의 난이도. 트랙별 기준 충족 시 자동 승급되고, 설정에서 수동 변경도 가능하다. |
| **Level auto-promotion (자동 승급)** | 서버가 트랙별 기준을 평가해 `current_level`을 1단계 올리는 이벤트. |
| **Recommendation (추천)** | AI가 생성한 콘텐츠 — 회화는 문장, TOPIK은 문제. 항상 사용자의 `current_level`을 기반으로 하며, 선택적 `prompt`로 해당 레벨 안에서 요청을 세분화한다. |
| **Lecture (강의)** | 주로 TOPIK의 보조 영상 / 읽기 / 듣기 콘텐츠. 자동 승급에는 영향을 주지 않는다. |
| **Sentence (문장)** | 오디오와 문법 태그를 갖춘 최소 학습 단위. |
| **Quiz (퀴즈)** | 객관식 / 빈칸 채우기 / 입력형 / 순서 맞추기 / 듣기. |
| **Attempt (풀이)** | 퀴즈에 제출된 단일 답안. |
| **Streak (연속 학습일수)** | 일일 목표를 달성한 연속 일수. |
| **Tier (티어)** | 리그 내 위치: Green → Lime → Yellow → Orange → Golden. |
| **Group (그룹)** | 티어 내에서 활동량 기준으로 30명씩 묶인 단위. 순위는 그룹 단위로 산정. |
| **Season (시즌)** | 미국 동부 표준시(US Eastern) 기준 주간 주기(월 00:00 ET → 일 21:00 ET). 종료 시 승급 / 유지 / 강등 처리 후 포인트 초기화. |
| **한글AI (HangulAI)** | 온디맨드 AI 대화 파트너. |
