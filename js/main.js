const menuToggle = document.querySelector('.menu-toggle');
const hamburger = document.querySelector('.hamburger');
const mainNav = document.querySelector('.main-nav');
const mobileNav = document.querySelector('.mobile-nav');
const pageType = document.body.dataset.page || 'home';

// Simple Markdown → HTML converter
function markdownToHtml(md) {
  if (!md) return '';
  let html = md
    // Escape HTML entities first
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold + Italic
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    // Horizontal rules
    .replace(/^---+$/gm, '<hr>')
    // Unordered lists
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    // Paragraphs (double newline)
    .replace(/\n\n+/g, '</p><p>')
    // Single newlines within paragraphs
    .replace(/\n/g, '<br>');
  
  // Wrap list items
  html = html.replace(/(<li>.*?<\/li>)(?:\s*<br>)*/gs, (match) => {
    return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
  });
  
  // Wrap in paragraph tags
  html = '<p>' + html + '</p>';
  
  // Clean up empty paragraphs and broken tags
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p>\s*(<h[1-3]>)/g, '$1');
  html = html.replace(/(<\/h[1-3]>)\s*<\/p>/g, '$1');
  html = html.replace(/<p>\s*(<hr>)\s*<\/p>/g, '$1');
  html = html.replace(/<p>\s*(<ul>)/g, '$1');
  html = html.replace(/(<\/ul>)\s*<\/p>/g, '$1');
  
  return html;
}
const POSTS_URL = 'data/posts.json';
const COINGECKO_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,ripple&vs_currencies=usd&include_24hr_change=true';
const TRENDING_COINS_URL = 'https://api.coingecko.com/api/v3/search/trending';
const RANKING_COINS_URL = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=24h';
const FEAR_GREED_URL = 'https://api.alternative.me/fng/?limit=1';
const POSTS_PER_PAGE = 6;
const coinConfig = [
  { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', icon: '₿' },
  { id: 'ethereum', symbol: 'ETH', name: 'Ethereum', icon: 'Ξ' },
  { id: 'solana', symbol: 'SOL', name: 'Solana', icon: '◎' },
  { id: 'binancecoin', symbol: 'BNB', name: 'BNB', icon: '◈' },
  { id: 'ripple', symbol: 'XRP', name: 'XRP', icon: '✕' }
];

const state = {
  posts: null,
  currentFilter: 'all',
  currentPage: 1,
  searchTerm: ''
};

function closeMobileMenu() {
  if (mobileNav) {
    mobileNav.classList.remove('open');
  }
  if (hamburger) {
    hamburger.setAttribute('aria-expanded', 'false');
  }
}

function toggleMobileMenu() {
  if (!mobileNav || !hamburger) return;
  const isOpen = mobileNav.classList.toggle('open');
  hamburger.setAttribute('aria-expanded', String(isOpen));
}

window.toggleMobileMenu = toggleMobileMenu;

function updateThemeIcon() {
  const themeIcon = document.querySelector('.theme-icon');
  if (!themeIcon) return;
  const isLight = document.body.classList.contains('light-mode');
  themeIcon.textContent = isLight ? '☀️' : '🌙';
}

function updateLogos() {
  const isLight = document.body.classList.contains('light-mode');
  document.querySelectorAll('.brand-logo').forEach(img => {
    img.src = isLight ? 'images/logo-combo-black.png' : 'images/logo-combo.png';
  });
}

function toggleTheme() {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
  updateThemeIcon();
  updateLogos();

  // Reload TradingView widgets with correct theme.
  // TradingView widgets don't support dynamic theme change,
  // so this remains a known limitation until a full re-render is triggered.
  if (document.getElementById('tradingview_btc') || document.getElementById('tradingview_eth')) {
    initTradingViewWidgets(true);
  }
}

(function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    document.body.classList.add('light-mode');
  }
  updateThemeIcon();
  updateLogos();
})();

window.toggleTheme = toggleTheme;

