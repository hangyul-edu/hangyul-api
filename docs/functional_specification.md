# Functional Specification — Hangyul Korean Learning Platform

- OpenAPI / Swagger UI: `GET /openapi.json`, `GET /docs`

---

## 1. Product Overview

Hangyul is a mobile Korean-language learning service for non-native speakers. Learning is organized into two tracks that differ by the type of content recommended:

- **Conversation (회화) track** → recommends **sentences** for study and practice.
- **TOPIK track** → recommends **questions** for the user to solve.

Each track has a single **`current_level`** representing the difficulty at which the user wants recommendations. There is no separate target level. The current level **auto-promotes** as the user meets per-track criteria. Recommendations can also be requested via free-form prompts (e.g. "sentences I can use when ordering food"). When the user answers a recommended TOPIK question incorrectly, the AI chatbot is invoked to explain the mistake.

The service combines streak-driven daily sessions, adaptive recommendations, video lectures, quizzes, an AI conversation partner, and a social league.

### 1.1 Primary user goals

| Goal | Supporting features |
|---|---|
| Learn enough Korean for everyday conversation | Conversation track (sentence recommendations), HangulAI chat, listening lessons |
| Practise TOPIK questions at the right level | TOPIK track (question recommendations), quiz attempts, AI explanations on mistakes |
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

### 3.5 Meta endpoints

- `GET /health` — unauthenticated liveness probe, returns `{"status": "ok"}`. Used by load balancers and uptime monitors.
- `GET /openapi.json` and `GET /docs` (Swagger UI) are FastAPI-provided and require no auth.

### 3.6 Non-functional requirements

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

- `purpose` selects the primary track.
  - `conversation`: `speaking_level` seeds the Conversation track's initial `current_level`.
  - `topik`: `topik_target` seeds the TOPIK track's initial `current_level` (1..6, treated as 급수).
- Both tracks exist for every user; `purpose` only determines which one the app opens to by default. Levels are editable from Settings and also auto-promote over time (see 4.6).
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

### 4.6 Learning tracks (`learning`)

Two tracks, distinguished by the type of recommended content:

| Track | Track ID | Recommended content | Level scale |
|---|---|---|---|
| Conversation (회화) | `trk_conversation` | sentences for study & practice | 1..10 |
| TOPIK | `trk_topik` | questions to solve | 1..6 (급수) |

Each track stores a single **`current_level`** per user — the difficulty at which the user wants recommendations. There is no target level.

**Auto-promotion**

- `current_level` advances automatically when per-track criteria are met. The criteria are configured server-side and may differ per track; examples: consecutive-day streak at a level, threshold of completed sentences, rolling accuracy on recommended questions.
- On promotion, the server emits a `LevelUpEvent` (surfaced in the dashboard / notifications).

**Manual override**

Users can also change `current_level` directly from Settings (see 4.17) — useful when starting from above beginner or stepping back to reinforce a level.

**Defaults**

- **Conversation:** seeded from onboarding `speaking_level`.
- **TOPIK:** seeded from onboarding `topik_target` (1..6 = 급수).

