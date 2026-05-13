# Vitacora - ColePago / KidWall

## Tracking Rule

- This file is the running project catalog for ColePago/KidWall work.
- Every meaningful change should be added here with:
  - date
  - files changed
  - architecture impact
  - verification performed
  - pending or risky items
- Do not store live passwords, tokens, API keys, private keys, or full secrets in this file.

## Current Implemented Architecture

### High-Level System

ColePago/KidWall is being shaped as a role-based wallet and school safety platform.

The same mobile APK should serve both parents and merchants. The backend stores users with a role:

- `parent`
- `merchant`

The app should authenticate the user once, then route them to a role-specific experience:

- Parent dashboard:
  - children
  - wallet deposits
  - trusted/alternate contacts
  - child safety alerts
  - route/location monitoring
- Merchant dashboard:
  - receive kid payments
  - confirm virtual coin/payment requests
  - view receivable balance
  - configure payout method
  - request/track payouts

### Backend API Layer

Primary backend code is in:

- `main.py`
- `colepago/api/router.py`
- `models.py`

The backend uses:

- FastAPI for API endpoints
- SQLAlchemy models for persistence
- PostgreSQL as the database
- Alembic for one-time schema migrations
- `.env` for runtime configuration

Current API responsibilities include:

- registration with role support
- parent profile management
- trusted/alternate contact management
- wallet funding
- child purchase confirmation
- child route/location monitoring
- urgent parent/contact escalation
- merchant payout method and payout preparation

### Database And Migrations

Alembic is used to apply controlled database schema changes.

Important current migration head:

- `e5f6a7b8c9d0`

Recent migrations added:

- parent username and address detail fields
- payment gateway ledger tables
- external payment records
- external payout records
- merchant payout method records

Alembic does not run continuously. It applies each migration once, then records the current revision in the database table:

- `alembic_version`

### Identity And Roles

Users are stored in the `users` table.

Important fields:

- `name`
- `username`
- `email`
- `password_hash`
- `role`
- `balance`

Current roles:

- `parent`
- `merchant`

Password hashing was changed from the failing `passlib` bcrypt path to direct `bcrypt` usage in the active API router.

### Parent Profile And Contacts

Parent profile data is stored separately from the core user record.

Main profile table:

- `parent_profiles`

Trusted/alternate contacts table:

- `emergency_contacts`

The model keeps the table name `emergency_contacts` for backward compatibility, but the application language is moving toward trusted or alternate contacts.

Parent profile now supports:

- relationship to child
- home address
- floor
- department
- home postal code
- home phone
- mobile phone
- country code
- work name
- work address
- work postal code
- work phone
- work shift
- work hours
- workplace
- notification email

### Notification Architecture

Email is configured through EasyDNS SMTP.

Files:

- `email_utils.py`
- `colepago/email_utils.py`

Automatic child safety alerts now send email to:

- parent account email
- parent profile email
- trusted/alternate contact emails

Duplicate email addresses are filtered before sending.

WhatsApp and voice call support is handled through Twilio helper code:

- `whatsapp_utils.py`

SMS is not implemented yet, but should be added as another Twilio channel.

### Payment Gateway Architecture

The project now has the first version of a provider-neutral payment gateway layer.

File:

- `services/payment_gateway.py`

The gateway layer is responsible for normalizing money movement before connecting to Mercado Pago, Stripe, or manual bank transfers.

Implemented gateway operations:

- record parent deposit
- record child purchase
- create merchant payout method
- prepare merchant payout
- create ledger accounts on demand
- post balanced ledger transactions

The current gateway does not yet execute real Stripe/Mercado Pago payouts. It records the internal ledger and prepares the payout records that provider adapters will later execute.

### Ledger Architecture

The ledger is intended to become the financial source of truth.

Core tables:

- `ledger_accounts`
- `ledger_transactions`
- `ledger_entries`

Supporting external money tables:

- `external_payments`
- `external_payouts`
- `merchant_payout_methods`

Ledger design:

- Each ledger transaction must balance to zero.
- Parent wallet deposits create ledger entries.
- Kid purchases debit the parent wallet.
- Merchant receivables are credited.
- ColePago fee revenue is credited.
- Merchant payouts debit merchant receivables and create payout records.

Example child purchase flow:

- parent wallet: debit full purchase amount
- merchant receivable: credit purchase amount minus ColePago fee
- platform fee account: credit ColePago commission

The current `users.balance` field still exists and is updated as a cached/display balance. Long term, ledger balances should become the authoritative source.

### Payment Provider Strategy

The system should support multiple providers through adapters.

Planned providers:

- Mercado Pago
- Stripe
- manual bank transfer

Recommended direction:

- Mercado Pago for Argentina-first marketplace flows.
- Stripe Connect for card deposits and connected merchant payouts where available.
- Manual bank transfer for fallback or admin-controlled payouts.

Provider adapters should eventually handle:

- deposit creation
- webhook verification
- deposit confirmation
- payout creation
- payout status refresh
- refunds
- reconciliation

### Ingress, Gateway, And Kubernetes Direction

Ingress and gateway are separate layers.

Ingress:

- public HTTPS front door
- TLS termination
- hostname/path routing into Kubernetes

Payment gateway:

- business/payment orchestration layer
- provider normalization
- idempotency
- ledger posting
- webhook normalization
- payout preparation

Recommended initial public routing:

- `https://api.drsrv.net.ar/api`
- `https://api.drsrv.net.ar/payments`
- `https://api.drsrv.net.ar/webhooks`

Internal service-to-service security can later use:

- internal TLS
- mTLS
- service mesh
- signed service tokens

### School Data Direction

The user plans to provide a complete US schools list.

Existing table:

- `schools`

Pending import work:

- define import format
- normalize school names and addresses
- deduplicate schools
- geocode or preserve provided coordinates
- add search/filter endpoint
- connect children to selected schools

### US School Data Sources Researched

Recommended authoritative sources for a complete US K-12 school dataset:

- Public schools:
  - NCES Common Core of Data (CCD) Public Elementary/Secondary School Universe.
  - Use the latest CCD Universe Files, currently 2024-25 Version 1a.
  - This is the primary public source for all US public elementary and secondary schools.
  - Source: `https://nces.ed.gov/use-work/dataset/2024-25-common-core-data-ccd-universe-files-version-1a`
- Private schools:
  - NCES Private School Universe Survey (PSS).
  - Latest public-use downloadable file currently available on the NCES PSS data page is 2021-22; 2023-24 is listed as being finalized for spring 2026.
  - Source: `https://nces.ed.gov/surveys/pss/pssdata.asp`
- Geocoded public school point locations:
  - NCES EDGE Public School Locations.
  - Useful for latitude/longitude and map/search features.
  - Current public school location layer is available through ArcGIS/NCES EDGE.
  - Source: `https://www.arcgis.com/home/item.html?id=4c5425750a334373921cd87560c276d5`

Import strategy:

