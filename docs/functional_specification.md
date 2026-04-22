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
| Speak everyday Korean with confidence | Conversation track — AI-generated sentence recommendations at the user's current level, optionally refined by a prompt (e.g. "sentences for ordering food"), plus HangulAI chat and audio playback |
| Practise TOPIK at my level and learn from mistakes | TOPIK track — AI-generated question recommendations at the user's current level, optionally refined by a prompt; AI chatbot automatically explains wrong answers |
| Study at a difficulty that feels right | Auto-promotion when per-track criteria are met; users can also move `current_level` up or down freely from Settings (progress resets on every manual change) |
| Keep a weekly rhythm with friends | Streaks, daily goal, reminders, 30-person weekly league (US Eastern, promote / maintain / demote), activity feed |
| Self-serve help when stuck | FAQs, 1:1 inquiry, in-app announcements |

---

## 2. Personas

| Persona | Description | Priority flows |
|---|---|---|
| **Beginner Bea** | K-content fan; picking up Korean from scratch. | Onboarding (`purpose=conversation`, `speaking_level=beginner`) → Conversation Lv 1 sentence feed → streak + audio |
| **Exam-focused Eun** | Working professional targeting TOPIK 3–4. | Onboarding (`purpose=topik`, `topik_target=4`) → TOPIK question recs at her level → AI chat unpacks every wrong answer |
| **Prompt-refining Paul** | Intermediate learner with situation-specific goals. | Uses the on-screen prompt input to refine his level-based feed (e.g. "sentences for a job interview", "피동 grammar questions") — the server re-calls `POST /recommendations/...` with his current level + the prompt; bookmarks favorites |
| **Busy Ben** | 10-minute commuter; wants short, audio-first sessions. | Dashboard daily goal → audio-led sentences → streak protection via freeze tokens |
| **Competitive Chris** | Motivated by ranks and social pressure. | Weekly 30-person group leaderboard (US Eastern) → top 20 % to promote → friend-feed reactions |

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

**Screens:** profile edit · nickname uniqueness · avatar picker (photo upload + default-character gallery) · friend search.

**Avatar picker**

Users can register their profile image in either of two ways:

1. **Upload a photo** — capture or pick an image from the phone and upload it as multipart.
2. **Pick a default character** — choose one of the app's curated character avatars. The client first fetches the catalog, then submits the chosen `default_avatar_id`.

