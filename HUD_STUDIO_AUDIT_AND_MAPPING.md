# HUD + Hollywood Studio — pre-implementation audit, inventory and mapping (PATCH3 lineage)

Baseline = PATCH3 release `KILCRITIC_KORA_10.5.0_PATCH3_GROWTH_SECURITY_HARDENING.zip` (169/169 PASS). VERSION unchanged. KORA 8.8.5 foundation preserved.
Evidence below comes from reading the extracted tree and from a live probe: `python3 run.py` on port 18080 with a temp DB (no credentials), `curl` against `/`, `/advanced`, `/api/*`.

## 1. Which screen does the user actually see?
`python3 run.py` (README) serves the Python bridge. Its static map (`kora/bridge/api.py` `STATIC`):

| URL | File | What it is |
|---|---|---|
| `/` | `kora/hud/creator_index.html` + `creator.js` + `creator.css` | **the mounted default screen**: "Creator desktop" (full-body avatar JPG, one folder button, drag-icons, category grid) |
| `/advanced`, `/legacy-hud` | `kora/hud/index.html` + `hud.js` + `hud.css` | the 10.2.1 "holographic HUD": face state, command box, task/approvals activity, Doctor/Backup/Improve Me, Advanced drawer |
| (not served by Python) | `src/App.tsx`, `src/components/KoraFaceHud.tsx`, `MediaSocialStudioHub.tsx` (React/Vite via `server.ts`) | third UI; README: "legacy React src (could not be built)" |

## 2. Root cause: why the HUD repair never changed the visible screen
1. **Three UIs, repairs landed on the non-default ones.** The 10.2.1 HUD repair (face state, command box, task panel, approvals) lives in `hud.js`/`index.html`, but since the creator-desktop change `/` points at `creator_index.html`; the HUD became `/advanced`. The React `KoraFaceHud.tsx` is only rendered inside React's Advanced section and is not served by `run.py` at all.
2. **The mounted screen (`creator.js`) has no task state, no command box on the home view, no task/activity panel, no error recovery view, no approval view and no access to Doctor/Backup/Improve Me** — only a link to `/advanced`.
3. **No test exercised the mounted screen.** Existing tests only assert `GET /` and `GET /hud.js` return 200 (`pro_tests.py:585`); nothing asserts what `/` contains or that its controls work, so "fixed" could not be falsified.
4. Ruled out: stale cache (every response has `Cache-Control: no-store`; the React `sw.js` is network-first and is not registered by `creator_index.html`), stale build (no `dist/` shipped; Python UI is not built), CSS override (`creator.css` and `hud.css` are separate pages), API errors (probe: `/api/brain` answers OK on loopback without a token; empty token = loopback owner only).
5. The React footer still claims "SUPREME 10.2.2" and "75/75 Core Tests Passing" (hard-coded, not measured). Legacy; not served; reported, not part of the mounted path.

## 3. Inventory (status vs. the master spec)
Legend: OK = EXISTS AND WORKS; BROKEN; DISC = EXISTS BUT DISCONNECTED; PART = PARTIALLY IMPLEMENTED; MOCK; MISSING; HEAVY = OPTIONAL HEAVY DEPENDENCY.