- Import CCD first for public schools.
- Import PSS second for private schools.
- Optionally enrich public schools with EDGE latitude/longitude data.
- Keep NCES IDs as external stable identifiers.
- Store source year and source dataset for every imported school.

### US School Import Completed

- Downloaded NCES school datasets into:
  - `data/schools/ccd_public_2024_25_prelim.zip`
  - `data/schools/edge_public_2024_25.zip`
  - `data/schools/edge_private_2023_24.zip`
- Extracted public CCD directory data:
  - `data/schools/ccd_public_2024_25_prelim/ccd_sch_029_2425_w_0a_051425.csv`
- Extracted public EDGE geocode data:
  - `data/schools/edge_public_2024_25/EDGE_GEOCODE_PUBLICSCH_2425.TXT`
- Extracted private EDGE geocode data:
  - `data/schools/edge_private_2023_24/EDGE_GEOCODE_PRIVATESCH_2324.dbf`
- Added school import fields to the database:
  - `source`
  - `source_year`
  - `external_id`
  - `sector`
  - `district_id`
  - `district_name`
  - `postal_code`
  - `website`
  - `level`
  - `low_grade`
  - `high_grade`
  - `locale_code`
  - `county_name`
- Added migration:
  - `alembic/versions/f6a7b8c9d0e1_add_nces_school_import_fields.py`
- Added importer:
  - `import_us_schools.py`
- Imported records into `schools`:
  - Public schools: `101,333`
  - Private schools: `22,510`
  - Combined US school records imported: `123,843`
  - Distinct state/territory codes observed: `56`
- Current Alembic head after import:
  - `f6a7b8c9d0e1`
- Verification:
  - Syntax checks passed.
  - Import completed successfully.
  - Sample public schools include coordinates and level values.
  - Sample private schools include coordinates.

School import notes:

- Public school core directory data comes from NCES CCD 2024-25 preliminary directory.
- Public school coordinates are enriched from NCES EDGE 2024-25 public geocode file.
- Private school records come from NCES EDGE 2023-24 private geocode file because it exposes clean directory/geocode columns.
- The downloaded PSS methodological frame CSV only had tracking fields and was not used for the main private-school import.
- The user's open `pss2122_pu.csv` was inspected but not needed for this first import because EDGE private geocodes provided direct school identity/address/location fields.

## Work Log

### 2026-05-11

#### Deployment File Note

- Confirmed that `D:\kidwall\.github\workflows\deploy_all.yml` does not exist anymore.
- Do not reference that GitHub Actions workflow as an active deployment path.
- Current deployment/start files observed at the project root include:
  - `deploy_all.ps1`
  - `colepago-backend-deployment.yaml`
  - `colepago-backend-ingress.yaml`
  - `deploy_wallet_stack.sh`
  - `start-all.ps1`
  - `start-quick.ps1`
  - `restart-all.bat`
  - `stop-all.bat`
- Pending:
  - Decide whether deployment should be managed by local PowerShell scripts, Kubernetes manifests, or a recreated GitHub Actions workflow.

#### Windows Python3 Compatibility

- Found Windows host has `python.exe` and `py.exe`, but no `python3.exe` on PATH.
- Added local app shim:
  - `colepago-parents-app/tools/python3.cmd`
- Updated build scripts to prepend the app `tools` directory to PATH:
  - `colepago-parents-app/build_both_apks.ps1`
  - `colepago-parents-app/build_kids_apk.ps1`
- Updated VS Code terminal environment for the app:
  - `colepago-parents-app/.vscode/settings.json`
- Fixed stray plain-text line in `build_kids_apk.ps1`.
- Verification:
  - `python3 --version` resolves through the local shim and reports Python 3.14.2.
  - VS Code settings JSON parses successfully.

#### Postgres Deployment Port Conflict

- Deployment failed because `postgres_colepago` already owned host port `5432`.
- `docker-compose up -d db` tried to start `kidwall_db` on the same port, leaving `kidwall_db` in `Created` state.
- Backup then targeted `kidwall_db`, which was not running.
- Updated `deploy_all.ps1`:
  - detects a healthy running `kidwall_db` first
  - otherwise detects a healthy container published on `5432`
  - reuses that container for readiness checks and `pg_dump`
  - aborts clearly if no ready database is found
  - reports the actual database container in the deployment summary
- Verification:
  - `postgres_colepago` accepts connections for user `colepago`.
  - Database `colepago` is present.
  - PowerShell syntax parse passed.

#### Parent App Navigation And Backend Auth

- Wired parent dashboard drawer item `Parent Config` to the existing profile form:
  - `colepago-parents-app/lib/screens/parent_dashboard_screen.dart`
- Added backend auth compatibility for the Flutter app:
  - `POST /api/auth/login`
  - registration now returns the same auth payload shape Flutter expects
  - payload includes `token`, `access_token`, `token_type`, `id`, `user_id`, `parent_id`, `role`, `name`, and `email`
- Files changed:
  - `colepago/api/router.py`
  - `colepago-parents-app/lib/screens/parent_dashboard_screen.dart`
- Verification:
  - `dart analyze` passed for the Flutter app.
  - Python compile check passed for `colepago/api/router.py`.
  - FastAPI route check confirmed `/api/auth/login` and `/api/auth/register` are mounted.
- Pending:
  - Replace placeholder generated bearer token with durable signed auth if/when protected endpoints enforce authorization.
  - Add role-based navigation for merchant users.

#### Merchant Information Profile

- Added merchant profile data model and migration:
  - `models.py`
  - `alembic/versions/g7h8i9j0k1l2_add_merchant_profiles.py`
- Merchant profile fields:
  - place scope: within school / outside school
  - business name
  - address for outside-school merchants
  - personal contact name
  - mobile phone
  - country code
  - transfer account type: CVU / CBU
  - transfer account value
  - transfer account alias
- Added backend endpoints:
  - `GET /api/merchant/{merchant_id}/profile`
  - `PUT /api/merchant/{merchant_id}/profile`
- Added Flutter merchant UI:
  - `merchant_dashboard_screen.dart`
  - `merchant_profile_form_screen.dart`
- Updated Flutter auth flow:
  - login/register callback now carries user role
  - merchant users route to merchant dashboard
  - parent users keep the existing parent first-time/profile flow
- Verification:
  - Alembic migration applied to the active local PostgreSQL database.
  - Verified `merchant_profiles` table columns in PostgreSQL.
  - Python syntax check passed for changed backend files.
  - `dart analyze` passed.
- Follow-up:
  - Added optional CVU/CBU alias support:
    - `transfer_account_alias`
    - `alembic/versions/h8i9j0k1l2m3_add_merchant_transfer_alias.py`
  - Applied the alias migration to the active local PostgreSQL database.
  - Verified Alembic DB revision is `h8i9j0k1l2m3`.
- Pending:
  - Connect CVU/CBU profile data to the merchant payout method flow.

