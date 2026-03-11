const menuToggle = document.querySelector('.menu-toggle');
const hamburger = document.querySelector('.hamburger');
const mainNav = document.querySelector('.main-nav');
const mobileNav = document.querySelector('.mobile-nav');
const pageType = document.body.dataset.page || 'home';
const POSTS_URL = 'data/posts.json';
const COINGECKO_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,ripple&vs_currencies=usd&include_24hr_change=true';
const TRENDING_COINS_URL = 'https://api.coingecko.com/api/v3/search/trending';
const FEAR_GREED_URL = 'https://api.alternative.me/fng/?limit=1';
const POSTS_PER_PAGE = 12;
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

function toggleTheme() {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
  updateThemeIcon();
}

(function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    document.body.classList.add('light-mode');
  }
  updateThemeIcon();
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
  return `article.html?id=${encodeURIComponent(post.id)}`;
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
      <p>${post.summary}</p>
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
  postsToRender.forEach((post) => {
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
  const post = posts.find((item) => String(item.id) === currentId) || posts[0];

  document.title = `${post.title} | Signal Hunters`;
  updateMetaTag('meta[name="description"]', 'content', post.summary);
  updateMetaTag('meta[property="og:title"]', 'content', `${post.title} | Signal Hunters`);
  updateMetaTag('meta[property="og:description"]', 'content', post.summary);
  updateMetaTag('meta[property="og:image"]', 'content', post.image);
  updateMetaTag('meta[property="og:url"]', 'content', `${window.location.origin}${window.location.pathname}?id=${post.id}`);

  articleDetail.innerHTML = `
    <img class="article-cover" src="${post.image}" alt="${post.title}">
    <div class="article-detail-body">
      <span class="${categoryClass(post.category)}">${categoryLabel(post.category)}</span>
      <h1>${post.title}</h1>
      <div class="article-meta"><span>${formatDate(post.date)}</span><span>${categoryLabel(post.category)}</span></div>
      <div class="article-content" data-article-content>${post.content}</div>
      <div class="article-cta-box">
        💰 Tiết kiệm phí trade? Đăng ký BingX hoàn phí 45%:
        <a href="https://bingx.com/vi-vn/partner/X7EZVIWI" target="_blank" rel="noreferrer">https://bingx.com/vi-vn/partner/X7EZVIWI</a>
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
window.setInterval(loadCryptoPrices, 60000);
window.setInterval(loadFearGreed, 3600000);
window.setInterval(loadTrendingCoins, 3600000);