if (menuToggle && mainNav) {
  menuToggle.addEventListener('click', () => {
    const isOpen = mainNav.classList.toggle('is-open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
  });

  mainNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mainNav.classList.remove('is-open');
      menuToggle.setAttribute('aria-expanded', 'false');
    });
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 860) {
      mainNav.classList.remove('is-open');
      menuToggle.setAttribute('aria-expanded', 'false');
    }
  });
}

if (mobileNav) {
  mobileNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      closeMobileMenu();
    });
  });
}

window.addEventListener('resize', () => {
  if (window.innerWidth > 768) {
    closeMobileMenu();
  }
});

function formatDate(dateString) {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return dateString;
  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(date);
}

function formatPrice(value) {
  if (typeof value !== 'number') return 'Đang tải...';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: value >= 1000 ? 0 : 2
  }).format(value);
}

function formatChange(value) {
  if (typeof value !== 'number') return '--';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function estimateReadTime(post) {
  const plainText = String(post.content || '').replace(/<[^>]+>/g, ' ');
  const words = plainText.trim().split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(3, Math.round(words / 180));
  return `${minutes} phút đọc`;
}

function categoryLabel(category) {
  const labels = {
    analysis: 'Phân tích',
    news: 'Tin tức',
    commodity: 'Hàng hóa',
    altcoin: 'Altcoin',
    onchain: 'On-chain'
  };
  return labels[category] || category;
}

function categoryClass(category) {
  return category === 'analysis' ? 'category-tag' : 'category-tag muted-accent';
}

function articleUrl(post) {
  return `/${post.slug || post.id}.html`;
}

function createMetaHTML(post) {
  return `<div class="article-meta"><span>${formatDate(post.date)}</span><span>${estimateReadTime(post)}</span></div>`;
}

function createHeroArticle(post) {
  return `
    <img src="${post.image}" alt="${post.title}">
    <div class="hero-overlay"></div>
    <div class="hero-content">
      <span class="${categoryClass(post.category)}">${categoryLabel(post.category)}</span>
      <p class="eyebrow">Bài nổi bật</p>
      <h1>${post.title}</h1>
      <p class="hero-summary">${post.summary}</p>
      ${createMetaHTML(post)}
    </div>
  `;
}

function createCompactArticle(post) {
  return `
    <img src="${post.image}" alt="${post.title}">
    <div>
      <span class="${categoryClass(post.category)}">${categoryLabel(post.category)}</span>
      <h2>${post.title}</h2>
      ${createMetaHTML(post)}
    </div>
  `;
}

function createNewsCard(post) {
  return `
    <img src="${post.image}" alt="${post.title}">
    <div class="card-content">
      <span class="${categoryClass(post.category)}">${categoryLabel(post.category)}</span>
      <h3>${post.title}</h3>
      <p>${post.summary}</p>
      ${createMetaHTML(post)}
    </div>
  `;
}

function createAnalysisItem(post) {
  return `
    <img src="${post.image}" alt="${post.title}">
    <div>
      <span class="${categoryClass(post.category)}">${categoryLabel(post.category)}</span>
      <h3>${post.title}</h3>
      <p>${post.summary}</p>
      ${createMetaHTML(post)}
    </div>
  `;
}

function makeArticleClickable(element, post) {
  element.classList.add('clickable-card');
  element.setAttribute('role', 'link');
  element.setAttribute('tabindex', '0');
  element.addEventListener('click', () => {
    window.location.href = articleUrl(post);
  });
  element.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      window.location.href = articleUrl(post);
    }
  });
}

function renderPopularPosts(posts) {
  const popularList = document.querySelector('[data-popular-list]');
  if (!popularList || !Array.isArray(posts) || !posts.length) return;

  popularList.innerHTML = '';
  posts.slice(0, 5).forEach((post) => {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = articleUrl(post);
    link.textContent = post.title;
    item.appendChild(link);
    popularList.appendChild(item);
  });
}