#### Parent Children Count Field

- Added one more parent profile field:
  - `children_using_colepago`
- UI label:
  - `How many children will use ColePago?`
- Language decision:
  - Use `children` for plural.
  - Avoid `childs`; it is not standard English.
  - `kids` is understandable but more casual than `children`.
- Files changed:
  - `models.py`
  - `colepago/api/router.py`
  - `colepago-parents-app/lib/screens/parent_profile_form_screen.dart`
  - `alembic/versions/i9j0k1l2m3n4_add_parent_children_using_colepago.py`
- Verification:
  - Alembic migration applied to active local PostgreSQL database.
  - Verified `parent_profiles.children_using_colepago` exists as integer.
  - Verified Alembic DB revision is `i9j0k1l2m3n4`.
  - Python syntax check passed.
  - `dart analyze` passed.

#### First-Time Child Setup Iteration

- Updated first-time parent setup so `children_using_colepago` drives child entry.
- Flow:
  - Parent completes profile.
  - App reads `children_using_colepago`.
  - Add-child screen iterates through that many child forms.
  - Progress is shown as `Child X of N`.
  - Setup completes only after the final child is saved.
- Updated:
  - `colepago-parents-app/lib/screens/first_time_screen.dart`
  - `colepago-parents-app/lib/screens/add_child_screen.dart`
- Verification:
  - `dart analyze` passed.

#### Child Home Data Inheritance

- Added child home inheritance support to reduce parent data entry.
- UI asks:
  - `Does this child live with you?`
- Behavior:
  - If yes, backend inherits `home_address` and `home_phone` from the parent profile.
  - If no, add-child form asks for the child's home address and optional home phone.
  - Backend rejects separate-home child creation without a child home address.
- Added child fields:
  - `lives_with_parent`
  - `home_address`
  - `home_phone`
- Added/updated backend endpoint:
  - `POST /api/parent/add-child`
- Files changed:
  - `models.py`
  - `colepago/api/router.py`
  - `colepago-parents-app/lib/screens/add_child_screen.dart`
  - `alembic/versions/j0k1l2m3n4o5_add_child_home_inheritance_fields.py`
- Verification:
  - Alembic migration applied to active local PostgreSQL database.
  - Verified child columns exist in PostgreSQL.
  - Verified Alembic DB revision is `j0k1l2m3n4o5`.
  - Restarted backend.
  - Created a test child with `lives_with_parent=true`; inherited parent home address and phone.
  - Verified `lives_with_parent=false` without child home address returns HTTP 400.
  - Python syntax check passed.
  - `dart analyze` passed.

#### Web Root Login App

- Replaced the root static marketing page with an app login/register page.
- Root URL now serves the ColePago app entry point instead of the selling/brochure page:
  - `http://api.drsrv.net.ar:8010/`
- Added functional browser flows:
  - parent login/register
  - merchant login/register
  - parent profile save
  - child creation with `Does this child live with you?`
  - merchant profile save with CVU/CBU and alias
- Updated:
  - `static/index.html`
  - `static/app.js`
  - `static/styles.css`
- Verification:
  - Root HTML returns HTTP 200.
  - Static JavaScript returns HTTP 200.
  - Static CSS returns HTTP 200.
  - Browser should be refreshed with cache bypass if old marketing assets remain cached.
- Note:
  - `node --check` could not run because Node.js is not installed on this host.

#### Production-Like Web And App Routing

- Restored the public brochure/marketing page at the root URL:
  - `http://api.drsrv.net.ar:8010/`
- Moved the browser test login/register app to:
  - `http://api.drsrv.net.ar:8010/app`
- Kept the real backend API under the same host:
  - `http://api.drsrv.net.ar:8010/api`
- This allows testing page, app, and API with one DNS entry and the same origin.
- Files changed:
  - `main.py`
  - `static/index.html`
  - `static/app.js`
  - `static/styles.css`
  - `static/portal.html`
  - `static/portal.js`
  - `static/portal.css`
- Verification:
  - Restarted the running backend process.
  - Confirmed `http://api.drsrv.net.ar:8010/` returns the public page.
  - Confirmed `http://api.drsrv.net.ar:8010/app` returns the login/register app.
  - Confirmed `http://api.drsrv.net.ar:8010/api/ping` returns `pong`.

#### Parent Country, Setup Completion, And Wallet Allocation

- Added country capture to the parent profile flow.
- Country now drives the default phone country code in:
  - Flutter parent profile form
  - `/app` browser test parent profile form
- Added parent profile database field:
  - `parent_profiles.country`
- Added migration:
  - `alembic/versions/k1l2m3n4o5p6_add_parent_country.py`
- Added backend dashboard/wallet endpoints:
  - `GET /api/parent/{parent_id}/wallet_summary`
  - `GET /api/parent/{parent_id}/children`
  - `GET /api/parent/{parent_id}/wallet_buckets`
  - `GET /api/child/{child_id}/wallet_buckets`
  - `GET /api/child/{child_id}/transactions`
  - `POST /api/wallet/allocate`
- Updated first-time setup completion:
  - after the last child is saved, the app returns to the parent dashboard
  - dashboard refreshes with wallet actions available
- Updated parent dashboard:
  - shows parent wallet balance
  - shows total applied to children
  - adds `Load Money`
  - adds `Apply to Child`
- Replaced the old Flutter funding screen:
  - supports general parent wallet funding
  - supports loading new money and applying it to a child immediately
  - supports applying existing parent wallet balance to a child
  - supports bucket allocation for Lunch / Snacks, Books, Fotocopies, Transport, and General
- Updated `/app` browser test page:
  - country selector
  - phone code auto-fill
  - wallet summary
  - general wallet funding
  - child bucket funding
- Verification:
  - Alembic upgraded active database to `k1l2m3n4o5p6`.
  - Backend syntax check passed.
  - Backend restarted.
  - End-to-end API smoke test passed:
    - created parent
    - saved country/profile
    - created child
    - loaded 100 to parent wallet
    - allocated 100 to child buckets
    - verified parent balance 0 and child balance 100
  - `dart analyze` passed.
  - DNS API ping returned `pong`.
  - DNS `/app` page contains country and money-loading UI.

#### Child Setup Counter Clamp

- Prevented impossible child setup labels such as:
  - `Add Child 3 of 2`
- Flutter:
  - setup child index is clamped between 1 and the setup total
  - progress bar value is clamped
  - save action exits setup if a bad over-total index is reached
- Browser `/app`:
  - next child display is clamped to the configured target
  - once target is reached, the child form shows completion and disables additional child entry
  - existing child count is reconciled against the configured target when dashboard data loads
- Files changed:
  - `colepago-parents-app/lib/screens/add_child_screen.dart`
  - `static/portal.js`
- Verification:
  - `dart analyze` passed.
  - Live `/static/portal.js` contains the child counter clamp.

#### Required Unique Kid Phone Number

