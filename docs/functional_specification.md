# Functional Specification — Hangyul Korean Learning Platform

- OpenAPI / Swagger UI: `GET /openapi.json`, `GET /docs`

---

## 1. Product Overview

Hangyul is a mobile Korean-language learning service for non-native speakers. Learning is split into two categories — **Conversation** (회화) and **TOPIK** — and each category holds two independent progressions, **lectures** and **sentence study**, each with its own current level. TOPIK additionally carries a target 급수 (1–6). The service combines streak-driven daily sessions, adaptive sentence recommendations, video lectures, quizzes, an AI conversation partner, and a social league.

### 1.1 Primary user goals

| Goal | Supporting features |
|---|---|
| Learn enough Korean for everyday conversation | Sentence study, HangulAI chat, listening/speaking lessons |
| Pass a target TOPIK grade | TOPIK track, level-gated lessons, mock quizzes |
| Build a daily habit | Streaks, goals, reminders, push notifications |
| Stay motivated | League tiers, seasonal rankings, friends feed |
| Get help | FAQs, 1:1 inquiry, announcements |

---

## 2. Personas

| Persona | Description | Priority flows |
|---|---|---|
| **Beginner Bea** | Studies K-culture, no Korean yet. | Onboarding → recommended Level 1 → streak |
| **Exam-bound Eun** | Targeting TOPIK 3/4. | TOPIK track, daily quizzes, writing feedback |
| **Busy Ben** | 10 min/day commuter. | Dashboard goals, audio sentences, reminders |
| **Social Sora** | Already learning, invited by friend. | Friend code, feed, league rankings |

---

## 3. Global Rules

### 3.1 Authentication & Session

- **Flow:** OAuth2 password flow + JWT access token (30 min) + refresh token (30 d).
- **Social providers:** Google, Apple, Kakao, Facebook, Line — exchange provider `id_token` for the same token envelope.
- **Phone verification** is required for (a) signup, (b) recovering email, (c) resetting password. SMS code has a 5-minute TTL and a 60-second resend cooldown.
- **Withdrawal (account deletion):** requires re-entering password (or social re-auth) and schedules a purge per privacy policy.
- **Bearer header:** `Authorization: Bearer <access_token>` on every authenticated request. Swagger "Authorize" uses `/auth/login/oauth2`.

### 3.2 Error envelope (RFC 7807)

All 4xx/5xx responses use `application/problem+json`:

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