function getHomeNewsSource() {
  if (!Array.isArray(state.posts)) return [];
  return state.posts.slice(1);
}

function normalizeText(value) {
  return String(value || '').toLowerCase().trim();
}

function getFilteredPosts() {
  const searchTerm = normalizeText(state.searchTerm);
  return getHomeNewsSource().filter((post) => {
    const matchesFilter = state.currentFilter === 'all'
      ? true
      : state.currentFilter === 'news'
        ? ['news', 'altcoin', 'onchain'].includes(post.category)
        : post.category === state.currentFilter;

    if (!matchesFilter) return false;
    if (!searchTerm) return true;

    const haystack = `${post.title} ${post.summary}`.toLowerCase();
    return haystack.includes(searchTerm);
  });
}

function updatePageParam(page) {
  const url = new URL(window.location.href);
  if (page > 1) {
    url.searchParams.set('page', String(page));
  } else {
    url.searchParams.delete('page');
  }
  window.history.replaceState({}, '', url);
}

function updatePagination(totalItems) {
  const currentPageEl = document.getElementById('current-page');
  const totalPagesEl = document.getElementById('total-pages');
  const prevBtn = document.querySelector('.prev-btn');
  const nextBtn = document.querySelector('.next-btn');
  const pagination = document.querySelector('.pagination');
  const totalPages = Math.max(1, Math.ceil(totalItems / POSTS_PER_PAGE));

  state.currentPage = Math.min(Math.max(state.currentPage, 1), totalPages);

  if (currentPageEl) currentPageEl.textContent = String(state.currentPage);
  if (totalPagesEl) totalPagesEl.textContent = String(totalPages);
  if (prevBtn) prevBtn.disabled = state.currentPage <= 1;
  if (nextBtn) nextBtn.disabled = state.currentPage >= totalPages;
  if (pagination) pagination.hidden = totalItems <= POSTS_PER_PAGE;

  updatePageParam(state.currentPage);
}

function renderNewsGrid(postsToRender) {
  const newsGrid = document.querySelector('[data-news-grid]');
  if (!newsGrid) return;

  if (!Array.isArray(postsToRender) || !postsToRender.length) {
    newsGrid.innerHTML = '<div class="empty-state article-panel">Không tìm thấy bài viết phù hợp.</div>';
    return;
  }

  newsGrid.innerHTML = '';
  postsToRender.forEach((post, index) => {
    const article = document.createElement('article');
    article.className = 'news-card article-panel';
    article.dataset.category = post.category;
    article.innerHTML = createNewsCard(post);
    makeArticleClickable(article, post);
    newsGrid.appendChild(article);
  });
}

function renderPagedNews() {
  if (pageType !== 'home') return;

  const posts = getFilteredPosts();
  const totalPages = Math.max(1, Math.ceil(posts.length / POSTS_PER_PAGE));
  if (state.currentPage > totalPages) {
    state.currentPage = totalPages;
  }

  const startIndex = (state.currentPage - 1) * POSTS_PER_PAGE;
  const visiblePosts = posts.slice(startIndex, startIndex + POSTS_PER_PAGE);
  renderNewsGrid(visiblePosts);
  updatePagination(posts.length);
}

function updateFilterNotice() {
  const filterNotice = document.querySelector('[data-filter-notice]');
  if (!filterNotice) return;

  const parts = [];
  if (state.currentFilter === 'analysis') {
    parts.push('Đang lọc các bài phân tích thị trường.');
  } else if (state.currentFilter === 'news') {
    parts.push('Đang lọc các bài tin tức và dòng tiền thị trường.');
  } else if (state.currentFilter === 'commodity') {
    parts.push('Đang lọc các bài liên quan hàng hóa.');
  }

  if (state.searchTerm.trim()) {
    parts.push(`Từ khóa: “${state.searchTerm.trim()}”.`);
  }

  filterNotice.hidden = parts.length === 0;
  filterNotice.textContent = parts.join(' ');
}