- Added required kid phone number to child creation.
- Backend:
  - `ChildCreateRequest.mobile_phone` is required.
  - phone is normalized to digits and `+`.
  - empty phone is rejected.
  - duplicate phone is rejected before insert.
  - child list and child creation responses include `mobile_phone`.
- Database:
  - added `children.mobile_phone`
  - added unique index `ix_children_mobile_phone`
  - migration `alembic/versions/l2m3n4o5p6q7_add_unique_child_mobile_phone.py`
- Flutter:
  - `AddChildScreen` asks for `Kid phone number`
  - field is required before saving.
- Browser `/app`:
  - child form asks for required `Kid phone number`
  - value is sent to `POST /api/parent/add-child`.
- Verification:
  - Backend syntax check passed.
  - `dart analyze` passed.
  - Alembic upgraded active database to `l2m3n4o5p6q7`.
  - Backend restarted.
  - API smoke test confirmed missing kid phone returns HTTP 422.
  - API smoke test confirmed duplicate kid phone returns HTTP 400 with `Child phone number is already used`.
  - DNS API ping returned `pong`.
  - DNS `/app` contains the kid phone field.

#### Child School Schedule And Activities

- Added child school schedule capture.
- Backend now requires and stores for each new child:
  - school attending
  - school shift
  - shift start time
  - shift end time
  - additional activities JSON
- Added child columns:
  - `school_id`
  - `school_name`
  - `shift`
  - `shift_start`
  - `shift_end`
  - `activities_json`
- Added migration:
  - `alembic/versions/m3n4o5p6q7r8_add_child_school_schedule.py`
- Flutter child form:
  - school search is now optional helper data
  - `School attending` is required and can be filled manually
  - `School shift` is required
  - shift start/end hours are required
  - extra activities can be added before or after school shift
  - supported activity types include dance, language lessons, music, soccer, baseball, other sports practice, and other
- Browser `/app` child form:
  - added the same school, shift hours, and additional activities fields
  - activities include before/after shift, type, name/detail, hours, address, institution, and teacher/professor/coach
- Verification:
  - Backend syntax check passed.
  - `dart analyze` passed.
  - Alembic upgraded active database to `m3n4o5p6q7r8`.
  - Backend restarted.
  - API smoke test created a child with school, shift hours, and two activities.
  - Child list API returned the stored activities.
  - DNS API ping returned `pong`.
  - DNS `/app` contains the new child schedule fields.

#### Route-Safety Explanation And Activity Place Contact

- Added explanation in child setup for why school, shift, route, and activity data is requested:
  - parents can be warned if a child separates from the normal walk, bus, school route, or expected activity schedule
- Added additional activity place contact details:
  - activity place name
  - activity place address
  - activity place phone
- Backend:
  - activity JSON now preserves `phone`
- Flutter:
  - added route-safety explanation card
  - renamed activity fields to place name/address
  - added activity place phone
- Browser `/app`:
  - added route-safety explanation text
  - renamed activity fields to place name/address
  - added activity place phone
  - activity preview includes place/address/phone
- Verification:
  - `dart analyze` passed.
  - Backend syntax check passed.
  - Backend restarted.
  - API smoke test confirmed activity place name, address, and phone are stored and returned.
  - DNS API ping returned `pong`.
  - DNS `/app` contains the explanation and activity place phone field.

#### Kid APK Activation And Merchant QR Payment Flow

- Backend:
  - added `POST /api/auth/kid-login`
  - kid activation uses parent email, parent password, and the child's unique phone number
  - response returns the real `child_id` for the kid APK
  - added `POST /api/merchant/sales/qr`
  - added `POST /api/child/pay-sale`
  - merchant sale payload includes merchant info, item descriptions, quantities, prices, line totals, total, note, and timestamp
  - child payment validates the selected bucket and debits bucket spend after ledger purchase recording
- Flutter kid APK:
  - replaced normal user login with kid activation screen
  - stores kid token and `kid_id` locally
  - requires biometric/face/iris authentication before bucket display
  - kid sees only wallet buckets
  - selecting a bucket opens the camera QR scanner immediately
- Flutter merchant flow:
  - added sale page with multiple item rows
  - calculates sale total
  - renders a real QR code for the kid camera to scan
- Parent setup:
  - after last child setup, prompts parent to install the kid APK, activate it, configure secure access, and verify bucket visibility
- Platform/dependencies:
  - added `mobile_scanner`
  - added `qr_flutter`
  - added Android camera permission
  - added iOS camera and Face ID usage descriptions
- Verification:
  - `flutter pub get` completed and updated lockfile.
  - `dart analyze` passed.
  - Backend syntax check passed.
  - Backend restarted on port `8010`.
  - API smoke test created disposable parent, child, merchant, funded wallet, allocated bucket money, activated kid login, created merchant sale QR payload, paid from selected bucket, and confirmed bucket remaining dropped from `60.0` to `30.0`.
  - Kids debug APK build was attempted but timed out after 10 minutes before producing a debug APK; build-era Dart/Java processes were stopped.

#### Item Bucket Routing, Bucket Borrowing, And Threshold Warnings

- Backend:
  - merchant sale items can now include `bucket_name`
  - QR payment routes each item to its own bucket when present
  - selected bucket remains the fallback for items without a bucket
  - if the target bucket is short, payment can borrow from other child buckets with available money
  - payment response returns bucket debits and borrowing details
  - parent WhatsApp notification is attempted when borrowing happens or affected buckets cross their warning threshold
  - notification text includes all affected buckets and borrowing details
  - added `PUT /api/child/{child_id}/wallet_buckets/thresholds`
  - wallet allocation can set `alert_threshold_pct` per bucket
- Flutter kid APK:
  - removed visible manual QR payload entry
  - kid flow is now bucket tap -> camera opens -> QR scan -> payment
- Flutter merchant flow:
  - each sale item has a bucket selector
  - QR payload carries item bucket names
- Flutter parent flow:
  - parent wallet screen has general warning threshold control
  - parent wallet screen has per-bucket warning threshold controls
  - thresholds can be saved independently or included when applying money to child buckets
- Browser `/app` parent flow:
  - parent money form has general and per-bucket warning threshold controls
  - added Transport bucket support to match the APK bucket set
  - thresholds can be saved independently or included when applying money
- Verification:
  - `dart analyze` passed.
  - Backend syntax check passed.
  - Backend restarted on port `8010`.
  - API smoke test created disposable parent, child, merchant, funded wallet, allocated `Lunch / Snacks=5.0` and `Books=40.0`, created sale item routed to `Lunch / Snacks` for `20.0`, paid successfully by debiting `5.0` from Lunch and borrowing `15.0` from Books.
  - Smoke test confirmed notification payload included affected buckets `Lunch / Snacks` and `Books`; send was blocked only because Twilio credentials are not configured in this environment.
  - Browser `/app` served threshold controls and updated portal JavaScript over DNS.
  - `node --check static/portal.js` could not run because Node.js is not installed on this host.
  - DNS API ping returned `pong`.

