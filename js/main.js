const menuToggle = document.querySelector('.menu-toggle');
const mainNav = document.querySelector('.main-nav');
const pageType = document.body.dataset.page || 'home';
const POSTS_URL = 'data/posts.json';
const COINGECKO_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,ripple&vs_currencies=usd&include_24hr_change=true';
const coinConfig = [
  { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', icon: '₿' },
  { id: 'ethereum', symbol: 'ETH', name: 'Ethereum', icon: 'Ξ' },
  { id: 'solana', symbol: 'SOL', name: 'Solana', icon: '◎' },
  { id: 'binancecoin', symbol: 'BNB', name: 'BNB', icon: '◈' },
  { id: 'ripple', symbol: 'XRP', name: 'XRP', icon: '✕' }
];

const state = {
  posts: null,
  currentFilter: 'all'
};

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

function renderHomePage(posts) {
  const heroArticle = document.querySelector('[data-hero-article]');
  const heroSideList = document.querySelector('[data-hero-side-list]');
  const newsGrid = document.querySelector('[data-news-grid]');
  const analysisList = document.querySelector('[data-analysis-list]');
  if (!heroArticle || !heroSideList || !newsGrid || !analysisList || !posts.length) return;

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

  renderNewsGrid(posts.slice(1, 7));
}

function renderNewsGrid(postsToRender) {
  const newsGrid = document.querySelector('[data-news-grid]');
  if (!newsGrid || !Array.isArray(postsToRender) || !postsToRender.length) return;

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

function applyFilter(filter) {
  if (pageType !== 'home' || !Array.isArray(state.posts)) return;
  state.currentFilter = filter;

  const filterNotice = document.querySelector('[data-filter-notice]');
  const newsSource = state.posts.slice(1, 7);
  let filteredPosts = newsSource;
  let targetId = 'latest-news';
  let noticeText = '';

  if (filter === 'analysis') {
    targetId = 'market-analysis';
    noticeText = 'Đang xem nhóm bài phân tích thị trường.';
  } else if (filter === 'news') {
    filteredPosts = newsSource.filter((post) => post.category === 'news' || post.category === 'altcoin' || post.category === 'onchain');
    noticeText = 'Đang lọc các bài tin tức và dòng tiền thị trường.';
  } else if (filter === 'commodity') {
    filteredPosts = newsSource.filter((post) => post.category === 'commodity');
    noticeText = 'Đang lọc các bài liên quan hàng hóa.';
  }

  if (filter === 'all') {
    renderNewsGrid(newsSource);
    if (filterNotice) filterNotice.hidden = true;
  } else if (filter === 'analysis') {
    if (filterNotice) {
      filterNotice.hidden = false;
      filterNotice.textContent = noticeText;
    }
  } else {
    renderNewsGrid(filteredPosts.length ? filteredPosts : newsSource);
    if (filterNotice) {
      filterNotice.hidden = false;
      filterNotice.textContent = noticeText;
    }
  }

  document.querySelectorAll('.main-nav a[data-filter]').forEach((link) => {
    link.classList.toggle('is-active', link.dataset.filter === filter);
  });

  const target = document.getElementById(targetId);
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function bindHomeNavigation() {
  if (pageType !== 'home' || !mainNav) return;
  mainNav.querySelectorAll('a[data-filter]').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      applyFilter(link.dataset.filter || 'all');
    });
  });
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
      renderHomePage(state.posts);
      applyFilter('all');
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

bindHomeNavigation();
loadPosts();
loadCryptoPrices();
window.setInterval(loadCryptoPrices, 60000);