The response schema (`AvatarResponse`) is the same for both paths and carries `source ∈ {"uploaded", "default"}` plus the resulting `avatar_url`.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /users/me` | Authenticated profile snapshot |
| `PATCH /users/me` | Update nickname / language (avatar_url can also be set directly but the dedicated endpoints below are preferred) |
| `GET /users/avatars/defaults` | List the built-in default character avatars (catalog for the picker) |
| `POST /users/me/avatar` | Multipart upload of a phone photo as the avatar |
| `POST /users/me/avatar/default` | Pick a default character by `default_avatar_id` |
| `POST /users/check-nickname` | Nickname uniqueness check |
| `GET /users/search?code=&nickname=` | Search by friend code or nickname |
| `GET /users/{user_id}/profile` | Public progress profile |
| `POST /users/feedback` | Recommendation feedback signal |

**Business rules**

- Nickname is unique case-insensitively.
- `friend_code` is a 6–8 char code unique per user; used for adding friends.
- Photo upload accepts JPEG / PNG / WebP / HEIC, ≤ 5 MB; missing `file` returns `422 validation_error`.
- `POST /users/me/avatar/default` rejects unknown `default_avatar_id` with `404 not_found`.
- The two avatar-setting endpoints both return `AvatarResponse`, and the server stores `source` alongside `avatar_url` so that a future catalog refresh can re-resolve `default_avatar_id` to the latest image.

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
- `goals[]` carries today's progress on each daily goal configured in Settings (§4.17): `daily_minutes` (unit=minutes), `daily_sentences` (unit=count, `track_id=trk_conversation`), and `daily_questions` (unit=count, `track_id=trk_topik`). Each item reports `target` and `current`, so the client can render a ring/progress bar per goal. Counters roll over at the start of the user's local day.

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

Sentences are the recommended content type for the Conversation track; every recommendation is **AI-generated at the user's Conversation `current_level`** (see 4.18). Bookmarking, audio, and review-complete events feed the Conversation auto-promotion criteria.

**Each recommended sentence ships with its own AI-generated pronunciation audio.** The response payload includes a nested `audio` object — a signed CDN URL plus format, duration, voice, and an `expires_at`. The client caches the audio file locally; the in-app replay button plays the local file with no extra API call.

**Each recommended sentence also ships with a translation in the user's selected default language.** Every `Sentence` carries `translation` (the rendered meaning) together with `translation_language` (BCP-47, mirrors `users.language` — e.g. `en`, `ja`, `zh-CN`). When the user updates `users.language`, subsequent recommendations are regenerated in the new language.

**Read-aloud flow**

1. Sentence arrives → client auto-plays `audio` once.
2. (Optional) user taps the replay button → client re-plays the cached file.
3. User taps the microphone and reads the sentence aloud (including any blanks in `display_text`). The client records audio and uploads it to `POST /sentences/{sentence_id}/speech-attempts`.
4. Server runs ASR + pronunciation scoring against the reference `korean` text and returns:
   - `correct: bool`
   - `transcription: str` — what the user actually pronounced
   - `pronunciation_score: int` (0–100)
   - `feedback_code: "correct" | "missed_words" | "bad_pronunciation" | "unclear_audio"`
5. Client UI:
   - `correct=true` → blue "correct" message.
   - `correct=false` → red "think again and try once more" message.

**Blanks**

If the recommended sentence is a fill-in-the-blank exercise, `display_text` contains the blanked form (e.g. `덕분에 잘 ___ 있어요`) while `korean` holds the full answer for TTS and evaluation. `blanks[]` carries the expected fill-ins.

Two distinct UIs live on the sentence screen:

1. **Prompt input (for recommendation refinement)** — a text field with a send button near the content card. Typing e.g. "sentences for a job interview" and pressing send re-calls `POST /recommendations/sentences` with the current level and the prompt; the new list replaces the feed.
2. **Chatbot icon (for context-aware chat)** — a separate icon in the top-right. Tapping it calls `POST /ai/conversations` with `context.kind="sentence"`, `sentence_id=...`, and optionally `auto_assistant_reply=true` when the entry point is a pre-canned CTA (4.10).

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
| `POST /sentences/{sentence_id}/listen` | Audio playback event (analytics + auto-promotion signal) |
| `GET /sentences/{sentence_id}/audio` | Refresh the signed audio URL (e.g. after `expires_at`); replay normally uses the cached file |
| `POST /sentences/{sentence_id}/speech-attempts` | Multipart upload of the user's spoken reading; returns correctness, ASR transcription, and pronunciation score |

**Business rules**

- Sentence `status` moves `new → learning → mastered` based on speech + exposure signals.
- Recommended sentences always include `audio` (AI TTS). Audio URLs are signed with a ≤ 15-minute TTL; the client caches the file locally on first fetch and reuses the cached file for replay. After `expires_at`, the client can call `GET /sentences/{sentence_id}/audio` to mint a fresh URL.
- `POST /sentences/{sentence_id}/speech-attempts` accepts audio up to 2 MB and 15 seconds. Requests without an `audio` file return `422 validation_error`. Each attempt mints an `attempt_id` for analytics / auto-promotion.
- The client-side UI uses `correct=true` to render a blue confirmation; any `correct=false` variant renders a red "think again" prompt with a retry affordance.

---

### 4.8 Quizzes (`quizzes`)

Quizzes are the recommended content type for the TOPIK track. Every question is **AI-generated at the user's TOPIK `current_level`** (see 4.18). A prompt-input UI next to the question card lets the user refine what gets generated (e.g. "피동 grammar questions") — submitting it re-calls `POST /recommendations/questions` with the current level and the prompt. **On an incorrect answer**, the server does **not** pre-create a conversation; instead, the chatbot icon shows a CTA offering an explanation. Only when the user taps it does the client open an AI-chat conversation seeded with the attempt and receive the explanation (see 4.10).

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
- When a recommended TOPIK attempt is incorrect, the attempt response carries no pre-built conversation. The client shows the chatbot icon with a CTA such as "Would you like an explanation of why it was incorrect or which part was confusing?". **Only when the user taps the CTA** does the client call `POST /ai/conversations` with `context.kind="quiz_attempt"`, `attempt_id=…`, `reason="explain_mistake"`, and `auto_assistant_reply=true`. The server then generates the explanation as the first assistant message in the new conversation, and the client navigates the user into it.
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

**Screens:** "물어보기" conversation with chat bubbles + suggestion chips · chatbot icon (top-right) overlaid on every study screen · "AI explains the mistake" conversations launched from a wrong TOPIK attempt (4.8).

> **Not the same as the recommendation prompt input.** Study screens also have a dedicated prompt-input field that drives the *recommendation* feed (see 4.7, 4.8, 4.18). The chatbot icon opens *this* module (conversational Q&A about the item). Both UIs may be visible at once; they are independent.

**Context-aware start**

Every study screen — sentence detail (4.7), quiz question (4.8), lecture player (4.6) — surfaces the chatbot icon. When the user taps it, the client starts a conversation **with structured context**, so the AI already knows what the user is looking at and the user does not need to retype anything.

The context object:

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

Only the fields relevant to `kind` are populated.

**Assistant-first replies (no user prompt required)**

`POST /ai/conversations` accepts `auto_assistant_reply: true`. When set, the server generates the first assistant message from `context` alone and returns it inline as `first_assistant_message`. This powers UI CTAs such as:

- TOPIK wrong answer → chatbot icon shows "Would you like an explanation of why it was incorrect or which part was confusing?" → tap → conversation is created with `context.kind="quiz_attempt"` + `reason="explain_mistake"` + `auto_assistant_reply=true`, and the first assistant message (the explanation) is rendered immediately.
- Sentence study → "What does this mean in a casual vs formal register?" → tap → conversation is created with `context.kind="sentence"` + `auto_assistant_reply=true`, and the first assistant message is already there.

All of these flows share one server behavior: no conversation is created in advance. Conversations are created on user action (tapping the chatbot icon or a CTA chip), and `auto_assistant_reply=true` is what drives the server to produce a ready-to-show assistant message in the same response.

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

**Screens:** language · theme · audio · vibration · romanization · daily goals (minutes + Conversation sentences + TOPIK questions) · active track · current level per track.

**Daily goals**

Three independent counters on `AppSettings`:

| Field | Scope | Range | Default |
|---|---|---|---|
| `daily_goal_minutes` | All activity | 5–120 | 10 |
| `daily_sentence_goal` | Conversation track — sentences studied | 1–200 | 10 |
| `daily_question_goal` | TOPIK track — questions attempted | 1–200 | 10 |

Users view progress against all three via `GET /dashboard/summary` (see §4.5); the response's `goals[]` array carries `current` and `target` for each, tagged with the relevant `track_id` for the per-track goals.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `GET /settings/me` | UI preferences and daily goals |
| `PUT /settings/me` | Update UI preferences and/or daily goals |
| `GET /me/learning` | Read `current_level` per track (see 4.6) |
| `PATCH /me/learning/{track_id}` | Change `current_level` in a track (see 4.6) |

**Business rules**

- Language change is propagated to `users.language` automatically.
- `daily_goal_minutes` bounded 5–120. `daily_sentence_goal` and `daily_question_goal` bounded 1–200. Out-of-range values return `422 validation_error`.
- Manual level changes delegate to `PATCH /me/learning/{track_id}`. Users may move up or down freely. Any such change **resets the in-flight promotion progress** on that track, so auto-promotion re-evaluates from scratch at the new level (see 4.6).

---

### 4.18 Recommendations (`recommendations`)

The primary surface for track content. **Both sentences and TOPIK questions are AI-generated** — every response is synthesized on demand, not pulled from a static catalog. Every recommendation is **grounded in the user's `current_level`** for the requested track; there is no separate "prompt-based mode". The client may additionally attach a free-form `prompt` that **refines** the recommendation (topic, scenario, grammar focus) within that level.

**On-screen prompt input**

On study screens, next to the content card, there is a prompt input field with a send button (visually and functionally distinct from the top-right chatbot icon, which drives the AI chat — see 4.10). Typing a request (e.g. "sentences for ordering food") and pressing send re-calls `POST /recommendations/sentences` (Conversation) or `POST /recommendations/questions` (TOPIK) with the user's `current_level` plus the typed prompt; the response replaces the current feed.

If the user submits an empty prompt, the server regenerates at `current_level` with no extra constraint.

**Endpoints**

| Method & Path | Purpose |
|---|---|
| `POST /recommendations/sentences` | Conversation-track recommendation — returns sentences (body: `{level?, prompt?, count?}`) |
| `POST /recommendations/questions` | TOPIK-track recommendation — returns quiz questions (body: `{level?, prompt?, count?}`) |
| `GET /recommendations/history?kind=sentences\|questions&cursor=` | Recently recommended items (for "again"/"similar" follow-ups) |
| `POST /recommendations` | Legacy internal recommender kept for backward compatibility with the initial project setup. New clients should use the sentences / questions endpoints above. |

**Business rules**

- `level` is always applied. If `level` is omitted, the server substitutes the caller's `current_level` in the target track; clients should not send a level that differs from the user's current level unless they are intentionally previewing another difficulty.
- `prompt` is an optional refinement. When present, the AI generates items that satisfy the prompt **while still respecting `level`**; when absent, the AI generates level-appropriate items using recent history as a signal.
- `prompt` is capped at 500 chars and moderated before being sent to the LLM.
- `count` defaults to 5, max 20.
- Items returned by `/recommendations/questions` use the same `QuizQuestion` shape as §4.8; attempts are submitted through the quiz attempt endpoint.
- Items returned by `/recommendations/sentences` use the same `Sentence` shape as §4.7 and always include:
  - the nested `audio` object (AI-generated TTS — signed URL, format, duration, `expires_at`); clients cache the file locally for the replay button and only call `GET /sentences/{sentence_id}/audio` to refresh after expiry.
  - `translation` + `translation_language` in the caller's `users.language`, so the UI can show the Korean line and its meaning side by side without an extra localization call.
- Bookmarks, listen events, and speech attempts flow through the sentence endpoints.

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
| **Recommendation** | AI-generated content — sentences for Conversation, questions for TOPIK. Always grounded in the user's `current_level`; an optional `prompt` refines the request within that level. |
| **Lecture** | Supplemental video / reading / listening unit, primarily for TOPIK; does not affect auto-promotion. |
| **Sentence** | Smallest studyable item with audio and grammar tags. |
| **Quiz** | MCQ / fill-blank / typing / ordering / listening. |
| **Attempt** | A single submitted answer on a quiz. |
| **Streak** | Consecutive days the user hit their daily goal. |
| **Tier** | League position: Green → Lime → Yellow → Orange → Golden. |
| **Group** | Set of 30 users inside a tier, matched by activity level; rankings are scoped to groups. |
| **Season** | Weekly cycle in US Eastern Time (Mon 00:00 ET → Sun 21:00 ET) that closes with promote / maintain / demote and a point reset. |
| **HangulAI (한글AI)** | On-demand AI conversation partner. |
