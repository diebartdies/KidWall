const apiBase = `${window.location.origin}/api`;

const state = {
  token: localStorage.getItem('colepago_token'),
  userId: Number(localStorage.getItem('colepago_user_id')),
  role: localStorage.getItem('colepago_role'),
  childTarget: 1,
  childSaved: 0,
  childCurrent: 1,
  childDrafts: {},
  childSavedIndexes: new Set(),
  children: [],
  economyChildren: [],
  childActivities: [],
  parentPhone: '',
  isAdmin: localStorage.getItem('colepago_is_admin') === 'true',
  theme: localStorage.getItem('colepago_theme') || 'light',
};

const countryCodes = {
  'United States': '+1',
  Argentina: '+54',
  Mexico: '+52',
  Brazil: '+55',
  Chile: '+56',
  Colombia: '+57',
  Uruguay: '+598',
  Paraguay: '+595',
  Peru: '+51',
  Spain: '+34',
};

let stripeClient = null;
let stripeElements = null;
let stripeCard = null;

const $ = (id) => document.getElementById(id);

function applyTheme(theme = state.theme) {
  state.theme = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = state.theme;
  localStorage.setItem('colepago_theme', state.theme);
  const button = $('theme-toggle-button');
  if (button) button.textContent = state.theme === 'dark' ? 'Light' : 'Dark';
}

function setMessage(id, text, tone = '') {
  const el = $(id);
  el.textContent = text;
  el.className = `message ${tone}`.trim();
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim());
}

