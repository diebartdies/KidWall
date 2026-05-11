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
