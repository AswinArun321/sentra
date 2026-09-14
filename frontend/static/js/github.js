/**
 * LicenseLens — GitHub Repositories Explorer
 * Handles async repository fetching, client-side filtering, and repository imports.
 */

(function () {
  'use strict';

  // State
  let repositories = [];
  let currentPage = 1;
  let isLoading = false;
  let hasMore = true;

  // DOM Elements
  const loadingEl = document.getElementById('repos-loading');
  const errorEl = document.getElementById('repos-error');
  const errorTitleEl = document.getElementById('repos-error-title');
  const errorMsgEl = document.getElementById('repos-error-msg');
  const gridEl = document.getElementById('repos-grid');
  const emptyEl = document.getElementById('repos-empty');
  const searchEmptyEl = document.getElementById('repos-search-empty');
  const searchInput = document.getElementById('repo-search-input');
  const privacyFilter = document.getElementById('repo-filter-privacy');
  const sortFilter = document.getElementById('repo-filter-sort');
  const refreshBtn = document.getElementById('refresh-repos-btn');
  const retryBtn = document.getElementById('repos-retry-btn');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const loadMoreWrap = document.getElementById('repos-load-more');
  const loadMoreBtn = document.getElementById('load-more-btn');

  // Helper: Get CSRF Token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Language Colors
  const LANG_COLORS = {
    'Python': '#3572A5',
    'JavaScript': '#f1e05a',
    'TypeScript': '#3178c6',
    'HTML': '#e34c26',
    'CSS': '#563d7c',
    'Java': '#b07219',
    'Go': '#00ADD8',
    'Rust': '#dea584',
    'C++': '#f34b7d',
    'C#': '#178600',
    'PHP': '#4F5D95',
    'Ruby': '#701516',
    'Shell': '#89e051',
  };

  function getLangColor(lang) {
    return LANG_COLORS[lang] || '#8f9cae';
  }

  // Format Date
  function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
      return dateStr;
    }
  }

  // Fetch Repositories from LicenseLens API
  async function fetchRepositories(page = 1, append = false) {
    if (isLoading) return;
    isLoading = true;

    if (!append) {
      loadingEl.style.display = 'block';
      gridEl.style.display = 'none';
      emptyEl.style.display = 'none';
      searchEmptyEl.style.display = 'none';
      errorEl.style.display = 'none';
      loadMoreWrap.style.display = 'none';
    } else if (loadMoreBtn) {
      loadMoreBtn.innerHTML = '<span class="spinner"></span> Loading...';
      loadMoreBtn.disabled = true;
    }

    try {
      const response = await fetch(`/api/github/repositories/?page=${page}&per_page=30`, {
        headers: {
          'Accept': 'application/json',
        }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Error ${response.status}: Failed to load repositories`);
      }

      const results = data.results || [];
      if (append) {
        // Prevent duplicate repository entries
        const existingIds = new Set(repositories.map(r => r.id));
        for (const r of results) {
          if (!existingIds.has(r.id)) {
            repositories.push(r);
          }
        }
      } else {
        repositories = results;
      }

      hasMore = results.length === 30;
      currentPage = page;

      renderRepositories();
    } catch (err) {
      console.error('Error fetching repositories:', err);
      loadingEl.style.display = 'none';
      errorEl.style.display = 'block';
      errorTitleEl.textContent = 'Unable to Load Repositories';
      errorMsgEl.textContent = err.message || 'An error occurred while communicating with GitHub.';
    } finally {
      isLoading = false;
      if (loadMoreBtn) {
        loadMoreBtn.innerHTML = 'Load More Repositories ↓';
        loadMoreBtn.disabled = false;
      }
    }
  }

  // Render & Filter Repositories
  function renderRepositories() {
    loadingEl.style.display = 'none';

    if (repositories.length === 0) {
      gridEl.style.display = 'none';
      emptyEl.style.display = 'block';
      searchEmptyEl.style.display = 'none';
      loadMoreWrap.style.display = 'none';
      return;
    }

    emptyEl.style.display = 'none';

    // Apply Client-Side Filters
    const query = (searchInput ? searchInput.value : '').trim().toLowerCase();
    const privacy = privacyFilter ? privacyFilter.value : 'all';
    const sort = sortFilter ? sortFilter.value : 'updated';

    let filtered = repositories.filter(repo => {
      // Privacy filter
      if (privacy === 'public' && repo.private) return false;
      if (privacy === 'private' && !repo.private) return false;

      // Search query
      if (query) {
        const matchesName = (repo.name || '').toLowerCase().includes(query);
        const matchesFull = (repo.full_name || '').toLowerCase().includes(query);
        const matchesDesc = (repo.description || '').toLowerCase().includes(query);
        const matchesLang = (repo.language || '').toLowerCase().includes(query);
        if (!matchesName && !matchesFull && !matchesDesc && !matchesLang) {
          return false;
        }
      }
      return true;
    });

    // Sort
    filtered.sort((a, b) => {
      if (sort === 'name') {
        return (a.name || '').localeCompare(b.name || '');
      } else if (sort === 'stars') {
        return (b.stargazers_count || 0) - (a.stargazers_count || 0);
      } else {
        // default updated
        return new Date(b.updated_at || 0) - new Date(a.updated_at || 0);
      }
    });

    if (filtered.length === 0) {
      gridEl.style.display = 'none';
      searchEmptyEl.style.display = 'block';
      loadMoreWrap.style.display = 'none';
      return;
    }

    searchEmptyEl.style.display = 'none';
    gridEl.style.display = 'grid';
    gridEl.innerHTML = '';

    filtered.forEach(repo => {
      gridEl.appendChild(createRepoCard(repo));
    });

    if (hasMore && !query) {
      loadMoreWrap.style.display = 'block';
    } else {
      loadMoreWrap.style.display = 'none';
    }
  }

  // Create Repository Card DOM Element
  function createRepoCard(repo) {
    const card = document.createElement('div');
    card.className = 'repo-card';
    card.id = `repo-card-${repo.id}`;

    const isPrivate = repo.private;
    const privacyBadge = isPrivate
      ? '<span class="badge" style="background:#fee2e2; color:#b91c1c;">Private</span>'
      : '<span class="badge badge-low">Public</span>';

    const langColor = getLangColor(repo.language);
    const dateFormatted = formatDate(repo.updated_at);

    // Initial Button State
    let actionBtnHtml = '';
    if (repo.already_imported) {
      actionBtnHtml = `
        <span class="badge badge-info" style="padding: 6px 12px; font-size: 12px; display: inline-flex; align-items: center; gap: 4px;">
          ✓ Imported
        </span>
        <a href="/projects/" class="btn btn-secondary btn-sm" id="btn-view-${repo.id}">
          View Projects →
        </a>
      `;
    } else {
      actionBtnHtml = `
        <button class="btn btn-primary btn-sm import-btn" data-repo-id="${repo.id}" data-repo-name="${escapeHtml(repo.name)}" id="btn-import-${repo.id}">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Import Project
        </button>
      `;
    }

    card.innerHTML = `
      <div class="repo-card-header">
        <div>
          <div class="repo-card-title">${escapeHtml(repo.name)}</div>
          <div class="repo-card-fullname">${escapeHtml(repo.full_name)}</div>
        </div>
        <div>${privacyBadge}</div>
      </div>

      <div class="repo-card-desc">
        ${escapeHtml(repo.description || 'No description provided.')}
      </div>

      <div class="flex gap-8 mb-16" style="margin-top:auto; flex-wrap:wrap;" id="action-wrap-${repo.id}">
        ${actionBtnHtml}
        <a href="/github/repositories/${repo.id}/documentation/" class="btn btn-secondary btn-sm" title="Analyze README documentation and recommendations">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          README
        </a>
        <a href="${escapeHtml(repo.html_url)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" title="Open repository in GitHub">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
          GitHub
        </a>
      </div>

      <div class="repo-card-meta">
        <span style="display:inline-flex; align-items:center; gap:6px;">
          <span class="lang-dot" style="background:${langColor};"></span>
          ${escapeHtml(repo.language || 'Plain')}
        </span>

        ${repo.stargazers_count > 0 ? `
          <span style="display:inline-flex; align-items:center; gap:4px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            ${repo.stargazers_count}
          </span>
        ` : ''}

        <span style="margin-left:auto;">
          Updated ${dateFormatted}
        </span>
      </div>
    `;

    // Attach Import Handler
    const importBtn = card.querySelector('.import-btn');
    if (importBtn) {
      importBtn.addEventListener('click', () => handleImport(repo));
    }

    return card;
  }

  // Handle Import Action
  async function handleImport(repo) {
    const actionWrap = document.getElementById(`action-wrap-${repo.id}`);
    const importBtn = document.getElementById(`btn-import-${repo.id}`);
    if (!importBtn) return;

    const originalText = importBtn.innerHTML;
    importBtn.disabled = true;
    importBtn.innerHTML = '<span style="display:inline-block; width:12px; height:12px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; vertical-align:middle; margin-right:4px;"></span> Importing...';

    const csrfToken = getCookie('csrftoken');

    try {
      const response = await fetch('/api/github/import/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          repository_id: repo.id,
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to import repository.');
      }

      // Mark as imported in local state
      repo.already_imported = true;

      // Update UI
      actionWrap.innerHTML = `
        <span class="badge badge-low" style="padding: 6px 12px; font-size: 12px; display: inline-flex; align-items: center; gap: 4px;">
          ✓ Imported
        </span>
        <a href="${data.project_url || `/projects/${data.project_id}/`}" class="btn btn-primary btn-sm">
          Open Project →
        </a>
        <a href="${escapeHtml(repo.html_url)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm">
          GitHub
        </a>
      `;

      // Show temporary inline notification
      const toast = document.createElement('div');
      toast.style.cssText = 'position:fixed; bottom:24px; right:24px; background:#10b981; color:#fff; padding:12px 20px; border-radius:8px; font-weight:600; font-size:13px; box-shadow:0 6px 20px rgba(0,0,0,0.15); z-index:9999; display:flex; align-items:center; gap:8px;';
      toast.innerHTML = `✓ Imported <strong>${escapeHtml(repo.name)}</strong>! Automatic analysis started...`;
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.style.transition = 'opacity 0.4s';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
      }, 3500);

    } catch (err) {
      console.error('Import failed:', err);
      alert(err.message || 'Unable to import repository. Please try again.');
      importBtn.disabled = false;
      importBtn.innerHTML = originalText;
    }
  }

  // Escape HTML utility
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Event Listeners
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(renderRepositories, 200);
    });
  }

  if (privacyFilter) {
    privacyFilter.addEventListener('change', renderRepositories);
  }

  if (sortFilter) {
    sortFilter.addEventListener('change', renderRepositories);
  }

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => fetchRepositories(1, false));
  }

  if (retryBtn) {
    retryBtn.addEventListener('click', () => fetchRepositories(1, false));
  }

  if (clearSearchBtn && searchInput) {
    clearSearchBtn.addEventListener('click', () => {
      searchInput.value = '';
      renderRepositories();
    });
  }

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', () => {
      fetchRepositories(currentPage + 1, true);
    });
  }

  // Initial Load
  fetchRepositories(1, false);

})();