#### Email Format Validation

- Confirmed backend registration rejects invalid email values through `EmailStr`.
- Added client-side email format validation to:
  - Flutter login screen
  - Flutter register screen
  - Flutter kid activation screen parent email
  - Browser `/app` login form
  - Browser `/app` register form
- Improved Flutter registration error display so backend validation details are shown instead of only `Registration failed`.
- Verification:
  - Direct backend registration with `email=drcalo` returned HTTP `422` with invalid email detail.
  - `dart analyze` passed.
  - Backend syntax check passed.
  - Browser `/app` served updated JavaScript containing email validation over DNS.

#### Multi-Child Navigation And Scoped School Selection

- Backend:
  - added database-backed school selector endpoints:
    - `GET /api/geo/provinces`
    - `GET /api/geo/cities?province=...`
    - `GET /api/geo/neighborhoods?province=...&city=...`
    - `GET /api/geo/schools?province=...&city=...&neighborhood=...`
  - school dropdowns use existing `schools` table fields:
    - `provincia`
    - `ciudad`
    - `comuna`
    - `name`
    - `address`
    - `phone`
- Flutter:
  - add-child setup now lets parents move Previous/Next between child forms during multi-child loading
  - each child form keeps an in-memory draft while navigating
  - saved child indexes are marked and are not re-submitted
  - school search is split into State/Province -> City -> Neighborhood/Comuna when present -> School
  - if no neighborhood/comuna data exists for a city, schools load directly after city selection
- Browser `/app`:
  - added Previous Child and Next Child controls
  - added in-browser child drafts while navigating through setup children
  - added State/Province, City, Neighborhood/Comuna, and School dropdowns
  - selected school fills `School attending`
- Verification:
  - Database has about `188449` schools, `80` provinces/states, and `23972` cities; current loaded `comuna` values are empty, so UI falls back from city directly to schools when needed.
  - `dart analyze` passed.
  - Backend syntax check passed.
  - Backend restarted on port `8010`.
  - API smoke test returned `80` provinces, sample province `AK`, sample city `ANCHORAGE`, and sample school `ANCHORAGE JUNIOR ACADEMY`.
  - Browser `/app` served the new province select, child navigation buttons, and school geo JavaScript over DNS.
  - DNS API ping returned `pong`.

#### Parent Workspace Frames And Parent Name

- Added parent name to the parent profile API:
  - `GET /api/parent/{parent_id}/profile` now returns `name`
  - `PUT /api/parent/{parent_id}/profile` accepts `name`
  - saving parent profile updates `users.name`
- Browser `/app` parent workspace now uses a vertical frame flow:
  - Parent Information at the top
  - Add/Browse Kids below
  - Load Money at the end
- Browser parent information frame now includes:
  - Parent name
  - Relationship
  - Children count
  - Parent phone/country/address details
- Verification:
  - Backend syntax check passed.
  - `dart analyze` passed.
  - Backend restarted on port `8010`.
  - API smoke test saved parent profile name as `Updated Parent Name` and loaded it back successfully.
  - Browser `/app` served the parent name field, parent frame layout, CSS, and JavaScript over DNS.

#### Kid Economy Dashboard And Modify Menu

- Backend:
  - added `GET /api/parent/{parent_id}/dashboard_economy`
  - returns parent balance, children balance, and per-kid economy details:
    - child balance
    - total remaining money
    - 7-day spend
    - 30-day spend
    - daily spend rate
    - estimated days left
    - affected/warning buckets
    - per-bucket allocated, spent, remaining, used percent, threshold, and status
- Flutter parent dashboard:
  - added Kids Economic Situation section
  - each kid card shows remaining money, spend rate, 7-day spend, estimated days left, and bucket progress
  - hamburger menu actions now give quick access to:
    - modify parent information
    - modify kid information
    - load or apply money
- Browser `/app`:
  - added Kids Economic Situation frame between Parent Information and Add/Browse Kids
  - added kid dropdown to browse each kid's economy
  - shows metrics and bucket warning state
  - added hamburger/dropdown menu to jump to parent info, kid info, or money frame
- Verification:
  - Backend syntax check passed.
  - `dart analyze` passed.
  - Backend restarted on port `8010`.
  - API smoke test created disposable parent, kid, merchant, funded/allocated money, processed a sale, then confirmed dashboard economy returned remaining `38.0`, 7-day spend `12.0`, daily rate `1.71`, and 2 buckets.
  - Browser `/app` served the economy frame, hamburger actions, dashboard JavaScript, and dashboard CSS over DNS.
  - DNS API ping returned `pong`.

#### Android App Bundle Build Output

- Updated `colepago-parents-app/build_both_apks.ps1`.
- Release build script now generates both formats:
  - APKs for direct install/testing
  - Android App Bundles (`.aab`) for Google Play upload
- Expected outputs:
  - `build/app/outputs/flutter-apk/app-kids-release.apk`
  - `build/app/outputs/bundle/kidsRelease/app-kids-release.aab`
  - `build/app/outputs/flutter-apk/app-parents-release.apk`
  - `build/app/outputs/bundle/parentsRelease/app-parents-release.aab`
- Verification:
  - PowerShell syntax check passed.
  - Full Flutter build was not run during this change.

#### Dense Browser Form Layout

- Updated browser `/app` CSS so form fields in backend/browser panels auto-pack into as many columns as the screen can fit.
- Kept mobile responsive behavior as single-column.
- Full-width elements remain full-width:
  - headings
  - messages
  - explanation blocks
  - activity boxes
  - dashboard heading/detail blocks
  - action rows
- Verification:
  - DNS `/static/portal.css` served the new `auto-fit` form layout rules.

#### Twilio SMS Channel

- Added SMS support through Twilio using environment variables only.
- Do not hardcode live Twilio credentials in source files.
- Added `send_sms` helper in `whatsapp_utils.py`.
- Added direct SMS endpoint:
  - `POST /api/parent/{parent_id}/sms`
- Added `sms` to escalation channels:
  - default channels are now `whatsapp`, `sms`, `call`, and `email`