function applyFilter(filter, options = {}) {
  if (pageType !== 'home' || !Array.isArray(state.posts)) return;

  state.currentFilter = filter;
  state.currentPage = 1;
  updateFilterNotice();
  renderPagedNews();

  document.querySelectorAll('.main-nav a[data-filter], .mobile-nav a[data-filter]').forEach((link) => {
    link.classList.toggle('is-active', link.dataset.filter === filter);
  });

  const shouldScroll = options.scroll !== false;
  const targetId = filter === 'analysis' ? 'market-analysis' : 'latest-news';
  const target = document.getElementById(targetId);
  if (shouldScroll && target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function bindHomeNavigation() {
  if (pageType !== 'home') return;

  document.querySelectorAll('.main-nav a[data-filter], .mobile-nav a[data-filter]').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      applyFilter(link.dataset.filter || 'all');
    });
  });
}

function hydrateInitialPageFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const page = Number.parseInt(params.get('page') || '1', 10);
  if (Number.isFinite(page) && page > 0) {
    state.currentPage = page;
  }
}

function renderHomePage(posts) {
  const heroArticle = document.querySelector('[data-hero-article]');
  const heroSideList = document.querySelector('[data-hero-side-list]');
  const analysisList = document.querySelector('[data-analysis-list]');
  if (!heroArticle || !heroSideList || !analysisList || !posts.length) return;

  const latestPost = posts[0];
  heroArticle.innerHTML = createHeroArticle(latestPost);
  makeArticleClickable(heroArticle, latestPost);

  heroSideList.innerHTML = '';
  posts.slice(1, 4).forEach((post) => {
    const article = document.createElement('article');
    article.className = 'side-article article-panel compact-panel';
    article.innerHTML = createCompactArticle(post);
    makeArticleClickable(article, post);
    heroSideList.appendChild(article);
  });

  analysisList.innerHTML = '';
  posts.filter((post) => post.category === 'analysis').forEach((post) => {
    const article = document.createElement('article');
    article.className = 'analysis-item article-panel';
    article.dataset.category = post.category;
    article.innerHTML = createAnalysisItem(post);
    makeArticleClickable(article, post);
    analysisList.appendChild(article);
  });

  updateFilterNotice();
  renderPagedNews();
}