Codes in active use: `validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `rate_limited`, `internal_error`, `http_<status>`.

### 3.3 Pagination

Cursor-based:

```json
{ "items": [...], "next_cursor": "opaque-string|null", "has_more": true }
```

Default page size 20 (min 1, max 100). Clients should stop when `next_cursor == null`.

### 3.4 Locales & time

- API bodies are UTF-8.
- Timestamps are ISO-8601 UTC.
- UI language codes: `ko`, `en`, `ja`, `zh-CN`, `zh-TW`, `vi`, `th`, `id`.
- Phone numbers are E.164.

### 3.5 Non-functional requirements

| Concern | Target |
|---|---|
| p95 API latency (reads) | ≤ 200 ms |
| p95 API latency (auth, AI) | ≤ 800 ms |
| Availability | 99.9 % monthly |
| Rate limit (anon) | 30 req/min per IP |
| Rate limit (authed) | 120 req/min per user |
| JWT rotation | Refresh once per access-token lifetime |
| Password rules | 8–64 chars, mixed case + digit |

---

## 4. Feature Modules

Each module below maps to a section of the Figma design, a module under `src/modules/`, and a tag group in the OpenAPI spec.

### 4.1 Authentication (`auth`)

**Screens:** splash/language select · email signup · social signup (5 providers) · phone verification · email/password recovery · welcome complete.

**User stories**

- As a new user, I can sign up with my email and password or a social provider so I can start learning immediately.
- As a returning user, I can recover my email or password using my phone number.
- As any user, I can withdraw my account and have my data deleted.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `POST /auth/signup/email` | Register with email + password |
| `POST /auth/login/email` | Login |
| `POST /auth/login/oauth2` | Swagger-UI password-flow endpoint |
| `POST /auth/login/social` | Social login (Google / Apple / Kakao / Facebook / Line) |
| `POST /auth/phone/verification` | Send SMS code |
| `POST /auth/phone/verification/confirm` | Verify SMS code → short-lived verification token |
| `POST /auth/email/recover` | Recover email from verification token |
| `POST /auth/password/reset` | Reset password after phone verification |
| `POST /auth/token/refresh` | Rotate access & refresh tokens |
| `POST /auth/logout` | Revoke refresh token |
| `DELETE /auth/account` | Withdraw account |

**Business rules**

- Nickname 2–20 chars, password 8–64 chars.
- Terms + privacy must be accepted at signup.
- Social accounts are deduplicated by provider + subject.
- SMS code retry: max 5 code sends / hour / phone; exceeded returns `rate_limited`.

---

### 4.2 User profile & discovery (`users`)

**Screens:** profile edit · nickname uniqueness · avatar picker · friend search.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /users/me` | Authenticated profile snapshot |
| `PATCH /users/me` | Update nickname / avatar / language |
| `POST /users/me/avatar` | Upload avatar image |
| `POST /users/check-nickname` | Nickname uniqueness check |
| `GET /users/search?code=&nickname=` | Search by friend code or nickname |
| `GET /users/{user_id}/profile` | Public progress profile |
| `POST /users/feedback` | Recommendation feedback signal |

**Business rules**

- Nickname is unique case-insensitively.
- `friend_code` is a 6–8 char code unique per user; used for adding friends.

---

### 4.3 Onboarding (`onboarding`)

**Screens:** learning purpose (회화 / TOPIK) · speaking level · TOPIK target · daily goal · push consent.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /onboarding/questions` | Question set for the carousel |
| `POST /onboarding/responses` | Submit answers → recommended track & level |
| `GET /onboarding/status` | Check completion state |

**Business rules**

- `purpose` selects the primary category.
  - `conversation`: seeds the Conversation lectures & sentences `current_level` from the `speaking_level` answer.
  - `topik`: seeds both TOPIK progressions to `current_level = 1`, and stores `topik_target` as the TOPIK `target_grade` (1–6).
- All seeded values are editable from Settings later.
- Daily goal defaults to 10 min; allowed 5–120 min.

---

### 4.4 Subscriptions (`subscriptions`)

**Screens:** paywall on dashboard · plan comparison ($7.99 / $5.99 promo / $54/yr) · purchase confirm · restore · purchase history.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /subscriptions/plans` | Plan catalog with promo prices |
| `GET /subscriptions/me` | Current subscription state |
| `POST /subscriptions/checkout` | Create checkout session (Stripe / Apple / Google) |
| `POST /subscriptions/cancel` | Cancel at period end |
| `POST /subscriptions/restore` | Restore purchases (mobile) |
| `GET /subscriptions/purchases` | Purchase history |

**Business rules**

- Trial: 7 days on monthly plan (first time only per user).
- Cancel at period end → access retained until `current_period_end`.
- Apple / Google purchases are server-verified via receipt; Stripe via webhook (out of scope of this spec but consumer API is fixed).

---

### 4.5 Dashboard (`dashboard`)

**Screens:** home with streak, two progress tracks, today's goal, paywall banner, bottom nav.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /dashboard/summary` | Aggregated home snapshot |
| `GET /dashboard/streak` | Detailed streak payload |

**Business rules**

- `streak_days` increments when the user hits `today_minutes_goal` (default 10 min).
- `freeze_tokens` (0+) protect a streak if the user misses a day.
- `paywall_required=true` when the next lesson requires subscription.

---

