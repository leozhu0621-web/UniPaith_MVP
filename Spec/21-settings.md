# 21 · Settings (Student + Institution)

> Account, security, locale, notification preferences, data-rights entry, and account deletion — for both roles. The dedicated home for the surfaces previously sketched in `05` §10. Routes: `/s/settings` (student, under the avatar dropdown) and `/i/settings` (institution).
>
> Status: **draft v1.0** · 2026-05-29 · Supersedes the `05` §10 table (which now points here). Gives `/s/settings` + `/i/settings` a dedicated build contract (previously a section in `05` §10).

---

## 1. Purpose

One predictable place for everything that isn't the product surface itself: who you are, how you sign in, how you're notified, what language/timezone you see, and how you leave. Notification preferences live **here**, not on Profile (one-place-for-notifications principle, `05` §6.6).

---

## 2. Student settings (`/s/settings`)

Vertical sections (each a card), in order:

### 2.1 Account
- Email (primary), role, member-since (read-only).
- Change email (Cognito flow — re-verify the new address).
- Profile photo / display name (the only identity bits that live in Settings; the durable record is `08`).

### 2.2 Security
- **Password change** — Cognito API. Current + new + confirm; strength meter.
- **MFA / 2FA** — Cognito MFA enroll/disable (TOTP; SMS optional). Recovery codes on enroll.
- **Active sessions** — list devices/sessions; "sign out everywhere."
- **Login activity** — recent logins + `login_risk_events` (`42` §3.17) surfaced read-only.

### 2.3 Preferences
- **Locale** (language) — drives `preferred_platform_writing_language` (`42` §3.1).
- **Timezone** — drives all deadline/calendar normalization (`16`, `42` §4.1 `timezone_normalized_deadline_calendar`).
- **Accessibility** — dyslexia-friendly mode, font size, reduced-motion (`03` §9, `42` §3.1 accessibility fields).
- **Theme** — light / dark / system (`01` dark theme).

### 2.4 Notifications
The Universal-Profile "Notifications" section (Master Paper §15) lives here. Per-channel × per-type matrix:
- Channels: email, SMS/WhatsApp (opt-in), in-app, push.
- Types: match updates, application missing-item, interview invites, deadline reminders, decisions, institution posts on saved programs (`17`/`20`/`16` triggers, mapped in `05` §12).
- Email frequency: all / weekly digest / important only / none (`42` §3.1).
- Each toggle persists to the student's notification-prefs; transactional/active-application messages can be down-ranked but not fully silenced (safety — see `29` §6).

### 2.5 Data & privacy (entry point)
- The full consent panel + portable export + access log live on **Profile → Data tab** (`08` §16, `46` §8). Settings shows a summary + a "Manage data rights →" link there (avoid two sources of truth).
- **Account deletion** — "Danger zone" card: triggers soft-delete + 30-day grace + full purge (`46` retention). Requires re-auth + typed confirmation.

### 2.6 Sign out
- Sign out (this device) + "sign out everywhere."

### 2.7 Billing (student, if subscribed)
- Plan status ($15/mo + trial state, `07` §4.1), card-on-file, invoices, cancel/downgrade, ad-free upgrade toggle. (Payments provider integration — Phase-2 detail; MVP shows plan state + manage link.)

---

## 3. Institution settings (`/i/settings`)

### 3.1 Account & team
- User account info; role within the institution.
- **Team / seats** — list staff, invite, role assignment (admissions / recruiter / marketing / IT), deactivate. Audit-logged (`36`). (Multi-institution switching is post-MVP, `05` §5.)

### 3.2 Institution profile basics
- Pointer to the full public profile editor (`22`); Settings holds only org-level account fields (legal name, billing contact, primary domain for SES/links).

### 3.3 Review configuration
- **Rubric management** — define/edit the scoring rubric used in `32` (criteria, weights, scales).
- **Blind-review default** + **calibration settings** (`32` §7A.1/§7A.2) toggles at the institution level.
- Reviewer-assignment defaults.

### 3.4 Integrations
- **Credentials** for SIS/CRM (Slate, Salesforce, Banner/Workday) + API webhooks (`06` §4; most deferred to Phase-2 per `49`).
- SES sender domain verification status (`25`).
- Data export / dataset access (`24`).