- Updated `.env.example` with:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_SMS_FROM`
  - `TWILIO_MESSAGING_SERVICE_SID`
  - `TWILIO_WHATSAPP_FROM`
  - `TWILIO_CALL_FROM`
- Fixed Twilio number normalization so numbers already entered with `+` are not prefixed with country code again.
- Verification:
  - Python syntax check passed.
  - Backend restarted on port `8010`.
  - API ping returned `pong`.
  - SMS endpoint smoke test returned expected `404 Parent profile not found` for a fake parent id, confirming the route is live without sending a real SMS.
- Follow-up:
  - Tightened phone normalization for profiles where `country_code` already contains the full phone number.
  - Attempted SMS to parent id `4` with message `hey I fine`.
  - Send failed because SMS sender is not configured:
    - set `TWILIO_SMS_FROM`
    - or set `TWILIO_MESSAGING_SERVICE_SID`
  - After `.env` was configured, backend was restarted and SMS send to parent id `4` succeeded.
  - Twilio SID returned: `SM44028e59816eb438a9ec7c800da3d425`.

#### Twilio WhatsApp Content Templates

- Added support for Twilio WhatsApp Content Template messages.
- Added helper:
  - `send_whatsapp_template`
- Existing endpoint `POST /api/parent/{parent_id}/whatsapp` now supports either:
  - free-text `message`
  - template `content_sid` plus `content_variables`
- `.env.example` now includes:
  - `TWILIO_WHATSAPP_TEMPLATE_CONTENT_SID`
- Verification:
  - Python syntax check passed.
  - Backend restarted on port `8010`.
  - API ping returned `pong`.

#### Message-Only Parent Alerts

- Added generic message-only endpoint:
  - `POST /api/parent/{parent_id}/message`
- Supported channels:
  - `whatsapp`
  - `sms`
- No voice call is attempted by this endpoint.
- Escalation defaults changed to message-first only:
  - default channels are now `whatsapp`, `sms`, and `email`
  - `call` is only used if explicitly included in a request
- Verification:
  - Python syntax check passed.
  - Backend restarted on port `8010`.
  - API ping returned `pong`.
  - Message endpoint smoke test returned expected `404 Parent profile not found` for fake parent id, confirming the route is live without sending a real message.

### 2026-05-09

#### APK Build/Deploy Consistency Check

- Reviewed `deploy_all.ps1` and `colepago-parents-app/build_both_apks.ps1` for APK build compatibility.
- Found issue:
  - `deploy_all.ps1` ran `flutter upgrade` immediately before building APKs.
  - This is unsafe for reproducible deployment because Flutter/Gradle/Android plugin upgrades can break the APK build without warning.
- Changed `deploy_all.ps1`:
  - Replaced `flutter upgrade` with `flutter --version`.
  - Deployment now verifies Flutter is available but does not upgrade it automatically.
  - Deployment aborts if `build_both_apks.ps1` returns a non-zero exit code.
- Found issue:
  - `build_both_apks.ps1` reported APK success when old APK files already existed, even if the new build failed.
- Changed `build_both_apks.ps1`:
  - Added strict error behavior.
  - Removes stale expected APK outputs before each flavor build.
  - Checks `$LASTEXITCODE` after each `flutter build apk`.
  - Throws on build failure or missing expected output.
  - Builds both flavors with explicit `--release`.
- Validation:
  - PowerShell syntax parse passed for `deploy_all.ps1`.
  - PowerShell syntax parse passed for `build_both_apks.ps1`.
- Important:
  - No new APK build was started during this check because the user was already running a build.

#### Gradle APK Build Crash Diagnosis

- User ran `deploy_all.ps1` and the APK build failed during `assembleKidsRelease`.
- Crash log inspected:
  - `colepago-parents-app/android/hs_err_pid18344.log`
- Root cause from JVM crash log:
  - Java native memory allocation failed.
  - Gradle daemon disappeared because the JVM crashed.
  - The JVM was launched with `-Xmx5G`.
  - Gradle had many worker/build operation threads active.
- Changed Android Gradle stability settings in:
  - `colepago-parents-app/android/gradle.properties`
- New settings:
  - reduced heap from `-Xmx5G` to `-Xmx3G`
  - reduced thread stack with `-Xss512k`
  - reduced metaspace/code cache
  - disabled Gradle daemon
  - disabled parallel build
  - disabled configure-on-demand
  - limited workers with `org.gradle.workers.max=2`
  - disabled R8 full mode with `android.enableR8.fullMode=false`
- Changed APK build helper:
  - `build_both_apks.ps1` now stops existing Gradle daemons before starting APK builds.
- Validation:
  - `deploy_all.ps1` syntax OK.
  - `build_both_apks.ps1` syntax OK.
- Important:
  - The failed output still showed `Checking for new Flutter version...`, which means it was run from the older script version or before the latest patch. The current `deploy_all.ps1` says `Checking Flutter version...` and does not run `flutter upgrade`.

#### Dependency Setup

- Installed missing Python dependencies from `colepago/requirements.txt` into the existing virtual environment.
- Verified dependency health with:
  - `python -m pip check`
- Result:
  - No broken requirements found.
- Note:
  - Payment-related tests were not run automatically to avoid accidental real external service calls.

#### Brochure Review

- Reviewed `D:\kidwall\brochure`.
- Found English and Spanish ColePago/StudentWallet brochure materials, PDFs, images, diagrams, and PDF generation scripts.
- Key brochure message:
  - Parents fund through Stripe or Mercado Pago.
  - Backend handles virtual tokens/coins.
  - Kids spend at school.
  - Parents receive notifications.
  - Security positioning: backend should not store card data or handle raw payment data.
- Pending brochure cleanup:
  - Replace placeholder contact emails.
  - Replace dummy image URLs.
  - Fix or regenerate broken/small `architecture_diagram.png`.
  - Improve Spanish PDF accent handling.
  - Verify public security claims against actual backend/database behavior.

#### Email Notifications

- Configured SMTP for EasyDNS in `.env`.
- Verified SMTP login successfully without sending email.
- Updated email utilities:
  - `email_utils.py`
  - `colepago/email_utils.py`
- Added/standardized alert email support.
- Automatic child safety alerts now email:
  - parent account email
  - parent profile email
  - trusted/alternate contacts with email
- Duplicate email recipients are filtered.
- Security note:
  - Mail credentials were provided during configuration. The password should be rotated after testing.

#### Parent And Trusted Contact Test Data

- Created local seed scripts:
  - `seed_test_contacts.py`
  - `seed_diego_parent.py`
  - `seed_test_merchant.py`
- Created initial test records:
  - parent
  - child
  - trusted/alternate contacts
  - test merchant
- Updated parent profile with Diego R Carloni details.
- Added missing database fields for cleaner parent profile storage:
  - `users.username`
  - `parent_profiles.home_floor`
  - `parent_profiles.home_department`
  - `parent_profiles.work_postal`
- Applied migration:
  - `d4e5f6a7b8c9_add_parent_username_and_address_details.py`
- Verified database read-back.

#### Registration And Password Hashing

- Replaced the failing `passlib` bcrypt path in the active API router with direct `bcrypt` hashing/checking.
- Reason:
  - Current installed `passlib` plus `bcrypt` version caused hashing errors.
- Registration now supports:
  - `name`
  - `username`
  - `email`
  - `password`
  - `role`
- Existing role model:
  - `parent`
  - `merchant`

#### Parent/Merchant App Direction

- Confirmed architecture direction:
  - Parents and merchants should use the same APK.
  - User role determines which dashboard/screens are shown.
- Backend already supports role-based users.
- Pending app work:
  - Check Flutter login/registration flow.
  - Route parent users to parent dashboard.
  - Route merchant users to merchant dashboard.
  - Add merchant payout setup UI.
  - Add trusted contact UI if incomplete.

#### Payment Flow Clarification

- Clarified that parent deposits real money through payment providers.
- Backend records internal wallet/ledger value.
- Kid presents/spends virtual coins.
- Merchant confirms the payment.
- Backend deducts from parent wallet and credits merchant receivable.
- Real money payout to merchant must happen through Mercado Pago, Stripe, or bank/manual payout.

#### Payment Gateway And Ledger Foundation

- Added provider-neutral ledger/gateway foundation.
- New model concepts:
  - ledger accounts
  - ledger transactions
  - ledger entries
  - external payments
  - external payouts
  - merchant payout methods
- Added migration:
  - `e5f6a7b8c9d0_add_payment_gateway_ledger.py`
- Added service:
  - `services/payment_gateway.py`
- Wired existing flows through gateway layer:
  - `/wallet/fund`
  - `/child/spend`
- Added starter merchant payout endpoints:
  - `POST /merchant/{merchant_id}/payout-methods`
  - `POST /merchant/{merchant_id}/payouts`
- Smoke test completed:
  - parent deposit posted
  - child purchase posted
  - ColePago fee split posted
  - merchant payout prepared
  - all ledger transactions balanced to zero
- Current migration head:
  - `e5f6a7b8c9d0`

#### Infrastructure Direction

- Clarified Kubernetes/Ingress/Gateway responsibilities:
  - Ingress is the public HTTPS front door.
  - Payment gateway is the business/payment orchestration layer.
  - Internal APIs can later use internal TLS or mTLS.
- Recommended initial routing:
  - `https://api.drsrv.net.ar/api`
  - `https://api.drsrv.net.ar/payments`
  - `https://api.drsrv.net.ar/webhooks`