async function api(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(state.userId ? { 'X-User-Id': String(state.userId) } : {}),
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

function showAuth() {
  $('auth-view').classList.remove('hidden');
  $('workspace-view').classList.add('hidden');
}

function showWorkspace() {
  $('auth-view').classList.add('hidden');
  $('workspace-view').classList.remove('hidden');
  $('session-role').textContent = state.role || '';
  $('session-title').textContent =
    state.role === 'merchant' ? 'Merchant Dashboard' : 'Parent Dashboard';
  $('parent-workspace').classList.toggle('hidden', state.role !== 'parent');
  $('merchant-workspace').classList.toggle('hidden', state.role !== 'merchant');
  $('admin-workspace').classList.toggle('hidden', !state.isAdmin);
  $('admin-menu-button').classList.toggle('hidden', !state.isAdmin);
  if (state.isAdmin) loadAdminSettings();
}

function saveSession(payload) {
  state.token = payload.token || payload.access_token;
  state.userId = payload.user_id || payload.parent_id || payload.id;
  state.role = payload.role || 'parent';
  state.isAdmin = Boolean(payload.is_admin);
  localStorage.setItem('colepago_token', state.token);
  localStorage.setItem('colepago_user_id', String(state.userId));
  localStorage.setItem('colepago_role', state.role);
  localStorage.setItem('colepago_is_admin', String(state.isAdmin));
}

function clearSession() {
  state.token = null;
  state.userId = 0;
  state.role = null;
  state.childCurrent = 1;
  state.childDrafts = {};
  state.childSavedIndexes = new Set();
  state.isAdmin = false;
  localStorage.removeItem('colepago_token');
  localStorage.removeItem('colepago_user_id');
  localStorage.removeItem('colepago_role');
  localStorage.removeItem('colepago_is_admin');
}

function switchAuth(mode) {
  const login = mode === 'login';
  $('login-form').classList.toggle('hidden', !login);
  $('register-form').classList.toggle('hidden', login);
  $('login-tab').classList.toggle('active', login);
  $('register-tab').classList.toggle('active', !login);
  setMessage('auth-message', '');
}

function updateChildHomeVisibility() {
  const livesWithParent = $('child-lives-with-parent').checked;
  $('child-home-fields').classList.toggle('hidden', livesWithParent);
}

function resetChildForm() {
  $('child-name').value = '';
  $('child-mobile-phone').value = '';
  $('child-school-province').value = '';
  $('child-school-city').innerHTML = '';
  $('child-school-neighborhood').innerHTML = '';
  $('child-school-neighborhood-wrap').classList.add('hidden');
  $('child-school-select').innerHTML = '';
  $('child-school-name').value = '';
  $('child-shift').value = '';
  $('child-shift-start').value = '';
  $('child-shift-end').value = '';
  $('child-lives-with-parent').checked = true;
  $('child-home-address').value = '';
  $('child-home-phone').value = '';
  state.childActivities = [];
  clearActivityDraft();
  renderChildActivities();
  updateChildHomeVisibility();
}

function captureChildDraft() {
  state.childDrafts[state.childCurrent] = {
    name: $('child-name').value,
    mobile: $('child-mobile-phone').value,
    province: $('child-school-province').value,
    city: $('child-school-city').value,
    neighborhood: $('child-school-neighborhood').value,
    schoolId: $('child-school-select').value,
    schoolName: $('child-school-name').value,
    shift: $('child-shift').value,
    shiftStart: $('child-shift-start').value,
    shiftEnd: $('child-shift-end').value,
    livesWithParent: $('child-lives-with-parent').checked,
    homeAddress: $('child-home-address').value,
    homePhone: $('child-home-phone').value,
    activities: [...state.childActivities],
  };
}

async function loadChildDraft(index) {
  const draft = state.childDrafts[index] || {};
  state.childCurrent = index;
  $('child-name').value = draft.name || '';
  $('child-mobile-phone').value = draft.mobile || '';
  $('child-school-province').value = draft.province || '';
  $('child-school-name').value = draft.schoolName || '';
  $('child-shift').value = draft.shift || '';
  $('child-shift-start').value = draft.shiftStart || '';
  $('child-shift-end').value = draft.shiftEnd || '';
  $('child-lives-with-parent').checked = draft.livesWithParent ?? true;
  $('child-home-address').value = draft.homeAddress || '';
  $('child-home-phone').value = draft.homePhone || '';
  state.childActivities = draft.activities || [];
  renderChildActivities();
  updateChildHomeVisibility();
  $('child-school-city').innerHTML = '';
  $('child-school-neighborhood').innerHTML = '';
  $('child-school-neighborhood-wrap').classList.add('hidden');
  $('child-school-select').innerHTML = '';
  if (draft.province) {
    await loadSchoolCities(draft.province, draft.city);
  }
  if (draft.province && draft.city) {
    await loadSchoolNeighborhoods(draft.province, draft.city, draft.neighborhood, draft.schoolId);
  }
  updateChildProgress();
}

async function goToChildDraft(index) {
  const target = Math.max(Number(state.childTarget || 1), 1);
  const nextIndex = Math.min(Math.max(index, 1), target);
  if (nextIndex === state.childCurrent) return;
  captureChildDraft();
  await loadChildDraft(nextIndex);
}

function updateChildProgress() {
  const target = Math.max(Number(state.childTarget || 1), 1);
  state.childSaved = Math.min(Math.max(Number(state.childSaved || 0), 0), target);
  state.childCurrent = Math.min(Math.max(Number(state.childCurrent || 1), 1), target);
  const complete = state.childSavedIndexes.size >= target;
  $('child-form-title').textContent = complete
    ? `Children complete (${target} of ${target})`
    : `Add Child ${state.childCurrent} of ${target}`;
  const savedLabel = state.childSavedIndexes.has(state.childCurrent) ? ' Current child saved.' : '';
  $('child-progress').textContent = `${state.childSavedIndexes.size} of ${target} children saved.${savedLabel}`;
  $('child-prev-button').disabled = state.childCurrent <= 1;
  $('child-next-button').disabled = state.childCurrent >= target;
  $('child-form')
    .querySelectorAll('input, select, button')
    .forEach((el) => {
      if (el.id !== 'child-prev-button' && el.id !== 'child-next-button') {
        el.disabled = complete;
      }
    });
}

function updateMoneyMode() {
  const childMode = $('money-mode').value === 'child';
  $('bucket-fields').classList.toggle('hidden', !childMode);
}

async function ensureStripeCard() {
  if (stripeCard) return stripeCard;
  if (!window.Stripe) {
    throw new Error('Stripe.js did not load. Check internet access and try again.');
  }
  const config = await api('/payments/stripe/config');
  stripeClient = window.Stripe(config.publishable_key);
  stripeElements = stripeClient.elements();
  stripeCard = stripeElements.create('card');
  stripeCard.mount('#stripe-card-element');
  return stripeCard;
}

async function updatePaymentMethodFields() {
  const isStripe = $('money-payment-method').value === 'stripe_card';
  $('stripe-card-block').classList.toggle('hidden', !isStripe);
  setMessage('stripe-payment-status', '');
  if (isStripe) {
    try {
      await ensureStripeCard();
    } catch (error) {
      setMessage('stripe-payment-status', error.message, 'error');
    }
  }
}

function money(value) {
  return Number(value || 0).toFixed(2);
}

function renderKidEconomy() {
  const children = state.economyChildren || [];
  const currentValue = $('economy-child').value;
  $('economy-child').innerHTML = children
    .map((child) => `<option value="${child.id}">${child.name}</option>`)
    .join('');
  if (!children.length) {
    $('kid-economy-summary').textContent = 'No kids loaded yet.';
    $('kid-economy-detail').innerHTML = '';
    $('accelerometer-summary').textContent = 'No movement samples yet.';
    drawAccelerometerGraph([]);
    return;
  }
  if (currentValue && children.some((child) => String(child.id) === currentValue)) {
    $('economy-child').value = currentValue;
  } else if (!$('economy-child').value) {
    $('economy-child').value = String(children[0].id);
  }
  const selected = children.find((child) => String(child.id) === $('economy-child').value) || children[0];
  const warnings = selected.affected_buckets || [];
  $('kid-economy-summary').textContent =
    `Remaining ${money(selected.total_remaining)} | 7-day spend ${money(selected.spend_7_days)} | Daily rate ${money(selected.daily_spend_rate)}`;
  $('kid-economy-detail').innerHTML = `
    <div class="economy-metrics">
      <div class="metric-tile">Balance<strong>${money(selected.balance)}</strong></div>
      <div class="metric-tile">Remaining<strong>${money(selected.total_remaining)}</strong></div>
      <div class="metric-tile">7-day spend<strong>${money(selected.spend_7_days)}</strong></div>
      <div class="metric-tile">30-day spend<strong>${money(selected.spend_30_days)}</strong></div>
      <div class="metric-tile">Daily spend rate<strong>${money(selected.daily_spend_rate)}</strong></div>
      <div class="metric-tile">Estimated days left<strong>${selected.estimated_days_left ?? 'n/a'}</strong></div>
    </div>
    ${warnings.length ? `<p class="message error">Warning buckets: ${warnings.join(', ')}</p>` : ''}
    <div class="bucket-status-list">
      ${(selected.buckets || []).map((bucket) => `
        <div class="bucket-status ${bucket.status === 'warning' ? 'warning' : ''}">
          <strong>${bucket.name}</strong>
          <span>Remaining ${money(bucket.remaining)} | Used ${bucket.pct_used}% | Warning at ${bucket.alert_threshold_pct}%</span>
          <progress max="100" value="${Math.min(Math.max(Number(bucket.pct_used || 0), 0), 100)}"></progress>
        </div>
      `).join('')}
    </div>
  `;
  loadAccelerometerGraph(selected.id);
}

function drawAccelerometerGraph(samples) {
  const canvas = $('accelerometer-chart');
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  canvas.width = Math.max(Math.floor(rect.width * scale), 320);
  canvas.height = Math.floor(150 * scale);
  ctx.scale(scale, scale);
  const width = canvas.width / scale;
  const height = canvas.height / scale;
  ctx.clearRect(0, 0, width, height);

  const styles = getComputedStyle(document.documentElement);
  const line = styles.getPropertyValue('--line').trim() || '#dbe3ed';
  const brand = styles.getPropertyValue('--brand').trim() || '#2563eb';
  const muted = styles.getPropertyValue('--muted').trim() || '#607084';
  const ink = styles.getPropertyValue('--ink').trim() || '#172033';

  ctx.strokeStyle = line;
  ctx.lineWidth = 1;
  for (let i = 0; i <= 3; i += 1) {
    const y = 16 + i * ((height - 32) / 3);
    ctx.beginPath();
    ctx.moveTo(12, y);
    ctx.lineTo(width - 12, y);
    ctx.stroke();
  }

  if (!samples.length) {
    ctx.fillStyle = muted;
    ctx.font = '13px Segoe UI, Arial, sans-serif';
    ctx.fillText('No accelerometer samples yet', 18, height / 2);
    return;
  }

  const values = samples.map((sample) => Number(sample.magnitude || 0));
  const max = Math.max(...values, 1);
  const xStep = values.length > 1 ? (width - 24) / (values.length - 1) : 0;
  ctx.strokeStyle = brand;
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = 12 + index * xStep;
    const y = height - 16 - (value / max) * (height - 32);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = ink;
  values.forEach((value, index) => {
    const x = 12 + index * xStep;
    const y = height - 16 - (value / max) * (height - 32);
    ctx.beginPath();
    ctx.arc(x, y, 2.5, 0, Math.PI * 2);
    ctx.fill();
  });
}

async function loadAccelerometerGraph(childId) {
  if (!childId) return;
  try {
    const data = await api(`/child/${childId}/accelerometer?limit=60`);
    const samples = data.samples || [];
    drawAccelerometerGraph(samples);
    if (!samples.length) {
      $('accelerometer-summary').textContent = 'No movement samples yet.';
      return;
    }
    const latest = samples[samples.length - 1];
    const peak = Math.max(...samples.map((sample) => Number(sample.magnitude || 0)));
    $('accelerometer-summary').textContent =
      `Latest movement ${Number(latest.magnitude || 0).toFixed(2)} g | Peak ${peak.toFixed(2)} g`;
  } catch (error) {
    drawAccelerometerGraph([]);
    $('accelerometer-summary').textContent = 'Movement graph unavailable.';
  }
}

function focusFrame(id) {
  const el = $(id);
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  const first = el.querySelector('input, select, button');
  if (first) first.focus();
}

function normalizedDialNumber(number, countryCode) {
  const raw = String(number || '').trim();
  if (!raw) return '';
  if (raw.startsWith('+')) return `+${raw.replace(/\D/g, '')}`;
  const digits = raw.replace(/\D/g, '');
  const ccDigits = String(countryCode || '').replace(/\D/g, '');
  if (ccDigits && ccDigits.endsWith(digits)) return `+${ccDigits}`;
  return ccDigits ? `+${ccDigits}${digits}` : digits;
}

function parentPhoneCacheKey() {
  return `colepago_parent_phone_${state.userId || 'current'}`;
}

function callParentPhone() {
  const phone = state.parentPhone || localStorage.getItem(parentPhoneCacheKey()) || '';
  if (!phone) {
    setMessage('workspace-message', 'No parent mobile phone is loaded.', 'error');
    return;
  }
  window.location.href = `tel:${phone}`;
}

function setCountryCodeFromCountry() {
  $('parent-country-code').value = countryCodes[$('parent-country').value] || '+1';
}

function setSelectOptions(id, values, placeholder = 'Select') {
  $(id).innerHTML = [`<option value="">${placeholder}</option>`]
    .concat(values.map((value) => `<option value="${value}">${value}</option>`))
    .join('');
}

async function loadSchoolProvinces() {
  try {
    const data = await api('/geo/provinces');
    setSelectOptions('child-school-province', data.provinces || [], 'Select state/province');
  } catch {
    setSelectOptions('child-school-province', [], 'No provinces loaded');
  }
}

async function loadSchoolCities(province, selectedCity = '') {
  if (!province) return;
  const data = await api(`/geo/cities?province=${encodeURIComponent(province)}`);
  setSelectOptions('child-school-city', data.cities || [], 'Select city');
  $('child-school-city').value = selectedCity || '';
}

async function loadSchoolNeighborhoods(province, city, selectedNeighborhood = '', selectedSchoolId = '') {
  if (!province || !city) return;
  const data = await api(
    `/geo/neighborhoods?province=${encodeURIComponent(province)}&city=${encodeURIComponent(city)}`,
  );
  const neighborhoods = data.neighborhoods || [];
  $('child-school-neighborhood-wrap').classList.toggle('hidden', neighborhoods.length === 0);
  setSelectOptions('child-school-neighborhood', neighborhoods, 'Select neighborhood/comuna');
  $('child-school-neighborhood').value = selectedNeighborhood || '';
  await loadSchools(province, city, selectedNeighborhood, selectedSchoolId);
}

async function loadSchools(province, city, neighborhood = '', selectedSchoolId = '') {
  if (!province || !city) return;
  const params = new URLSearchParams({ province, city });
  if (neighborhood) params.set('neighborhood', neighborhood);
  const data = await api(`/geo/schools?${params.toString()}`);
  const schools = data.schools || [];
  $('child-school-select').innerHTML = '<option value="">Select school</option>' + schools
    .map((school) => `<option value="${school.id}" data-name="${school.name}">${school.name}</option>`)
    .join('');
  $('child-school-select').value = selectedSchoolId || '';
}

function moneyAmount() {
  return Number($('money-amount').value || 0);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForPaymentConfirmation(paymentId) {
  for (let i = 0; i < 12; i += 1) {
    const payment = await api(`/payments/${paymentId}`);
    if (payment.status === 'confirmed') return payment;
    if (payment.status === 'failed') throw new Error('Stripe payment failed.');
    await sleep(1000);
  }
  throw new Error('Stripe payment approved, but webhook confirmation is still pending. Keep stripe listen running.');
}

async function handleStripeWalletDeposit(amount) {
  await ensureStripeCard();
  setMessage('stripe-payment-status', 'Creating Stripe payment...', '');
  const intent = await api('/wallet/stripe/create-payment-intent', {
    method: 'POST',
    body: JSON.stringify({
      parent_id: state.userId,
      amount_pesos: amount,
    }),
  });
  setMessage('stripe-payment-status', 'Confirming card payment...', '');
  const result = await stripeClient.confirmCardPayment(intent.client_secret, {
    payment_method: { card: stripeCard },
  });
  if (result.error) {
    throw new Error(result.error.message || 'Stripe card payment failed.');
  }
  setMessage('stripe-payment-status', 'Payment approved. Waiting for Stripe webhook...', '');
  await waitForPaymentConfirmation(intent.payment_id);
  setMessage('stripe-payment-status', 'Stripe deposit confirmed.', 'success');
}

function fillAdminSettings(settings) {
  $('admin-fee-percent').value = settings.fee_percent ?? 2;
  $('admin-fee-payer').value = settings.fee_payer || 'merchant';
  $('admin-currency').value = settings.currency || 'ARS';
  $('admin-country').value = settings.country || '';
  $('admin-society-profile').value = settings.society_profile || '';
  $('admin-religion-context').value = settings.religion_context || '';
  $('admin-local-policy-notes').value = settings.local_policy_notes || '';
  $('admin-merchant-fee-disclosure').value = settings.merchant_fee_disclosure || '';
}

async function loadAdminSettings() {
  if (!state.isAdmin) return;
  try {
    const settings = await api('/admin/settings');
    fillAdminSettings(settings);
    setMessage('admin-settings-status', settings.updated_at ? `Last updated ${settings.updated_at}` : '');
  } catch (error) {
    setMessage('admin-settings-status', error.message, 'error');
  }
}

function bucketValue(id) {
  return Number($(id).value || 0);
}

const bucketDefinitions = [
  { name: 'Lunch / Snacks', amountId: 'bucket-lunch', thresholdId: 'threshold-lunch' },
  { name: 'Books', amountId: 'bucket-books', thresholdId: 'threshold-books' },
  { name: 'Fotocopies', amountId: 'bucket-fotocopies', thresholdId: 'threshold-fotocopies' },
  { name: 'Transport', amountId: 'bucket-transport', thresholdId: 'threshold-transport' },
  { name: 'General', amountId: 'bucket-general', thresholdId: 'threshold-general-bucket' },
];

function thresholdValue(id, fallback = 80) {
  const value = Number($(id).value || fallback);
  return Math.min(Math.max(Math.round(value || fallback), 1), 100);
}

function thresholdPayload() {
  const fallback = thresholdValue('threshold-general', 80);
  return bucketDefinitions.map((bucket) => ({
    name: bucket.name,
    alert_threshold_pct: thresholdValue(bucket.thresholdId, fallback),
  }));
}

async function loadSelectedChildThresholds() {
  const childId = Number($('money-child').value || 0);
  if (!childId) return;
  try {
    const buckets = await api(`/child/${childId}/wallet_buckets`);
    const values = [];
    buckets.forEach((bucket) => {
      const definition = bucketDefinitions.find((item) => item.name === bucket.name);
      if (!definition) return;
      const threshold = Number(bucket.alert_threshold_pct || 80);
      $(definition.thresholdId).value = threshold;
      values.push(threshold);
    });
    if (values.length && values.every((value) => value === values[0])) {
      $('threshold-general').value = values[0];
    }
  } catch {
    // Existing thresholds are optional for first-time allocation.
  }
}

async function saveThresholds() {
  const childId = Number($('money-child').value || 0);
  if (!childId) throw new Error('Select a child');
  await api(`/child/${childId}/wallet_buckets/thresholds`, {
    method: 'PUT',
    body: JSON.stringify({
      parent_id: state.userId,
      default_threshold_pct: thresholdValue('threshold-general', 80),
      buckets: thresholdPayload(),
    }),
  });
}

function clearActivityDraft() {
  $('activity-period').value = 'after_shift';
  $('activity-type').value = '';
  $('activity-name').value = '';
  $('activity-start').value = '';
  $('activity-end').value = '';
  $('activity-address').value = '';
  $('activity-institution').value = '';
  $('activity-phone').value = '';
  $('activity-professor').value = '';
}

function renderChildActivities() {
  $('child-activities-list').innerHTML = state.childActivities
    .map((activity) => (
      `<div class="activity-item">${activity.period === 'before_shift' ? 'Before shift' : 'After shift'} - ${activity.type || 'Activity'} - ${activity.name || ''} ${activity.start || ''}${activity.end ? ` to ${activity.end}` : ''}<br>${activity.institution || ''}${activity.address ? `, ${activity.address}` : ''}${activity.phone ? `, ${activity.phone}` : ''}</div>`
    ))
    .join('');
}

function addChildActivity() {
  const type = $('activity-type').value;
  const name = $('activity-name').value.trim();
  if (!type && !name) return;
  state.childActivities.push({
    period: $('activity-period').value,
    type: type || 'Other',
    name,
    start: $('activity-start').value.trim(),
    end: $('activity-end').value.trim(),
    address: $('activity-address').value.trim(),
    institution: $('activity-institution').value.trim(),
    phone: $('activity-phone').value.trim(),
    professor: $('activity-professor').value.trim(),
  });
  clearActivityDraft();
  renderChildActivities();
}

async function loadParentDashboardData() {
  if (state.role !== 'parent') return;
  try {
    state.children = await api(`/parent/${state.userId}/children`);
    const economy = await api(`/parent/${state.userId}/dashboard_economy`);
    state.economyChildren = economy.children || [];
    renderKidEconomy();
    state.childSaved = Math.min(state.children.length, Math.max(Number(state.childTarget || 1), 1));
    if (state.childSavedIndexes.size === 0) {
      state.childSavedIndexes = new Set(
        Array.from({ length: state.childSaved }, (_, index) => index + 1),
      );
      state.childCurrent = Math.min(state.childSaved + 1, Math.max(Number(state.childTarget || 1), 1));
    }
    updateChildProgress();
    $('money-child').innerHTML = state.children
      .map((child) => `<option value="${child.id}">${child.name}</option>`)
      .join('');
    await loadSelectedChildThresholds();
    const summary = await api(`/parent/${state.userId}/wallet_summary`);
    $('wallet-summary').textContent =
      `Parent wallet: ${Number(summary.parent_balance || 0).toFixed(2)} | Applied to children: ${Number(summary.children_balance || 0).toFixed(2)}`;
  } catch {
    $('wallet-summary').textContent = '';
  }
}

async function loadProfileForRole() {
  setMessage('workspace-message', '');
  if (state.role === 'parent') {
    try {
      const profile = await api(`/parent/${state.userId}/profile`);
      $('parent-name').value = profile.name || '';
      $('parent-relationship').value = profile.relationship_to_child || '';
      $('parent-children-count').value = profile.children_using_colepago || '';
      $('parent-mobile').value = profile.mobile_phone || '';
      $('parent-country').value = profile.country || 'United States';
      $('parent-country-code').value = profile.country_code || '+1';
      state.parentPhone = normalizedDialNumber(profile.mobile_phone, profile.country_code);
      if (state.parentPhone) {
        localStorage.setItem(parentPhoneCacheKey(), state.parentPhone);
      }
      $('parent-home-address').value = profile.home_address || '';
      $('parent-home-phone').value = profile.home_phone || '';
      state.childTarget = Math.max(Number(profile.children_using_colepago || 1), 1);
      updateChildProgress();
      await loadSchoolProvinces();
      await loadParentDashboardData();
    } catch {
      updateChildProgress();
      await loadSchoolProvinces();
      await loadParentDashboardData();
    }
  }
  if (state.role === 'merchant') {
    try {
      const profile = await api(`/merchant/${state.userId}/profile`);
      $('merchant-place').value = profile.place_scope || '';
      $('merchant-business-name').value = profile.business_name || '';
      $('merchant-address').value = profile.address || '';
      $('merchant-personal-name').value = profile.personal_name || '';
      $('merchant-mobile').value = profile.mobile_phone || '';
      $('merchant-country-code').value = profile.country_code || '+54';
      $('merchant-transfer-type').value = profile.transfer_account_type || '';
      $('merchant-transfer-account').value = profile.transfer_account || '';
      $('merchant-transfer-alias').value = profile.transfer_account_alias || '';
    } catch {
      setMessage('workspace-message', '');
    }
  }
}

async function startSession(payload) {
  saveSession(payload);
  showWorkspace();
  await loadProfileForRole();
}

window.addEventListener('DOMContentLoaded', () => {
  applyTheme();
  $('login-tab').addEventListener('click', () => switchAuth('login'));
  $('register-tab').addEventListener('click', () => switchAuth('register'));
  $('theme-toggle-button').addEventListener('click', () => {
    applyTheme(state.theme === 'dark' ? 'light' : 'dark');
  });
  $('logout-button').addEventListener('click', () => {
    clearSession();
    showAuth();
  });
  $('admin-menu-button').addEventListener('click', () => focusFrame('admin-workspace'));

  $('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    setMessage('auth-message', 'Signing in...');
    if (!isValidEmail($('login-email').value)) {
      setMessage('auth-message', 'Enter a valid email address.', 'error');
      return;
    }
    try {
      const payload = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: $('login-email').value.trim(),
          password: $('login-password').value,
        }),
      });
      await startSession(payload);
    } catch (error) {
      setMessage('auth-message', error.message, 'error');
    }
  });

  $('register-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    setMessage('auth-message', 'Creating account...');
    if (!isValidEmail($('register-email').value)) {
      setMessage('auth-message', 'Enter a valid email address.', 'error');
      return;
    }
    try {
      const payload = await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          role: $('register-role').value,
          name: $('register-name').value.trim(),
          username: $('register-username').value.trim() || null,
          email: $('register-email').value.trim(),
          password: $('register-password').value,
        }),
      });
      await startSession(payload);
    } catch (error) {
      setMessage('auth-message', error.message, 'error');
    }
  });

  $('admin-settings-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const response = await api('/admin/settings', {
        method: 'PUT',
        body: JSON.stringify({
          fee_percent: Number($('admin-fee-percent').value || 0),
          fee_payer: $('admin-fee-payer').value,
          currency: $('admin-currency').value.trim(),
          country: $('admin-country').value.trim(),
          society_profile: $('admin-society-profile').value.trim(),
          religion_context: $('admin-religion-context').value.trim(),
          local_policy_notes: $('admin-local-policy-notes').value.trim(),
          merchant_fee_disclosure: $('admin-merchant-fee-disclosure').value.trim(),
        }),
      });
      fillAdminSettings(response.settings);
      setMessage('admin-settings-status', 'Admin settings saved.', 'success');
    } catch (error) {
      setMessage('admin-settings-status', error.message, 'error');
    }
  });

  $('parent-profile-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const childrenCount = Math.max(Number($('parent-children-count').value), 1);
    try {
      await api(`/parent/${state.userId}/profile`, {
        method: 'PUT',
        body: JSON.stringify({
          relationship_to_child: $('parent-relationship').value,
          name: $('parent-name').value.trim(),
          children_using_colepago: childrenCount,
          mobile_phone: $('parent-mobile').value.trim(),
          country: $('parent-country').value,
          country_code: $('parent-country-code').value.trim(),
          home_address: $('parent-home-address').value.trim(),
          home_phone: $('parent-home-phone').value.trim(),
        }),
      });
      state.childTarget = childrenCount;
      await loadParentDashboardData();
      setMessage('workspace-message', 'Parent information saved.', 'success');
    } catch (error) {
      setMessage('workspace-message', error.message, 'error');
    }
  });

  $('child-lives-with-parent').addEventListener('change', updateChildHomeVisibility);
  $('child-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (state.childSavedIndexes.has(state.childCurrent)) {
      updateChildProgress();
      setMessage('workspace-message', 'This child is already saved. Move to another child.', 'success');
      return;
    }
    if (state.childSavedIndexes.size >= state.childTarget) {
      updateChildProgress();
      setMessage('workspace-message', 'All children are already saved. You can load money now.', 'success');
      return;
    }
    captureChildDraft();
    const livesWithParent = $('child-lives-with-parent').checked;
    const body = {
      parent_id: state.userId,
      full_name: $('child-name').value.trim(),
      mobile_phone: $('child-mobile-phone').value.trim(),
      school_id: $('child-school-select').value || null,
      school_name: $('child-school-name').value.trim(),
      shift: $('child-shift').value,
      shift_start: $('child-shift-start').value.trim(),
      shift_end: $('child-shift-end').value.trim(),
      activities: state.childActivities,
      lives_with_parent: livesWithParent,
    };
    if (!livesWithParent) {
      body.home_address = $('child-home-address').value.trim();
      body.home_phone = $('child-home-phone').value.trim();
    }
    try {
      await api('/parent/add-child', {
        method: 'POST',
        body: JSON.stringify(body),
      });
      state.childSavedIndexes.add(state.childCurrent);
      state.childSaved = state.childSavedIndexes.size;
      updateChildProgress();
      await loadParentDashboardData();
      if (state.childSavedIndexes.size >= state.childTarget) {
        setMessage('workspace-message', 'Setup complete. You can load money now.', 'success');
      } else {
        setMessage('workspace-message', 'Child saved.', 'success');
        const nextOpen = Array.from({ length: state.childTarget }, (_, i) => i + 1)
          .find((index) => !state.childSavedIndexes.has(index));
        if (nextOpen) await loadChildDraft(nextOpen);
      }
    } catch (error) {
      setMessage('workspace-message', error.message, 'error');
    }
  });

  $('parent-country').addEventListener('change', setCountryCodeFromCountry);
  $('economy-child').addEventListener('change', () => {
    renderKidEconomy();
  });
  $('menu-parent-info').addEventListener('click', () => focusFrame('parent-profile-form'));
  $('menu-kid-info').addEventListener('click', () => focusFrame('child-form'));
  $('menu-money-info').addEventListener('click', () => focusFrame('money-form'));
  $('menu-call-parent').addEventListener('click', callParentPhone);
  $('add-activity-button').addEventListener('click', addChildActivity);
  $('child-prev-button').addEventListener('click', () => goToChildDraft(state.childCurrent - 1));
  $('child-next-button').addEventListener('click', () => goToChildDraft(state.childCurrent + 1));
  $('child-school-province').addEventListener('change', async () => {
    const province = $('child-school-province').value;
    $('child-school-city').innerHTML = '';
    $('child-school-neighborhood').innerHTML = '';
    $('child-school-neighborhood-wrap').classList.add('hidden');
    $('child-school-select').innerHTML = '';
    $('child-school-name').value = '';
    if (province) await loadSchoolCities(province);
  });
  $('child-school-city').addEventListener('change', async () => {
    const province = $('child-school-province').value;
    const city = $('child-school-city').value;
    $('child-school-neighborhood').innerHTML = '';
    $('child-school-neighborhood-wrap').classList.add('hidden');
    $('child-school-select').innerHTML = '';
    $('child-school-name').value = '';
    if (province && city) await loadSchoolNeighborhoods(province, city);
  });
  $('child-school-neighborhood').addEventListener('change', async () => {
    await loadSchools(
      $('child-school-province').value,
      $('child-school-city').value,
      $('child-school-neighborhood').value,
    );
  });
  $('child-school-select').addEventListener('change', () => {
    const option = $('child-school-select').selectedOptions[0];
    $('child-school-name').value = option?.dataset.name || $('child-school-name').value;
  });
  $('money-mode').addEventListener('change', updateMoneyMode);
  $('money-payment-method').addEventListener('change', updatePaymentMethodFields);
  $('money-child').addEventListener('change', loadSelectedChildThresholds);
  $('save-thresholds-button').addEventListener('click', async () => {
    try {
      await saveThresholds();
      setMessage('workspace-message', 'Bucket warning thresholds saved.', 'success');
    } catch (error) {
      setMessage('workspace-message', error.message, 'error');
    }
  });
  $('money-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const amount = moneyAmount();
    const childMode = $('money-mode').value === 'child';
    const paymentMethod = $('money-payment-method').value;
    try {
      if (paymentMethod === 'stripe_card') {
        await handleStripeWalletDeposit(amount);
      } else {
        await api('/wallet/fund', {
          method: 'POST',
          body: JSON.stringify({
            parent_id: state.userId,
            amount_pesos: amount,
            payment_method: paymentMethod,
            bank_account: 'manual-test',
            mp_token: 'manual-test',
          }),
        });
      }

      if (childMode) {
        const thresholds = thresholdPayload();
        const buckets = bucketDefinitions
          .map((bucket) => ({
            name: bucket.name,
            amount: bucketValue(bucket.amountId),
            alert_threshold_pct: thresholds.find((item) => item.name === bucket.name).alert_threshold_pct,
          }))
          .filter((bucket) => bucket.amount > 0);
        const total = buckets.reduce((sum, bucket) => sum + bucket.amount, 0);
        if (Math.abs(total - amount) > 0.01) {
          throw new Error('Bucket amounts must equal the amount.');
        }
        await api('/wallet/allocate', {
          method: 'POST',
          body: JSON.stringify({
            parent_id: state.userId,
            child_id: Number($('money-child').value),
            amount_pesos: amount,
            buckets,
          }),
        });
      }

      $('money-amount').value = '';
      bucketDefinitions.forEach((bucket) => {
        const id = bucket.amountId;
        $(id).value = '';
      });
      await loadParentDashboardData();
      setMessage('workspace-message', childMode ? 'Money applied to child buckets.' : 'Money loaded to parent wallet.', 'success');
    } catch (error) {
      setMessage('workspace-message', error.message, 'error');
    }
  });

  $('merchant-profile-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api(`/merchant/${state.userId}/profile`, {
        method: 'PUT',
        body: JSON.stringify({
          place_scope: $('merchant-place').value,
          business_name: $('merchant-business-name').value.trim(),
          address: $('merchant-address').value.trim(),
          personal_name: $('merchant-personal-name').value.trim(),
          mobile_phone: $('merchant-mobile').value.trim(),
          country_code: $('merchant-country-code').value.trim(),
          transfer_account_type: $('merchant-transfer-type').value,
          transfer_account: $('merchant-transfer-account').value.trim(),
          transfer_account_alias: $('merchant-transfer-alias').value.trim(),
        }),
      });
      setMessage('workspace-message', 'Merchant information saved.', 'success');
    } catch (error) {
      setMessage('workspace-message', error.message, 'error');
    }
  });

  updateChildHomeVisibility();
  updateMoneyMode();
  if (state.token && state.userId && state.role) {
    showWorkspace();
    loadProfileForRole();
  } else {
    showAuth();
  }
});