### 3.5 Notifications (institution)
- Per-type institution alerts (new inquiry, new application, reviewer overdue, yield-risk, disparate-impact threshold — `05` §12, `46` §6) × channel.

### 3.6 Billing
- Usage-based billing ($15/applicant, `07` §4.2): current cycle usage, invoices, payment method, plan/add-ons.

### 3.7 Security
- Password / MFA (as §2.2); SSO for staff is a Phase-2 consideration.

---

## 4. Data shape

```ts
type UserSettings = {
  account: { email: string; display_name: string; photo_url: string | null };
  security: { mfa_enabled: boolean; mfa_method: 'totp' | 'sms' | null };
  preferences: {
    locale: string; timezone: string; theme: 'light' | 'dark' | 'system';
    accessibility: { dyslexia_mode: boolean; font_size: 'sm'|'md'|'lg'|'xl'; reduced_motion: boolean };
  };
  notifications: Array<{ type: string; channels: { email: boolean; sms: boolean; in_app: boolean; push: boolean } }>;
  email_frequency: 'all' | 'weekly' | 'important' | 'none';
};
```

Endpoints:
- `GET /me/settings` · `PATCH /me/settings`.
- `POST /me/settings/change-password` · `POST /me/settings/mfa/{enroll,disable}` · `GET /me/settings/sessions` · `POST /me/settings/sessions/revoke`.
- `POST /me/account/delete` (starts grace) · `POST /me/account/delete/cancel`.
- Institution: `GET/PATCH /i/settings`, `GET /i/settings/team`, `POST /i/settings/team/invite`, `PATCH /i/settings/rubric`, `GET/PATCH /i/settings/integrations`.

Most fields map to `42` §3.1/§3.2 (contact, accessibility, consent, communication prefs) — Settings is a focused editor over a subset of the Prompt Library + Cognito-managed auth fields.

---

## 5. States

- **Loading:** section skeletons.
- **MFA enroll:** QR + recovery codes modal; confirm before enabling.
- **Email change:** "Check your new inbox to confirm" pending state.
- **Account deletion:** typed-confirmation + re-auth gate; then "Scheduled for deletion on <date> · Undo."
- **Save:** inline per-section save with optimistic UI + toast; errors revert.

---

## 6. Brand compliance

- Plain, dense, editorial — no decorative imagery.
- Danger-zone card uses `--danger` border/text only (no full-red fill); destructive buttons require confirmation.
- **No gold** anywhere in Settings (utility surface, not a brand/celebration moment).
- Toggles + inputs per `02` component rules; respects dark theme + `03` mobile (single-column, sticky save).

---

## 7. Gaps (relative to current code)

- Settings exists today as a thin page; this spec is the contract for the full surface.
- Password change / MFA / locale / timezone / deletion are TODO in the current build (`05` §10 marked them TODO).
- Notification-prefs matrix is NEW; backend notification-prefs store required.
- Institution team/seats + rubric config + integrations are partially present (rubric in `32`); consolidate here.

---

## 8. Tests

- Notification toggle persists + governs delivery (cross-check `05` §12 triggers).
- Password change + MFA enroll/disable round-trip via Cognito.
- Timezone change re-normalizes calendar deadlines (`16`).
- Account deletion → 30-day grace state + undo; purge after grace (`46`).
- Data-rights link routes to Profile Data tab (no duplicate consent UI).
- Role scoping: student cannot see institution settings + vice-versa.

---

## 9. Copy

- "Account" / "Security" / "Preferences" / "Notifications" / "Data & privacy" / "Danger zone".
- "Sign out everywhere".
- "Manage data rights →" (links to Profile → Data).
- "Scheduled for deletion on <date> · Undo".
- "Check your new inbox to confirm your email."

---

## 10. Open questions

- **Notification prefs storage.** Own table vs JSONB on profile — recommend a `notification_preferences` table keyed by (user, type, channel) for queryability.
- **Student billing UI depth.** MVP: plan state + manage link; full invoice history Phase-2.
- **SSO for institution staff.** Deferred; capture provider preferences when an enterprise customer requires it.
- **Data-rights split.** Consent lives on Profile Data tab; deletion lives in Settings. Confirm this split reads well to users, or consolidate both under Settings.