## 2026-05-11 - Direct Parent Phone Call Fallback

- Added an explicit backend call endpoint:
  - `POST /api/parent/{parent_id}/call`
  - Calls are opt-in only; message endpoints still send WhatsApp/SMS and do not call.
- Added a direct dial option in the real browser app at `/app`:
  - dashboard menu item `Call parent phone`
  - uses `tel:` with the stored parent profile mobile phone.
- Added the same direct dial option to the parent APK dashboard menu and drawer.
- Added Android `tel:` dial intent visibility for `url_launcher`.
- Cached the last loaded parent dial number locally in the APK and browser app so the direct call action can still use it after a later backend/network failure.
- Verified:
  - backend syntax check passed
  - `dart analyze` passed
  - backend restarted on port `8010`
  - `/api/ping` returned `pong`
  - fake parent call route returned `404` without placing a real call
  - served `/app` includes the call menu and `tel:` launcher

## 2026-05-11 - Stripe Test PaymentIntent Backend

- Confirmed `.env` contains Stripe test variables without printing secret values:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLISHABLE_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_CURRENCY`
- Added pending/confirmed parent deposit lifecycle helpers in `services/payment_gateway.py`.
- Added Stripe config endpoint:
  - `GET /api/payments/stripe/config`
- Added Stripe PaymentIntent creation endpoint:
  - `POST /api/wallet/stripe/create-payment-intent`
  - Creates a pending `ExternalPayment`.
  - Returns `client_secret` for the app/browser payment UI.
- Added Stripe webhook endpoint:
  - `POST /api/webhooks/stripe`
  - Confirms wallet deposits only on `payment_intent.succeeded`.
  - Marks pending deposits failed on `payment_intent.payment_failed`.
- Added payment lookup endpoint:
  - `GET /api/payments/{payment_id}`
- Wired browser `/app` money form to Stripe Elements:
  - shows a card field when `Stripe card` is selected
  - creates/confirms a PaymentIntent
  - waits for webhook confirmation before applying child bucket allocation
- Changed old `/api/wallet/fund` `stripe_card` path to reject direct wallet credit and point callers to PaymentIntent flow.
- Verified:
  - backend syntax check passed
  - backend restarted on port `8010`
  - `/api/ping` returned `pong`
  - `/api/payments/stripe/config` returned currency and a publishable key flag
  - served `/app` includes Stripe Elements script and card field
  - creating a test PaymentIntent for `ARS 20,000` succeeded and created pending payment id `6`
  - small `ARS 100` test amount was rejected by Stripe because it converted below the account minimum
  - old direct Stripe fund route returned `400` instead of crediting money

## 2026-05-11 - Admin-Only Configuration Menu

- Added private admin detection from allowlisted owner email/user ids:
  - `ADMIN_EMAILS`
  - `ADMIN_USER_IDS`
- Auth responses now include `is_admin` for browser visibility.
- Added admin-only backend endpoints:
  - `GET /api/admin/settings`
  - `PUT /api/admin/settings`
- Added runtime settings file:
  - `config/admin_settings.json`
  - ignored by Git as environment-specific configuration.
- Added browser `/app` hidden admin menu/frame:
  - visible only when `is_admin` is true
  - controls fee percent, fee payer, currency, country, society profile, religion context, local policy notes, and merchant fee disclosure.
- Connected purchase commission calculation to admin `fee_percent`.
- Verified:
  - backend syntax check passed
  - backend restarted on port `8010`
  - `/api/ping` returned `pong`
  - owner user id can read/save admin settings
  - request without admin user id returns `401`
  - served `/app` includes hidden admin UI

## 2026-05-11 - Browser Dark Theme

- Added a light/dark theme toggle to the `/app` header.
- Stores the selected theme in browser local storage under `colepago_theme`.
- Added dark theme CSS variables for:
  - page background
  - panels
  - form fields
  - menus
  - soft metric panels
  - warning buckets
  - focus and shadow colors
- Verified:
  - served `/app` includes the theme toggle
  - backend `/api/ping` still returns `pong`

## 2026-05-11 - Kid APK Background Picker

- Added a kid-side background picker to the bucket screen.
- The picker is opened from a palette icon in the kid app bar.
- Built-in backgrounds:
  - Sky
  - Space
  - Candy
  - Jungle
  - Arcade
- The selected background is saved locally per kid device with `SharedPreferences`.
- Verified:
  - `dart format` completed
  - `dart analyze` passed

## 2026-05-11 - Browser Child Navigation Fix

- Fixed browser `/app` child setup navigation:
  - Previous/Next now remain enabled after the planned children are complete.
  - Navigation controls were moved near the child frame title.
- Reduced the child setup frame density:
  - smaller grid columns
  - smaller labels/inputs/buttons
  - compact additional-activities layout
- Verified:
  - served `/app` contains the moved child navigation
  - served JavaScript keeps child navigation enabled after completion
  - served CSS contains compact child frame rules
  - backend `/api/ping` returned `pong`

## 2026-05-11 - Dashboard Accelerometer Graph

- Added optional accelerometer fields to child location pings:
  - `accel_x`
  - `accel_y`
  - `accel_z`
- Added migration:
  - `n4o5p6q7r8s9_add_accelerometer_to_location_pings.py`
- Added graph-ready backend endpoint:
  - `GET /api/child/{child_id}/accelerometer?limit=60`
  - returns movement magnitude over time instead of raw x/y/z values.
- Added a Movement graph to the parent dashboard kid section.
- Fixed the dashboard kid selector so changing kids does not jump back to the first child while rendering.
- Verified:
  - backend syntax check passed
  - migration applied
  - backend restarted on port `8010`
  - `/api/ping` returned `pong`
  - served `/app` contains the accelerometer graph canvas
  - public graph endpoint returns graph-ready samples payload

### 2026-05-12

#### Android APK Crash-On-Launch — Three Sequential Fixes

All three fixes below were applied to the Flutter multi-flavor Android app at `colepago-parents-app/`. Both flavors (`kids` and `parents`) crashed immediately on launch without showing any UI. Three root causes were identified and fixed in sequence.

##### Fix 1 — FlutterFragmentActivity Required By local_auth

- `local_auth ^3.0.1` requires the host activity to extend `FlutterFragmentActivity`, not `FlutterActivity`.
- Flutter auto-registers all plugins via `GeneratedPluginRegistrant` at startup, so the crash occurred before any UI was shown.
- Changed:
  - `android/app/src/main/kotlin/com/example/colepago_parents_app/MainActivity.kt`
  - Base class changed from `io.flutter.embedding.android.FlutterActivity` to `io.flutter.embedding.android.FlutterFragmentActivity`.
- Current content after fix:
  ```kotlin
  package com.example.colepago_parents_app
  import io.flutter.embedding.android.FlutterFragmentActivity
  class MainActivity : FlutterFragmentActivity()
  ```

##### Fix 2 — INTERNET Permission Missing From Release Manifest

- The `INTERNET` permission was declared only in `android/app/src/debug/AndroidManifest.xml`.
- Release builds merged only from `android/app/src/main/AndroidManifest.xml`, so release APKs had no network access.
- Changed:
  - `android/app/src/main/AndroidManifest.xml`
  - Added `<uses-permission android:name="android.permission.INTERNET"/>` as the first `uses-permission` entry, before `USE_BIOMETRIC`, `USE_FINGERPRINT`, and `CAMERA`.

##### Fix 3 — Namespace Must Be Top-Level In android {} Block

- Logcat showed `ClassNotFoundException: Didn't find class "com.example.colepago_parents_app.MainActivity"` for both `colepago.kids` and `colepago.parents` processes.
- Root cause: `namespace` was set inside `productFlavors` (per-flavor), which is not valid Android Gradle Plugin (Kotlin DSL) syntax.
  - `namespace` is a top-level `android {}` property.
  - Without a valid top-level namespace, AGP cannot correctly compile and link the Kotlin class into the APK DEX.