| Feature | Status | Where / evidence |
|---|---|---|
| Full-screen responsive home with avatar | PART | `creator_index.html` (`.hero`, `body-avatar`), safe-area `viewport-fit=cover` meta present but no `env(safe-area-inset-*)` in CSS |
| Truthful state (IDLE/LISTENING/THINKING/WORKING/NEEDS APPROVAL/ERROR/COMPLETE) | PART | `creator.js` only READY/THINKING/LISTENING; `hud.js` has IDLE/WORKING/THINKING/LISTENING/SAFE MODE/FROZEN/OFFLINE/ERROR from `/api/active` |
| Command input on main view | DISC | exists in workspace only (`#commandForm`) and in `/advanced` |
| Task/activity panel, current task, approvals | DISC | `hud.js` + `/api/active` (OK); absent from `/` |
| Voice | PART | browser SpeechRecognition in both UIs (`creator.js voice()` lang en-IN only; `hud.js` pa-IN default); backend `/api/voice`, `voice_stt.py`; no provider needed for browser STT but support is browser-dependent |
| Shared dispatcher for voice/text/touch | OK (backend) | `POST /api/brain` → `brain.handle` (touch is "the SAME command path"); frontends call it separately, no shared UI task state |
| Floating glass buttons / back / minimize / resume | PART | `.glass` buttons, `← Desktop`; no minimize/resume, no checkpoints |
| Task checkpoints survive menu change | MISSING | no state persistence in `creator.js` (only icon positions) |
| Media + Social + Studio folder | PART | `#masterFolder` → workspace with 12 category buttons; each only POSTs "Open X workflow" to `/api/brain` and shows a plan-only message (`brain.py:46-76`) |
| Hollywood Studio create (video generation) | MISSING / NOT_IMPLEMENTED | `hollywood_studio.py` = planning contracts; `brain.py:49` states NOT_IMPLEMENTED |
| 3D/4D/5D, cartoon/animation generation | MISSING (no engine) → shown as OPTIONAL HEAVY / future | no renderer in tree |
| Import media | MISSING | no upload route (API is JSON-only, 1 MB default) |
| Preview/play/pause/seek/stop | MISSING | no player anywhere in `kora/hud`; CSP also lacks `media-src`/`blob:` |
| Trim/split/crop/rotate/resize/aspect | MISSING | only `convert_variant` (4 fixed platform sizes) |
| Text overlay, filters, brightness/contrast, audio volume/fade, watermark | MISSING | `subtitles.burn_subtitles` OK (SRT burn-in) |
| Quality check | OK | `media_pipeline.verify_quality` (ffprobe, measured) |
| Platform variants | OK | `convert_variant`, `asset_compiler.compile_variants`, `POST /api/media/convert` |
| Subtitles | OK | `subtitles.py` (SRT validate/generate/burn) |
| Media rights / dedup | OK | `media_rights.py`, `media_dedup.py` |
| Draft save / reopen / undo-redo | MISSING | no project store for edits |
| ffmpeg/ffprobe | HEAVY (optional external) | present in this sandbox; code returns `UNAVAILABLE` when absent |
| Social create/approve/reject | OK (mock transports in tests) | `/api/social/posts*`; platforms `AUTH_REQUIRED` (no creds) per `/api/platforms/readiness` |
| Real publishing to YouTube/FB/IG/TikTok/X | NEEDS CREDENTIALS; live-verified: none | `/api/capabilities` → `READY_WITH_EXTERNAL_SETUP`, `live_verified:false` |
| Amazon posting | NOT_IMPLEMENTED (no adapter) | not in `platform_readiness`; UI must say so |
| Search / Discover / live trends | PART | `/api/research/search` needs a provider; no trend source → "NO SOURCE" |
| Growth / analytics | OK (evidence-gated) | `/api/growth/*` |
| 30-day Autopilot / schedule | OK | `/api/autopilot/schedules`, `/calendar`; creator.js has Schedule modal |
| Advanced/System: Health/Doctor, Backup, Improve Me, Resources, Discovery | OK in `/advanced` (hud.js) | `/api/doctor/*`, `/api/backup/create`, `/api/evolution/*`, `/api/ops`, `/api/providers` |
| Events, Tests, audit, Offline queue | PART | endpoints exist (`/api/active`, `/api/tests/run`, queue stats); only React tabs show them |
| Show/hide/pin/reorder controls | PART | `creator.js` drawer + drag icons (hide never deletes) |
| Content audience modes (Kids/General/Adult) | OK backend | existing legal/audience preflight (growth/legal_guard, auto_post_legal) — UI must not bypass |