**Screens:** track selector · level badge · auto-promotion celebration · calendar grid · stats charts · video player · sentence list · TOPIK question list.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /tracks` | List the two tracks with their metadata. |
| `GET /tracks/{track_id}` | Track detail. |
| `GET /tracks/{track_id}/levels` | Levels available in a track (1..N) with labels. |
| `GET /me/learning` | My `current_level` per track. |
| `PATCH /me/learning/{track_id}` | Manually update my `current_level` in a track. |
| `GET /me/learning/events?type=level_up&cursor=` | Auto-promotion history. |
| `GET /learning/calendar?from=&to=` | Daily study calendar. |
| `GET /learning/stats?range=week\|month\|year\|all` | Aggregated stats for charts. |
| `GET /lectures?track_id=&level=` | List lectures for a (track, level). Lectures are a supplemental content type, primarily for TOPIK. |
| `GET /lectures/{lecture_id}` | Lecture detail. |
| `GET /lectures/{lecture_id}/video` | Signed video URL (HLS, TTL ≤ 1 h). |
| `POST /lectures/{lecture_id}/progress` | Playback heartbeat and completion signal. |

**Business rules**

- Conversation and TOPIK levels are independent — advancing in one never moves the other.
- Auto-promotion is criterion-based, evaluated on learning events (quiz attempts, sentence completions, etc.). There is no automatic demotion.
- The user can manually change `current_level` in either direction (up or down) at any time, including returning to a level already visited (e.g. `1 → 2 → 3 → 2`). **Any manual change resets the in-flight promotion progress on that track**: the user must re-accumulate activity at the new level to be evaluated for promotion again.
- Lectures are optional content and do not affect auto-promotion.

---

### 4.7 Sentence study (`sentences`)

Sentences are the recommended content type for the Conversation track. The feed is filtered by the user's Conversation `current_level` by default, and can also be driven by free-form prompt (see 4.18). Bookmarking, audio, and review-complete events continue to feed the Conversation auto-promotion criteria.

**Screens:** sentence list with audio, bookmark, grammar points · bookmarked list · recently studied.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /sentences?level=&topic=&cursor=` | Study feed — defaults to the user's Conversation `current_level`. |
| `GET /sentences/bookmarks` | Bookmarked sentences |
| `GET /sentences/recently-studied` | Recency list |
| `GET /sentences/{sentence_id}` | Sentence detail with examples |
| `POST /sentences/{sentence_id}/bookmark` | Add bookmark |
| `DELETE /sentences/{sentence_id}/bookmark` | Remove bookmark |
| `POST /sentences/{sentence_id}/listen` | Audio playback event |
| `GET /sentences/{sentence_id}/audio` | Signed audio URL |

**Business rules**

- Sentence `status` moves `new → learning → mastered` based on quiz + exposure signals.
- Audio URLs TTL ≤ 15 min.

---

### 4.8 Quizzes (`quizzes`)

Quizzes are the recommended content type for the TOPIK track. Questions are pulled from the user's TOPIK `current_level` by default, and can also be requested via free-form prompt (see 4.18). **On an incorrect answer**, the server starts an AI-chat explanation conversation and returns its id in the attempt response; the client links the user into that chat to receive a richer explanation (see 4.10).

**Screens:** MCQ (덕분에/동안/처럼/만큼) · typing quiz with Korean keyboard · celebration / retry · "AI explains the mistake" deep link.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /quizzes?type=&level=` | Quiz bank |
| `GET /quizzes/daily` | Today's curated set |
| `GET /quizzes/{quiz_id}` | Single question |
| `POST /quizzes/{quiz_id}/attempts` | Submit answer |
| `GET /quizzes/{quiz_id}/attempts/{attempt_id}` | Past attempt detail |
| `GET /quizzes/attempts/me` | My attempt history |

**Business rules**

- Attempt XP: +10 correct, 0 wrong; bonus +5 if streak of 5 correct in a row.
- Daily set is deterministic per (user, date); safe to re-fetch.
- Explanations localized by `language` query or profile default.
- When a recommended TOPIK attempt is incorrect, the server starts an AI-chat conversation seeded with the question + the user's answer + the correct answer, and returns its `chatbot_conversation_id` in the attempt response. The client opens `/ai/conversations/{conversation_id}/messages` to continue.
- Correct TOPIK attempts feed the TOPIK auto-promotion criteria in the learning module.

---

### 4.9 Writing practice (`writing`)

**Screens:** prompt list · free-form Korean composition · graded feedback.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /writing/prompts` | Prompt list |
| `POST /writing/prompts/{prompt_id}/submissions` | Submit text |
| `GET /writing/submissions/me` | My past submissions |
| `GET /writing/submissions/{submission_id}` | Submission + AI feedback |

**Business rules**

- Text length 1–2000 chars.
- Feedback fields: `score 0–100`, grammar issues, suggestions, corrected text. Graded async — status `pending → graded | failed`.

---

### 4.10 한글AI chat (`ai-chat`)

**Screens:** "물어보기" conversation with chat bubbles + suggestion chips · "AI explains the mistake" conversations launched from a wrong TOPIK attempt (4.8).

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `POST /ai/conversations` | Start session |
| `GET /ai/conversations` | List sessions |
| `GET /ai/conversations/{conversation_id}/messages` | Paged message history |
| `POST /ai/conversations/{conversation_id}/messages` | Send user message, receive assistant reply |