- Changed:
  - `android/app/build.gradle.kts`
  - Added `namespace = "com.example.colepago_parents_app"` at the top of the `android {}` block.
  - Removed `namespace` entries from both `kids` and `parents` product flavor definitions.
- Current state of relevant block:
  ```kotlin
  android {
      namespace = "com.example.colepago_parents_app"
      compileSdk = flutter.compileSdkVersion
      ndkVersion = "28.2.13676358"
      ...
      productFlavors {
          create("kids") {
              dimension = "app"
              applicationId = "colepago.kids"
              manifestPlaceholders["appLabel"] = "colepago-kids"
          }
          create("parents") {
              dimension = "app"
              applicationId = "colepago.parents"
              manifestPlaceholders["appLabel"] = "colepago-parents"
          }
      }
  }
  ```
- Note: `applicationId` per flavor still controls distinct package names on the device (`colepago.kids` / `colepago.parents`). `namespace` only controls where AGP looks for compiled Kotlin classes; it must match the `package` declaration in `MainActivity.kt`.

##### Files Changed

- `android/app/src/main/kotlin/com/example/colepago_parents_app/MainActivity.kt`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/build.gradle.kts`

##### Verification

- All three source edits applied and confirmed with no parse errors.
- Old APKs uninstalled from device:
  - `adb uninstall colepago.kids`
  - `adb uninstall colepago.parents`
- Rebuild pending: run `build_both_apks.ps1` and reinstall both APKs.

##### Pending

- Rebuild both APKs with `.\build_both_apks.ps1` from `colepago-parents-app/`.
- Reinstall and retest on device.
- If still failing, capture filtered logcat: `adb logcat -s flutter colepago.kids colepago.parents AndroidRuntime`.

## Pending Items

- Rotate exposed SMTP/mail password after testing.
- Add SMS support through Twilio:
  - add `TWILIO_SMS_FROM`
  - add `send_sms`
  - add `sms` channel to escalation flow
  - handle A2P/10DLC compliance for US SMS if needed
- Complete WhatsApp/Twilio configuration.
- Add real provider adapters:
  - Mercado Pago deposits/webhooks/payouts
  - Stripe deposits/webhooks/Connect payouts
  - manual bank payout workflow
- Add idempotency keys to deposits, purchases, webhooks, and payouts.
- Add webhook endpoints:
  - Mercado Pago
  - Stripe
- Add reconciliation/admin views:
  - external payment status
  - external payout status
  - ledger transaction browser
  - failed payout retry
- Replace float balance usage with integer-cent ledger balances as source of truth.
- Keep `users.balance` only as a cached/display balance or remove it later.
- Add tests for:
  - ledger balanced entries
  - parent deposit
  - child purchase fee split
  - merchant payout preparation
  - insufficient funds
  - duplicate webhook/idempotency handling
- Create/import US schools dataset when available.
- Add school import validation:
  - deduplication
  - address normalization
  - geocoding strategy
  - school search endpoint
- Review security/compliance:
  - credential rotation
  - no secrets in Git
  - payment provider webhook signature checks
  - audit logs
  - role-based permissions
  - merchant onboarding verification
- Review Flutter app:
  - single APK for parent and merchant
  - role-based navigation
  - merchant payment confirmation screen
  - parent trusted contacts screen
  - payout setup screen

## Important Files Changed Or Added

- `models.py`
- `email_utils.py`
- `colepago/email_utils.py`
- `colepago/api/router.py`
- `services/payment_gateway.py`
- `alembic/versions/d4e5f6a7b8c9_add_parent_username_and_address_details.py`
- `alembic/versions/e5f6a7b8c9d0_add_payment_gateway_ledger.py`
- `seed_test_contacts.py`
- `seed_diego_parent.py`
- `seed_test_merchant.py`
- `.env.example`

## Notes

- Do not store or repeat live credentials in this file.
- Alembic migrations run once per migration and record the current version in the database table `alembic_version`.
- The ledger should become the source of truth for money movement.
- Provider balances and payouts must be reconciled against Mercado Pago, Stripe, or bank records before production use.
