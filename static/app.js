const i18n = {
  es: {
    title: "ColePago | Billetera Escolar Inteligente",
    h1: "Billetera digital para escuelas, padres y niños",
    sub: "Los padres distribuyen dinero por buckets de gasto y el backend solo maneja tokens virtuales, nunca dinero real.",
    b1: "Backend: FastAPI + PostgreSQL",
    b2: "Pagos: Stripe / Mercado Pago",
    b3: "IA: biometría y control",
    cta1: "Ver arquitectura",
    cta2: "Descargar brochure ES",
    sec1: "Cómo funciona",
    sec1p: "Flujo seguro para convertir dinero real en tokens de uso escolar.",
    step1t: "1) Carga de saldo",
    step1p: "Padres cargan la billetera vía Stripe o Mercado Pago con TLS.",
    step2t: "2) Distribución por buckets",
    step2p: "Asignación por categorías: útiles, snacks, lunch, books y fotocopies.",
    step3t: "3) Uso controlado",
    step3p: "Niños usan tokens y los padres reciben notificaciones y reportes.",
    sec2: "Arquitectura",
    sec2p: "Separación clara entre pagos reales y economía virtual interna.",
    sec3: "Indicadores",
    sec3p: "Ejemplo de distribución y consumo por buckets para decisiones familiares.",
    f: "ColePago 2026 · Seguridad, trazabilidad y educación financiera"
  },
  en: {
    title: "ColePago | Smart School Wallet",
    h1: "Digital wallet for schools, parents, and kids",
    sub: "Parents allocate funds into spending buckets, and the backend handles virtual tokens only, never real money.",
    b1: "Backend: FastAPI + PostgreSQL",
    b2: "Payments: Stripe / Mercado Pago",
    b3: "AI: biometrics and control",
    cta1: "View architecture",
    cta2: "Download brochure EN",
    sec1: "How it works",
    sec1p: "Secure flow to convert real money into school-use tokens.",
    step1t: "1) Wallet top-up",
    step1p: "Parents fund the wallet through Stripe or Mercado Pago over TLS.",
    step2t: "2) Bucket allocation",
    step2p: "Funds are split by categories: school supplies, snacks, lunch, books, and photocopies.",
    step3t: "3) Controlled spending",
    step3p: "Kids spend tokens and parents get notifications and reports.",
    sec2: "Architecture",
    sec2p: "Clear separation between real-money payments and internal virtual economy.",
    sec3: "Key metrics",
    sec3p: "Sample bucket distribution and usage to support family decisions.",
    f: "ColePago 2026 · Security, traceability, and financial education"
  }
};

const bucketChartI18n = {
  es: {
    labels: ['Utiles', 'Snacks', 'Lunch', 'Books', 'Fotocopies'],
    assigned: 'Asignado',
    used: 'Consumido',
  },
  en: {
    labels: ['Supplies', 'Snacks', 'Lunch', 'Books', 'Photocopies'],
    assigned: 'Allocated',
    used: 'Used',
  },
};

const bucketAssignedData = [120, 80, 140, 70, 60];
const bucketUsedData = [85, 52, 98, 44, 31];
let bucketChart = null;

function updateChartLanguage(lang) {
  if (!bucketChart) return;
  const c = bucketChartI18n[lang] || bucketChartI18n.es;
  bucketChart.data.labels = c.labels;
  bucketChart.data.datasets[0].label = c.assigned;
  bucketChart.data.datasets[1].label = c.used;
  bucketChart.update();
}

function applyLang(lang) {
  const t = i18n[lang] || i18n.es;
  document.documentElement.lang = lang;
  document.title = t.title;
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.textContent = t[key];
  });

  document.getElementById('btn-es').classList.toggle('active', lang === 'es');
  document.getElementById('btn-en').classList.toggle('active', lang === 'en');

  const brochureLink = document.getElementById('brochure-link');
  brochureLink.href = lang === 'en' ? '/brochure/colepago_onepage_brochure.md' : '/brochure/colepago_onepage_brochure_es.md';

  updateChartLanguage(lang);
  localStorage.setItem('colepago_lang', lang);
}

window.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('colepago_lang') || 'es';
  applyLang(saved);

  document.getElementById('btn-es').addEventListener('click', () => applyLang('es'));
  document.getElementById('btn-en').addEventListener('click', () => applyLang('en'));

  const chart = document.getElementById('bucket-chart');
  if (window.Chart && chart) {
    bucketChart = new Chart(chart, {
      type: 'bar',
      data: {
        labels: bucketChartI18n.es.labels,
        datasets: [
          { label: bucketChartI18n.es.assigned, data: bucketAssignedData, backgroundColor: '#0f9d8a' },
          { label: bucketChartI18n.es.used, data: bucketUsedData, backgroundColor: '#ef6c00' }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    // Respect previously selected language after chart instantiation
    updateChartLanguage(saved);
  }
});