## 4. Mapping: requested feature → existing implementation → action → regression test
| Requested | Existing (reuse) | Required action | Test |
|---|---|---|---|
| One full-screen HUD at `/` showing face, state, command box, task panel | `creator_index.html/js/css` (mounted) + task data `/api/active` from `hud.js` logic | **repair `creator_*` in place**: add status badge, always-visible command bar, task/activity panel (from `/api/active`), floating glass buttons around the avatar; keep `/advanced` untouched | T170 mounted-HUD static+live (served `/`, required element ids, JS references) |
| Same state machine for voice/text/touch | `/api/brain` + `creator.js command()` | single `dispatch(text, source)` in `creator.js`; touch/voice/text all call it; local UI intents map to UI actions; publish/purchase never executed locally | T171 dispatcher (Node/py harness of the pure intent function) + route contract |
| Advanced/System keeps Health/Doctor, Discovery, Backup, Improve Me, Voice, Events, Tests, audit | `hud.js` actions + endpoints | add an **Advanced / System panel inside the mounted screen** whose buttons call the same real endpoints; keep the full `/advanced` link | T172 every Advanced control present and mapped to a registered route |
| Unified Media+Social+Studio folder | existing master folder + categories | make categories open real tools; replace plan-only dead-ends with Studio panel; unavailable engines labelled | T173 every visible control has handler or `disabled`/NOT IMPLEMENTED label |
| Import, library, preview player | none | new `/api/studio/upload|assets|file` (chunked JSON/base64, confined to `data/media/library`), `<video>/<audio>/<img>` bound controls; CSP `media-src 'self' blob:` + `img-src blob:` | T174 real fixture upload→list→preview bytes→ffprobe |
| Edit ops (trim, crop, rotate, resize, aspect, text, brightness/contrast, filter, volume, mute, fade) | `media_pipeline` ffmpeg conventions (fixed argv, no shell, root-confined, ffprobe-verified output) | **extend `media_pipeline.py`** with `edit_media` (one engine, no new media module); `/api/studio/edit` | T175 real ffmpeg fixtures: each op measured by ffprobe; invalid params rejected; ffmpeg-missing → UNAVAILABLE |
| Export presets, quality check | `CONVERT_TARGETS`, `verify_quality` | reuse; add compressed/preview presets | T175/T176 |
| Draft autosave/reopen/undo-redo | none | project JSON store in `hollywood_studio.py` + client undo stack | T176 save→reopen round-trip |
| Create-to-post separation (preview ≠ publish), approval | `/api/social/posts` (PENDING_APPROVAL), `autopilot` | UI "Save draft / Request approval" calls `/api/social/posts`; no direct publish button; `NEEDS APPROVAL` state | T177 UI contains no direct-publish call; social create stays pending |
| Heavy features (3D/4D/5D, AI video) | — | shown as OPTIONAL HEAVY / NOT_IMPLEMENTED with requirements; no fake generation | T173 |
| Security | auth, rate limits, CSP | owner-only by default (routes absent from `ROUTE_PERMS`), path confinement, ext allowlist, size caps, no secrets | T178 traversal/ext/size/auth |

Out of scope / untouched: KORA core, Guardian, auth, approval gates, schemas, learning memory, credentials, VERSION, React `src/` (cannot be built here: npm registry returns HTTP 403 from the session proxy — BLOCKED, not retried).

## 5. Outcome (after implementation)
| Feature | Final status | Evidence |
|---|---|---|
| Mounted `/` HUD (state, command bar, task panel, ring, Advanced) | IMPLEMENTED & TESTED | T170, T173; real Chromium run `scripts/ui_mounted_check.py` (mobile 390x780 + desktop 1280x800) |
| Voice/text/touch one dispatcher | IMPLEMENTED & TESTED (voice recognition itself: browser-dependent, NOT TESTED with a real microphone) | T171; dispatch('…','voice') exercised in browser |
| Advanced/System (Doctor, Discovery, Backup, Improve Me, Resources, Events, Audit, Tests, Voice, token) | IMPLEMENTED & TESTED | T172; browser: Doctor + Audit chain |
| Studio import / library / preview / play / pause / seek / stop / mute | IMPLEMENTED & TESTED (WebM in real Chromium) | T174; H.264 NOT decodable in headless Chromium (shown honestly); should work on phone browsers with H.264 — NOT VERIFIED there |
| Edits: trim, crop/aspect, rotate, resize, color/filter, text, audio, export presets | IMPLEMENTED & TESTED (ffprobe-measured) | T175 |
| Drafts, undo/redo, quality check | IMPLEMENTED & TESTED | T176; browser |
| Save for approval (never publish) | IMPLEMENTED & TESTED | T177; browser |
| Real publishing to YouTube/FB/IG/TikTok/X | NEEDS CREDENTIALS (unchanged, not verified live) | `/api/platforms/readiness` AUTH_REQUIRED |
| Amazon posting, 3D/4D/5D, generative video, multi-track, cloud render, 4K | NOT IMPLEMENTED / OPTIONAL HEAVY (labelled in UI) | `studio_capabilities().not_implemented` |
| Live trends | NO SOURCE (none claimed) | — |
| Frontend build of legacy React `src/` | BLOCKED (npm registry 403 via session proxy) | `curl` through proxy: 403 |