**Business rules**

- Content moderation: prompt + response filtered before return.
- Free plan: 10 AI messages / day; subscribers unlimited (429 `rate_limited` when exceeded).
- Suggestion chips are optional follow-ups surfaced by the model.
- Explanation conversations opened from a wrong TOPIK attempt are pre-seeded by the server with the question, the user's answer, the correct answer, and a request for a clear explanation; the first assistant reply is the explanation.

---

### 4.11 Gamification — points, leagues, seasons (`gamification`)

**Screens:** points balance · points-earning history · my group leaderboard (30 users) · my league tier · past seasons · end-of-season result banner (promote / maintain / demote).

**Tiers**

Five tiers progress as: **Green → Lime → Yellow → Orange → Golden**. Each tier auto-splits into **groups of 30 users** matched by activity level (e.g. a tier holding 300 users has 10 groups). Rankings are computed **per group**, not per tier.

| Tier | Group size | Promotion | Demotion |
|---|---|---|---|
| Green | 30 | ✓ | ✗ (floor) |
| Lime | 30 | ✓ | ✓ |
| Yellow | 30 | ✓ | ✓ |
| Orange | 30 | ✓ | ✓ |
| Golden | 30 | ✗ (ceiling) | ✓ |

**Seasons**

- Each season lasts **one week** in **US Eastern Time (America/New_York, Washington D.C. reference)**: Monday 00:00 ET → Sunday 21:00 ET. The boundary follows US DST automatically (EST / EDT).
- `season_id` uses the ISO-week label computed in America/New_York (e.g. `2026-W17`).
- Season end triggers, in order: (1) final ranking, (2) promote / maintain / demote, (3) points reset to 0 at the start of the next season.
- Client displays may localize the window to the user's device timezone, but all server decisions (season boundaries, scheduled jobs, tie-break clocks) are anchored to America/New_York.

**Promotion / demotion bands (per group of 30)**

- **Top 20 %** — ranks 1–6 → promote.
- **Middle 60 %** — ranks 7–24 → maintain.
- **Bottom 20 %** — ranks 25–30 → demote.
- Green never demotes; Golden never promotes.

**Points earning**

| Action | Points |
|---|---|
| Daily attendance | 5 |
| 7-day attendance streak bonus | +10 |
| Sentence completed | 10 per sentence (e.g. 5-sentence course → 50, 20-sentence course → 200) |
| Lecture completed | 100 |
| Saved-sentence review completed | 5 |

- All points accumulate during the week; resets at season start.
- Tie-break: most recent activity wins (higher `last_activity_at` ranks first).

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /points/me` | Balance (total / weekly / season) |
| `GET /points/history` | Points-earning events |
| `GET /leagues/me` | My current tier, group, rank, and promote/demote cutoffs |
| `GET /leagues/current` | Active weekly season metadata |
| `GET /leagues/current/rankings` | Live leaderboard of my current group |
| `GET /leagues/current/groups/{group_id}/rankings` | Leaderboard for a specific group (e.g. a friend's) |
| `GET /leagues/seasons` | Past seasons |
| `GET /leagues/seasons/{season_id}/rankings` | Frozen leaderboard of my group for that season |

**Business rules**

- Rankings update in real time; a few seconds of lag is acceptable.
- At season close, `RankingEntry.outcome` is set to `promote` / `maintain` / `demote` per the bands above.
- Group assignment is stable within a season and recomputed at season start.

---

### 4.12 Social — friends & feed (`social`)

**Screens:** friend add by code · incoming/outgoing requests · friend list · friends activity feed · reactions.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /friends` | My friends |
| `POST /friends` | Send request (by code or user_id) |
| `DELETE /friends/{friend_user_id}` | Remove friend |
| `GET /friends/requests` | Incoming & outgoing requests |
| `POST /friends/requests/{request_id}/accept` | Accept |
| `POST /friends/requests/{request_id}/decline` | Decline |
| `GET /feed` | Friend activity feed |
| `POST /feed/{feed_id}/reactions` | React with emoji |

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
| `POST /notifications/{notification_id}/read` | Mark one read |
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
| `GET /announcements/{announcement_id}` | Detail |

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
| `GET /support/faqs/{faq_id}` | Detail |
| `POST /support/inquiries` | Submit inquiry |
| `GET /support/inquiries/me` | My inquiries |
| `GET /support/inquiries/{inquiry_id}` | Single inquiry + admin reply |

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