### 4.6 Learning categories & progressions (`learning`)

Learning is split into **two top-level categories**, each containing **two independent progressions** that advance separately:

| Category | Track ID | Progressions |
|---|---|---|
| Conversation (회화) | `trk_conversation` | lectures · sentences |
| TOPIK | `trk_topik` | lectures · sentences |

For every (user, category, progression) triple, the server maintains a **`current_level`** that advances as the user completes content.

TOPIK additionally carries a **`target_grade`** at the category level — the user's goal 급수 (1–6), captured at onboarding.

**Defaults**

- **TOPIK:** both lectures and sentences start at `current_level = 1`; `target_grade` comes from onboarding `topik_target` (1–6).
- **Conversation:** `current_level` for both lectures and sentences is seeded from onboarding `speaking_level`.

Users can override the `current_level` of any progression — and, for TOPIK, the `target_grade` — from Settings at any time (see 4.17).

**Screens:** category / progression selector · level list (학습 레벨 1–N) · calendar grid · stats charts · video player · sentence list.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /tracks` | List the two categories with their progression metadata. |
| `GET /tracks/{track_id}` | Category detail. |
| `GET /tracks/{track_id}/progressions/{kind}/levels` | Levels in a progression. `kind` ∈ `lectures`, `sentences`. |
| `GET /me/learning` | My `current_level` per (category, progression), plus TOPIK `target_grade`. |
| `PATCH /me/learning/{track_id}/{kind}` | Update my `current_level` in a progression. |
| `PATCH /me/learning/trk_topik` | Update my TOPIK `target_grade` (1–6). |
| `GET /learning/calendar?from=&to=` | Daily study calendar (aggregated across categories). |
| `GET /learning/stats?range=week\|month\|year\|all` | Aggregated stats for charts. |
| `GET /lectures?track_id=&level=` | List lectures for a (category, level) — always the lectures progression. |
| `GET /lectures/{id}` | Lecture detail. |
| `GET /lectures/{id}/video` | Signed video URL (HLS, TTL ≤ 1 h). |
| `POST /lectures/{id}/progress` | Playback heartbeat and completion signal. |

**Business rules**

- Lectures and sentence study advance **independently** — completing a lecture never moves the sentence-study `current_level`, and vice versa.
- Within a progression, levels unlock sequentially (level N requires 100 % of level N-1).
- Video URLs are signed and expire; clients must refresh on expiry.
- XP is awarded once per (user, lecture) on completion.

---

### 4.7 Sentence study (`sentences`)

Sentence study is one of the two progressions in each category (see 4.6). The study feed is scoped to the user's active category and its sentence-progression `current_level`, which advances independently from the lectures progression.

**Screens:** sentence list with audio, bookmark, grammar points · bookmarked list · recently studied.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /sentences?track_id=&level=&topic=&cursor=` | Study feed — defaults to the user's active category and sentence-progression `current_level` |
| `GET /sentences/bookmarks` | Bookmarked sentences |
| `GET /sentences/recently-studied` | Recency list |
| `GET /sentences/{id}` | Sentence detail with examples |
| `POST /sentences/{id}/bookmark` | Add bookmark |
| `DELETE /sentences/{id}/bookmark` | Remove bookmark |
| `POST /sentences/{id}/listen` | Audio playback event |
| `GET /sentences/{id}/audio` | Signed audio URL |

**Business rules**

- Sentence `status` moves `new → learning → mastered` based on quiz + exposure signals.
- Audio URLs TTL ≤ 15 min.

---

### 4.8 Quizzes (`quizzes`)