async function loadPosts() {
  try {
    const response = await fetch(POSTS_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const posts = await response.json();
    if (!Array.isArray(posts) || !posts.length) throw new Error('Invalid posts payload');
    state.posts = posts.sort((a, b) => new Date(b.date) - new Date(a.date));
    renderPopularPosts(state.posts);

    if (pageType === 'home') {
      hydrateInitialPageFromUrl();
      renderHomePage(state.posts);
      applyFilter('all', { scroll: false });
    }

    if (pageType === 'article') {
      renderArticlePage(state.posts);
    }
  } catch (error) {
    console.warn('Không thể tải posts.json, giữ nguyên placeholder content.', error);
  }
}

function updateMetaTag(selector, attr, value) {
  const tag = document.querySelector(selector);
  if (tag && value) {
    tag.setAttribute(attr, value);
  }
}

function renderArticlePage(posts) {
  const articleDetail = document.querySelector('[data-article-detail]');
  if (!articleDetail || !posts.length) return;

  const params = new URLSearchParams(window.location.search);
  const currentId = params.get('id');
  const currentSlug = params.get('slug') || extractSlugFromPath();
  
  function extractSlugFromPath() {
    // Parse slug from clean URL: /slug-name.html or /slug-name
    const path = window.location.pathname;
    const match = path.match(/\/([a-z0-9-]+?)(?:\.html)?$/);
    if (match && match[1] !== 'article' && match[1] !== 'index') {
      return match[1];
    }
    return null;
  }
  
  const post = posts.find((item) => 
    (currentSlug && item.slug === currentSlug) || 
    (currentId && String(item.id) === currentId)
  ) || posts[0];

  // Update URL to slug format if loaded by ID
  if (currentId && post.slug && !currentSlug) {
    window.history.replaceState(null, '', `/${post.slug}.html`);
  }

  document.title = `${post.title} | Signal Hunters`;
  updateMetaTag('meta[name="description"]', 'content', post.summary);
  updateMetaTag('meta[property="og:title"]', 'content', `${post.title} | Signal Hunters`);
  updateMetaTag('meta[property="og:description"]', 'content', post.summary);
  updateMetaTag('meta[property="og:image"]', 'content', post.image);
  updateMetaTag('meta[property="og:url"]', 'content', `${window.location.origin}/${post.slug || post.id}.html`);

  articleDetail.innerHTML = `
    <img class="article-cover" src="${post.image}" alt="${post.title}">
    <div class="article-detail-body">
      <span class="${categoryClass(post.category)}">${categoryLabel(post.category)}</span>
      <h1>${post.title}</h1>
      <div class="article-meta"><span>${formatDate(post.date)}</span><span>${categoryLabel(post.category)}</span></div>
      <div class="article-content" data-article-content>${markdownToHtml(post.content)}</div>
      <div class="ref-separator">
        <a href="https://bingx.com/vi-vn/partner/X7EZVIWI" target="_blank" rel="noopener">
          🎁 BingX — Hoàn phí <strong>45%</strong> vĩnh viễn
        </a>
      </div>
      <div class="telegram-comments">
        <h3>💬 Bình luận</h3>
        <script async src="https://telegram.org/js/telegram-widget.js?22"
          data-telegram-discussion="SignalHuntersCrypto"
          data-comments-limit="10"
          data-colorful="1"
          data-color="E74C3C"
          data-dark="1"
          data-dark-color="E74C3C">
        </script>
      </div>
      <a class="back-home-link" href="index.html">← Quay lại trang chủ</a>
    </div>
  `;
}

function renderPriceList(data) {
  const priceList = document.querySelector('[data-price-list]');
  if (!priceList) return;

  if (!data) {
    priceList.innerHTML = '<div class="price-row"><strong>Đang tải...</strong><span></span><b></b></div>';
    return;
  }

  priceList.innerHTML = coinConfig.map((coin) => {
    const coinData = data[coin.id] || {};
    const change = coinData.usd_24h_change;
    const trendClass = change >= 0 ? 'up' : 'down';
    return `
      <div class="price-row">
        <strong><span class="coin-icon">${coin.icon}</span>${coin.name}</strong>
        <span>${formatPrice(coinData.usd)}</span>
        <b class="${trendClass}">${formatChange(change)}</b>
      </div>
    `;
  }).join('');
}

function renderTicker(data) {
  const tickerGroup = document.querySelector('[data-ticker-group]');
  const tickerClone = document.querySelector('[data-ticker-clone]');
  if (!tickerGroup || !tickerClone || !data) return;

  const tickerItems = coinConfig.map((coin) => {
    const coinData = data[coin.id] || {};
    const change = coinData.usd_24h_change || 0;
    const trendClass = change >= 0 ? 'up' : 'down';
    return `<span class="ticker-item"><strong>${coin.symbol}</strong><em>${formatPrice(coinData.usd)}</em><b class="${trendClass}">${formatChange(change)}</b></span>`;
  }).join('');

  tickerGroup.innerHTML = tickerItems;
  tickerClone.innerHTML = tickerItems;
}

async function loadCryptoPrices() {
  try {
    const response = await fetch(COINGECKO_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderPriceList(data);
    renderTicker(data);
  } catch (error) {
    console.warn('Không thể tải giá crypto realtime.', error);
    renderPriceList(null);
  }
}

async function loadFearGreed() {
  const valueEl = document.getElementById('fng-value');
  const labelEl = document.getElementById('fng-label');
  const fillEl = document.getElementById('fng-fill');
  if (!valueEl || !labelEl || !fillEl) return;

  try {
    const response = await fetch(FEAR_GREED_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const fng = data?.data?.[0];
    if (!fng) throw new Error('Missing FNG payload');

    valueEl.textContent = fng.value;
    labelEl.textContent = fng.value_classification;
    fillEl.style.width = `${fng.value}%`;

    const v = Number.parseInt(fng.value, 10);
    if (v <= 25) fillEl.style.background = '#e74c3c';
    else if (v <= 50) fillEl.style.background = '#f39c12';
    else if (v <= 75) fillEl.style.background = '#2ecc71';
    else fillEl.style.background = '#27ae60';
  } catch (error) {
    console.warn('FNG error', error);
    valueEl.textContent = '--';
    labelEl.textContent = 'Chưa tải được dữ liệu';
    fillEl.style.width = '0%';
  }
}

async function loadTrendingCoins() {
  const trendingList = document.getElementById('trending-list');
  if (!trendingList) return;

  try {
    const response = await fetch(TRENDING_COINS_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const coins = (data?.coins || []).slice(0, 5);
    if (!coins.length) throw new Error('Missing trending coins payload');

    trendingList.innerHTML = coins.map(({ item }) => `
      <div class="trending-item">
        <img src="${item.small}" alt="${item.name}">
        <div class="trending-meta">
          <span class="coin-name">${item.name}</span>
          <span class="coin-symbol">${String(item.symbol || '').toUpperCase()}</span>
        </div>
        <span class="coin-rank">#${item.market_cap_rank || '--'}</span>
      </div>
    `).join('');
  } catch (error) {
    console.warn('Trending coins error', error);
    trendingList.textContent = 'Chưa tải được danh sách trending.';
  }
}

function getTradingViewTheme() {
  return document.body.classList.contains('light-mode') ? 'light' : 'dark';
}

function loadTradingViewScript() {
  if (window.TradingView) return Promise.resolve();
  if (window.__tradingViewScriptPromise) return window.__tradingViewScriptPromise;

  window.__tradingViewScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });

  return window.__tradingViewScriptPromise;
}

async function initTradingViewWidgets(forceReload = false) {
  const btcContainer = document.getElementById('tradingview_btc');
  const ethContainer = document.getElementById('tradingview_eth');
  if (!btcContainer && !ethContainer) return;

  try {
    await loadTradingViewScript();
    const theme = getTradingViewTheme();

    if (btcContainer && (forceReload || btcContainer.dataset.tvReady !== 'true')) {
      btcContainer.innerHTML = '';
      new TradingView.widget({
        autosize: true,
        symbol: 'BINANCE:BTCUSDT',
        interval: '60',
        timezone: 'Asia/Ho_Chi_Minh',
        theme,
        style: '1',
        locale: 'vi_VN',
        toolbar_bg: '#0f0f13',
        enable_publishing: false,
        hide_side_toolbar: false,
        allow_symbol_change: true,
        container_id: 'tradingview_btc',
        hide_volume: false,
        studies: ['RSI@tv-basicstudies']
      });
      btcContainer.dataset.tvReady = 'true';
    }

    if (ethContainer && (forceReload || ethContainer.dataset.tvReady !== 'true')) {
      ethContainer.innerHTML = '';
      new TradingView.widget({
        autosize: true,
        symbol: 'BINANCE:ETHUSDT',
        interval: '60',
        timezone: 'Asia/Ho_Chi_Minh',
        theme,
        style: '1',
        locale: 'vi_VN',
        toolbar_bg: '#0f0f13',
        enable_publishing: false,
        hide_side_toolbar: false,
        allow_symbol_change: true,
        container_id: 'tradingview_eth',
        hide_volume: false,
        studies: ['RSI@tv-basicstudies']
      });
      ethContainer.dataset.tvReady = 'true';
    }
  } catch (error) {
    console.warn('TradingView widget error', error);
  }
}

async function fetchRankingCoins() {
  // Try direct first
  try {
    const r = await fetch(RANKING_COINS_URL, { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch (e) {}
  // Try allorigins proxy
  try {
    const r = await fetch(`https://api.allorigins.win/raw?url=${encodeURIComponent(RANKING_COINS_URL)}`, { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch (e) {}
  // Try corsproxy.io
  try {
    const r = await fetch(`https://corsproxy.io/?${encodeURIComponent(RANKING_COINS_URL)}`, { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch (e) {}
  throw new Error('All ranking sources failed');
}

async function loadRanking() {
  const gainersContainer = document.getElementById('gainers-list');
  const losersContainer = document.getElementById('losers-list');
  if (!gainersContainer || !losersContainer) return;

  try {
    const coins = await fetchRankingCoins();
    if (!Array.isArray(coins) || !coins.length) throw new Error('Missing ranking coins payload');

    const validCoins = coins.filter((coin) => Number.isFinite(coin?.price_change_percentage_24h));
    const gainers = [...validCoins]
      .sort((a, b) => b.price_change_percentage_24h - a.price_change_percentage_24h)
      .slice(0, 5);
    const losers = [...validCoins]
      .sort((a, b) => a.price_change_percentage_24h - b.price_change_percentage_24h)
      .slice(0, 5);

    function renderList(items, container) {
      container.innerHTML = items.map((coin) => `
        <div class="ranking-item">
          <img src="${coin.image}" alt="${coin.name}" width="24" height="24">
          <span class="coin-name">${String(coin.symbol || '').toUpperCase()}</span>
          <span class="coin-price">$${Number(coin.current_price || 0).toLocaleString()}</span>
          <span class="coin-change ${coin.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}">
            ${coin.price_change_percentage_24h >= 0 ? '+' : ''}${coin.price_change_percentage_24h.toFixed(2)}%
          </span>
        </div>
      `).join('');
    }

    renderList(gainers, gainersContainer);
    renderList(losers, losersContainer);
  } catch (error) {
    console.warn('Ranking error', error);
    gainersContainer.innerHTML = '<div class="ranking-item">Chưa tải được dữ liệu.</div>';
    losersContainer.innerHTML = '<div class="ranking-item">Chưa tải được dữ liệu.</div>';
  }
}

function showRanking(type) {
  const gainersList = document.getElementById('gainers-list');
  const losersList = document.getElementById('losers-list');
  if (!gainersList || !losersList) return;

  gainersList.style.display = type === 'gainers' ? 'flex' : 'none';
  losersList.style.display = type === 'losers' ? 'flex' : 'none';

  document.querySelectorAll('.rank-tab').forEach((tab) => tab.classList.remove('active'));
  const activeButton = window.event?.target;
  if (activeButton?.classList?.contains('rank-tab')) {
    activeButton.classList.add('active');
  } else {
    const fallbackButton = document.querySelector(`.rank-tab[onclick*="${type}"]`);
    if (fallbackButton) fallbackButton.classList.add('active');
  }
}

window.showRanking = showRanking;

function searchPosts(keyword) {
  state.searchTerm = keyword || '';
  state.currentPage = 1;
  updateFilterNotice();
  renderPagedNews();
}

function changePage(direction) {
  const posts = getFilteredPosts();
  const totalPages = Math.max(1, Math.ceil(posts.length / POSTS_PER_PAGE));
  const nextPage = state.currentPage + direction;
  if (nextPage < 1 || nextPage > totalPages) return;
  state.currentPage = nextPage;
  renderPagedNews();
  const latestNews = document.getElementById('latest-news');
  if (latestNews) {
    latestNews.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

window.searchPosts = searchPosts;
window.changePage = changePage;

bindHomeNavigation();
loadPosts();
loadCryptoPrices();
loadFearGreed();
loadTrendingCoins();
loadRanking();
initTradingViewWidgets();
window.setInterval(loadCryptoPrices, 60000);
window.setInterval(loadFearGreed, 3600000);
window.setInterval(loadTrendingCoins, 3600000);
window.setInterval(loadRanking, 300000);