**Screens:** language · theme · audio · vibration · romanization · daily goal · active track · current level per track.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /settings/me` | UI preferences |
| `PUT /settings/me` | Update UI preferences |
| `GET /me/learning` | Read `current_level` per track (see 4.6) |
| `PATCH /me/learning/{track_id}` | Change `current_level` in a track (see 4.6) |

**Business rules**

- Language change is propagated to `users.language` automatically.
- `daily_goal_minutes` bounded 5–120.
- Manual level changes delegate to `PATCH /me/learning/{track_id}`. Users may move up or down freely. Any such change **resets the in-flight promotion progress** on that track, so auto-promotion re-evaluates from scratch at the new level (see 4.6).

---

### 4.18 Recommendations (`recommendations`)

The primary surface for track content. Supports both *default* level-based recommendations and *prompt-driven* requests where the user asks for specific learning content.

**Recommendation modes**

- **Level-based (default):** server uses the caller's `current_level` in the requested track plus recent history to pick items.
- **Prompt-driven:** the client passes a free-form `prompt` such as "sentences I can use when ordering food" or "TOPIK 4급 level grammar questions about 피동". The server uses an LLM to interpret and select items that satisfy the request.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `POST /recommendations/sentences` | Conversation-track recommendation — returns sentences (body: `{level?, prompt?, count?}`) |
| `POST /recommendations/questions` | TOPIK-track recommendation — returns quiz questions (body: `{level?, prompt?, count?}`) |
| `GET /recommendations/history?kind=sentences\|questions&cursor=` | Recently recommended items (for "again"/"similar" follow-ups) |
| `POST /recommendations` | Legacy internal recommender (back-compat with the original scaffold). New clients should use the sentences / questions endpoints above. |

**Business rules**

- If `level` is omitted, the user's current level in that track is used.
- `prompt` is capped at 500 chars and moderated before being sent to the LLM.
- `count` defaults to 5, max 20.
- Items returned by `/recommendations/questions` use the same `QuizQuestion` shape as §4.8; attempts are submitted through the quiz attempt endpoint.
- Items returned by `/recommendations/sentences` use the same `Sentence` shape as §4.7; bookmarks and listen events flow through the sentence endpoints.

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

### 5.5 Track level auto-promotion

```
current_level N ──per-track criteria met──▶  current_level N+1   (emits LevelUpEvent)
current_level N ──manual change (Settings)──▶ current_level M    (any 1..max; resets level_progress)
```

Manual changes work in either direction. There is no automatic demotion, but every manual change — up *or* down — resets the in-flight promotion progress on that track (`level_progress_ratio` returns to 0).

---

## 6. Domain Glossary

| Term | Meaning |
|---|---|
| **Track** | Top-level learning split: Conversation (회화) or TOPIK. Each has its own `current_level`. |
| **Current level** | The user's chosen difficulty for recommendations in a track. Auto-promotes on criteria; editable from Settings. |
| **Level auto-promotion** | Server-side event raising `current_level` when per-track criteria are met. |
| **Recommendation** | Server-picked content — sentences for Conversation, questions for TOPIK. May be level-based or prompt-driven. |
| **Lecture** | Supplemental video / reading / listening unit, primarily for TOPIK; does not affect auto-promotion. |
| **Sentence** | Smallest studyable item with audio and grammar tags. |
| **Quiz** | MCQ / fill-blank / typing / ordering / listening. |
| **Attempt** | A single submitted answer on a quiz. |
| **Streak** | Consecutive days the user hit their daily goal. |
| **Tier** | League position: Green → Lime → Yellow → Orange → Golden. |
| **Group** | Set of 30 users inside a tier, matched by activity level; rankings are scoped to groups. |
| **Season** | Weekly cycle in US Eastern Time (Mon 00:00 ET → Sun 21:00 ET) that closes with promote / maintain / demote and a point reset. |
| **HangulAI (한글AI)** | On-demand AI conversation partner. |