**Screens:** MCQ (덕분에/동안/처럼/만큼) · typing quiz with Korean keyboard · celebration / retry.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /quizzes?type=&level=` | Quiz bank |
| `GET /quizzes/daily` | Today's curated set |
| `GET /quizzes/{id}` | Single question |
| `POST /quizzes/{id}/attempts` | Submit answer |
| `GET /quizzes/{id}/attempts/{attempt_id}` | Past attempt detail |
| `GET /quizzes/attempts/me` | My attempt history |

**Business rules**

- Attempt XP: +10 correct, 0 wrong; bonus +5 if streak of 5 correct in a row.
- Daily set is deterministic per (user, date); safe to re-fetch.
- Explanations localized by `language` query or profile default.

---

### 4.9 Writing practice (`writing`)

**Screens:** prompt list · free-form Korean composition · graded feedback.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /writing/prompts` | Prompt list |
| `POST /writing/prompts/{id}/submissions` | Submit text |
| `GET /writing/submissions/me` | My past submissions |
| `GET /writing/submissions/{id}` | Submission + AI feedback |

**Business rules**

- Text length 1–2000 chars.
- Feedback fields: `score 0–100`, grammar issues, suggestions, corrected text. Graded async — status `pending → graded | failed`.

---

### 4.10 한글AI chat (`ai-chat`)

**Screens:** "물어보기" conversation with chat bubbles + suggestion chips.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `POST /ai/conversations` | Start session |
| `GET /ai/conversations` | List sessions |
| `GET /ai/conversations/{id}/messages` | Paged message history |
| `POST /ai/conversations/{id}/messages` | Send user message, receive assistant reply |

**Business rules**

- Content moderation: prompt + response filtered before return.
- Free plan: 10 AI messages / day; subscribers unlimited (429 `rate_limited` when exceeded).
- Suggestion chips are optional follow-ups surfaced by the model.

---

### 4.11 Gamification — points, leagues, seasons (`gamification`)

**Screens:** points balance · current league tier (Green → Lime → Yellow → Orange) · 2026 Spring Season leaderboard · past seasons.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /points/me` | Balance (total / weekly / season) |
| `GET /points/history` | Points-earning events |
| `GET /leagues/me` | Current tier, rank, promotion thresholds |
| `GET /leagues/current` | Active season metadata |
| `GET /leagues/current/rankings` | Live leaderboard |
| `GET /leagues/seasons` | Past seasons |
| `GET /leagues/seasons/{id}/rankings` | Frozen leaderboard |

**Business rules**

- Seasons last roughly one quarter (configurable).
- Promotion when `season_points >= promotion_threshold`; demotion when below `demotion_threshold` at season close.
- Leaderboards are eventually consistent (≤ 60 s lag).

---

### 4.12 Social — friends & feed (`social`)

**Screens:** friend add by code · incoming/outgoing requests · friend list · friends activity feed · reactions.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /friends` | My friends |
| `POST /friends` | Send request (by code or user_id) |
| `DELETE /friends/{user_id}` | Remove friend |
| `GET /friends/requests` | Incoming & outgoing requests |
| `POST /friends/requests/{id}/accept` | Accept |
| `POST /friends/requests/{id}/decline` | Decline |
| `GET /feed` | Friend activity feed |
| `POST /feed/{id}/reactions` | React with emoji |

**Business rules**

- Friends capped at 300 per user.
- Feed item types: `level_up`, `streak`, `badge`, `league_promotion`, `friend_join`.
- Reactions use emoji shortcodes; rate-limited to 30 / min / user.

---

### 4.13 Notifications (`notifications`)

**Screens:** alarm inbox · notification detail · push & email preferences.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /notifications` | Paginated inbox |
| `POST /notifications/{id}/read` | Mark one read |
| `POST /notifications/read-all` | Mark all read |
| `GET /notifications/settings` | Current preferences |
| `PUT /notifications/settings` | Update preferences |

**Business rules**

- Categories: `learning_reminder`, `streak`, `friend`, `league`, `announcement`, `marketing`, `system`.
- Quiet hours respect device timezone; server sends a scheduled-for-later flag.
- Push-token registration is handled by a device-registration endpoint (future).

---

### 4.14 Announcements (`announcements`)

**Screens:** announcement list · pinned banners · detail view.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /announcements` | List |
| `GET /announcements/{id}` | Detail |

**Business rules**

- Categories: `notice`, `event`, `update`, `maintenance`.
- Pinned items always sort first.

---

### 4.15 Support — FAQs & 1:1 inquiries (`support`)

**Screens:** FAQ categories · FAQ detail · 1:1 inquiry form · my inquiries.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /support/faqs?category=` | Browsable FAQ |
| `GET /support/faqs/{id}` | Detail |
| `POST /support/inquiries` | Submit inquiry |
| `GET /support/inquiries/me` | My inquiries |
| `GET /support/inquiries/{id}` | Single inquiry + admin reply |

**Business rules**

- Inquiry statuses: `open → in_progress → answered | closed`.
- Attachments uploaded via pre-signed S3 URLs.

---

### 4.16 Legal documents (`legal`)

**Screens:** terms · privacy · marketing consent.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /legal/terms?locale=` | Terms of service |
| `GET /legal/privacy?locale=` | Privacy policy |
| `GET /legal/marketing-consent?locale=` | Marketing consent text |

**Business rules**

- Each document has `version` + `effective_date`. On bump, app prompts re-acceptance.

---

### 4.17 App settings (`settings`)

**Screens:** language · theme · audio · vibration · romanization · daily goal · active category · current level per progression · TOPIK target grade.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /settings/me` | UI preferences |
| `PUT /settings/me` | Update UI preferences |
| `GET /me/learning` | Read `current_level` per progression and TOPIK `target_grade` (see 4.6) |
| `PATCH /me/learning/{track_id}/{kind}` | Change `current_level` in a progression (see 4.6) |
| `PATCH /me/learning/trk_topik` | Change TOPIK `target_grade` (see 4.6) |

**Business rules**

- Language change is propagated to `users.language` automatically.
- `daily_goal_minutes` bounded 5–120.
- Current-level overrides delegate to `PATCH /me/learning/{track_id}/{kind}`; TOPIK target-grade changes go to `PATCH /me/learning/trk_topik`.

---

### 4.18 Recommendations (internal, `recommendations`)

The pre-existing recommendation engine module. Consumed by dashboard & sentence feed to pick next-best content.

---

## 5. State Machines (summary)

### 5.1 Sentence mastery

```
new ──answer_correct──▶ learning ──correct_streak(3)──▶ mastered
          ▲                                            │
          └──────────── answer_wrong ──────────────────┘
```

### 5.2 Writing submission

```
pending ──grader_ok──▶ graded
pending ──grader_fail──▶ failed
```

### 5.3 Subscription

```
none → trialing → active → past_due → canceled / expired
                           │
                           └── cancel_at_period_end → canceled
```

### 5.4 Friend request

```
pending ──accept──▶ accepted
pending ──decline──▶ declined
pending ──cancel──▶ canceled
```

---

## 6. Domain Glossary

| Term | Meaning |
|---|---|
| **Category** | Top-level learning grouping: Conversation (회화) or TOPIK. |
| **Track** | Synonym for Category in API paths (`/tracks`, `trk_conversation`, `trk_topik`). |
| **Progression** | An independent level sequence inside a category: `lectures` or `sentences`. Advances separately per user. |
| **Level** | Ordered unit within a progression (학습 레벨 1–N). |
| **Lecture** | Video / reading / listening unit inside the lectures progression. |
| **Sentence** | Smallest studyable item with audio and grammar tags. |
| **Quiz** | MCQ / fill-blank / typing / ordering / listening. |
| **Attempt** | A single submitted answer on a quiz. |
| **Streak** | Consecutive days the user hit their daily goal. |
| **Tier** | League position: Green → Lime → Yellow → Orange. |
| **Season** | Quarterly cycle with frozen final standings. |
| **HangulAI (한글AI)** | On-demand AI conversation partner. |
