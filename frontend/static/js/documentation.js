/**
 * LicenseLens — README Documentation Analyzer & Recommendation Client
 */

(function () {
  'use strict';

  // DOM Elements
  const container = document.getElementById('doc-container');
  if (!container) return;

  const repoId = container.dataset.repoId;
  const repoName = container.dataset.repoName;
  const repoFull = container.dataset.repoFull;

  const loadingEl = document.getElementById('doc-loading');
  const errorEl = document.getElementById('doc-error');
  const errorMsgEl = document.getElementById('doc-error-msg');
  const retryBtn = document.getElementById('doc-retry-btn');
  const contentEl = document.getElementById('doc-content');

  const scoreNumEl = document.getElementById('score-num');
  const ratingBadgeEl = document.getElementById('rating-badge');
  const statusBadgeEl = document.getElementById('readme-status-badge');
  const statusDescEl = document.getElementById('readme-status-desc');
  const sectionsListEl = document.getElementById('sections-checklist');
  const recsListEl = document.getElementById('recommendations-list');

  const editorTextarea = document.getElementById('readme-editor');
  const editorView = document.getElementById('editor-view');
  const previewView = document.getElementById('preview-view');
  const tabEditBtn = document.getElementById('tab-btn-edit');
  const tabPreviewBtn = document.getElementById('tab-btn-preview');
  const charCountEl = document.getElementById('char-count');

  const generateBtn = document.getElementById('btn-generate-readme');
  const loadExistingBtn = document.getElementById('btn-load-existing-readme');
  const openCommitModalBtn = document.getElementById('btn-open-commit-modal');

  const modalBackdrop = document.getElementById('commit-modal-backdrop');
  const modalCommitMsgInput = document.getElementById('modal-commit-msg');
  const modalOverwriteWrap = document.getElementById('modal-overwrite-warning');
  const modalOverwriteCheckbox = document.getElementById('modal-overwrite-checkbox');
  const modalCancelBtn = document.getElementById('btn-cancel-commit');
  const modalConfirmBtn = document.getElementById('btn-confirm-commit');

  const successBanner = document.getElementById('commit-success-banner');
  const successText = document.getElementById('commit-success-text');
  const successLink = document.getElementById('commit-success-link');

  // State
  let analysisData = null;
  let existingReadmeContent = '';
  let generatedReadmeContent = '';

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

  // Fetch Documentation Audit
  async function loadDocumentationAnalysis() {
    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    contentEl.style.display = 'none';

    try {
      const response = await fetch(`/api/github/repositories/${repoId}/documentation/`, {
        headers: { 'Accept': 'application/json' }
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to analyze repository documentation.');
      }

      analysisData = data;
      renderAnalysis(data);

      loadingEl.style.display = 'none';
      contentEl.style.display = 'block';
    } catch (err) {
      console.error('Error loading documentation analysis:', err);
      loadingEl.style.display = 'none';
      errorEl.style.display = 'block';
      errorMsgEl.textContent = err.message || 'An error occurred while connecting to GitHub.';
    }
  }

  // Render Analysis Data to UI
  function renderAnalysis(data) {
    const score = data.score || 0;
    scoreNumEl.textContent = score;

    // Rating Badge Style
    ratingBadgeEl.textContent = data.rating || 'Unknown';
    ratingBadgeEl.className = 'badge';
    if (score >= 90) {
      ratingBadgeEl.classList.add('badge-low');
    } else if (score >= 75) {
      ratingBadgeEl.classList.add('badge-info');
    } else if (score >= 50) {
      ratingBadgeEl.classList.add('badge-medium');
    } else {
      ratingBadgeEl.classList.add('badge-critical');
    }

    // README Status
    if (data.exists) {
      statusBadgeEl.className = 'badge badge-low';
      statusBadgeEl.textContent = `✓ ${data.filename || 'README.md'} Present`;
      statusDescEl.innerHTML = `Found <strong>${escapeHtml(data.filename || 'README.md')}</strong> in repository root. Evaluated content across 10 standard criteria.`;
      if (data.content) {
        existingReadmeContent = data.content;
        editorTextarea.value = existingReadmeContent;
        updateCharCount();
        loadExistingBtn.style.display = 'inline-flex';
      }
    } else {
      statusBadgeEl.className = 'badge badge-high';
      statusBadgeEl.textContent = '⚠ README Missing';
      statusDescEl.innerHTML = `No standard README file found in the root of <strong>${escapeHtml(repoFull)}</strong>. We strongly recommend generating one to document this project.`;
      loadExistingBtn.style.display = 'none';

      // Auto trigger generation if missing
      if (!editorTextarea.value.trim()) {
        generateReadme();
      }
    }

    // Render Checklist of Sections
    sectionsListEl.innerHTML = '';
    const details = data.sections_detail || [];
    details.forEach(sec => {
      const item = document.createElement('div');
      item.className = `section-check-item ${sec.present ? 'present' : 'missing'}`;
      item.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
          ${sec.present ?
            '<span style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; background: #10b981; color: #fff; border-radius: 50%; font-size: 11px;">✓</span>' :
            '<span style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; background: #e2e8f0; color: #64748b; border-radius: 50%; font-size: 11px;">✗</span>'
          }
          <strong style="color: ${sec.present ? '#166534' : 'var(--text-title)'};">${escapeHtml(sec.name)}</strong>
        </div>
        <span class="badge ${sec.present ? 'badge-low' : 'badge-secondary'}" style="font-size: 11px;">
          ${sec.present ? `+${sec.points} pts` : `0 / ${sec.points} pts`}
        </span>
      `;
      sectionsListEl.appendChild(item);
    });

    // Render Recommendations
    recsListEl.innerHTML = '';
    const recs = data.recommendations || [];
    if (recs.length === 0) {
      recsListEl.innerHTML = `
        <li class="rec-bullet-item" style="background: #f0fdf4; border-color: #bbf7d0; color: #166534;">
          <span>Outstanding documentation! All standard sections and best practices are present.</span>
        </li>
      `;
    } else {
      recs.forEach(rec => {
        const li = document.createElement('li');
        li.className = 'rec-bullet-item';
        li.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" style="flex-shrink: 0; margin-top: 2px;">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>${escapeHtml(rec)}</span>
        `;
        recsListEl.appendChild(li);
      });
    }
  }

  // Generate Suggested README
  async function generateReadme() {
    const originalText = generateBtn.innerHTML;
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner"></span> Synthesizing README...';

    try {
      const response = await fetch(`/api/github/repositories/${repoId}/readme/generate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        }
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate README.');
      }

      generatedReadmeContent = data.content || '';
      editorTextarea.value = generatedReadmeContent;
      updateCharCount();

      // Switch to edit view if in preview
      switchToEditTab();

    } catch (err) {
      console.error('README generation error:', err);
      alert(err.message || 'Unable to generate README.');
    } finally {
      generateBtn.disabled = false;
      generateBtn.innerHTML = originalText;
    }
  }

  // Load Existing README
  function loadExisting() {
    if (existingReadmeContent) {
      editorTextarea.value = existingReadmeContent;
      updateCharCount();
      switchToEditTab();
    }
  }

  // Character Counter
  function updateCharCount() {
    const len = (editorTextarea ? editorTextarea.value.length : 0);
    if (charCountEl) {
      charCountEl.textContent = `${len.toLocaleString()} characters`;
    }
  }

  // Tab Switching (Editor vs Preview)
  function switchToEditTab() {
    tabEditBtn.style.background = 'var(--bg-base)';
    tabEditBtn.style.fontWeight = '700';
    tabPreviewBtn.style.background = '#fff';
    tabPreviewBtn.style.fontWeight = '500';

    editorView.style.display = 'block';
    previewView.style.display = 'none';
  }

  function switchToPreviewTab() {
    tabPreviewBtn.style.background = 'var(--bg-base)';
    tabPreviewBtn.style.fontWeight = '700';
    tabEditBtn.style.background = '#fff';
    tabEditBtn.style.fontWeight = '500';

    editorView.style.display = 'none';
    previewView.style.display = 'block';

    const rawMarkdown = editorTextarea.value;
    previewView.innerHTML = renderSimpleMarkdown(rawMarkdown);
  }

  // Lightweight Markdown to HTML Renderer
  function renderSimpleMarkdown(md) {
    if (!md) return '<em style="color: var(--text-muted);">No content to preview</em>';

    let html = escapeHtml(md);

    // Fenced Code blocks
    html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 12px; margin: 12px 0;"><code>$2</code></pre>');

    // Inline Code
    html = html.replace(/`([^`]+)`/g, '<code style="background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #0f172a;">$1</code>');

    // Headers
    html = html.replace(/^# (.*?)$/gm, '<h1 style="font-size: 24px; font-weight: 800; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin: 16px 0 12px;">$1</h1>');
    html = html.replace(/^## (.*?)$/gm, '<h2 style="font-size: 18px; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin: 18px 0 10px;">$1</h2>');
    html = html.replace(/^### (.*?)$/gm, '<h3 style="font-size: 15px; font-weight: 700; margin: 14px 0 8px;">$1</h3>');

    // Bold & Italics
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Horizontal Rules
    html = html.replace(/^---$/gm, '<hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 16px 0;">');

    // Lists
    html = html.replace(/^\- (.*?)$/gm, '<li style="margin-left: 20px; margin-bottom: 4px;">$1</li>');

    // Paragraphs / Newlines
    html = html.replace(/\n\n+/g, '<br><br>');

    return html;
  }

  // Open Commit Modal
  function openCommitModal() {
    const content = editorTextarea.value.trim();
    if (!content) {
      alert('Please enter or generate README content before committing.');
      return;
    }

    const exists = analysisData && analysisData.exists;
    const filename = (analysisData && analysisData.filename) || 'README.md';

    document.getElementById('modal-filename-target').textContent = filename;

    if (exists) {
      modalOverwriteWrap.style.display = 'block';
      modalOverwriteCheckbox.checked = false;
      modalCommitMsgInput.value = `Update ${filename} via LicenseLens`;
    } else {
      modalOverwriteWrap.style.display = 'none';
      modalOverwriteCheckbox.checked = false;
      modalCommitMsgInput.value = 'Add README.md via LicenseLens';
    }

    modalBackdrop.style.display = 'flex';
  }

  function closeCommitModal() {
    modalBackdrop.style.display = 'none';
  }

  // Commit README to GitHub
  async function commitReadme() {
    const content = editorTextarea.value.trim();
    const commitMessage = modalCommitMsgInput.value.trim() || 'Add README.md via LicenseLens';
    const exists = analysisData && analysisData.exists;
    const overwrite = modalOverwriteCheckbox ? modalOverwriteCheckbox.checked : false;

    if (exists && !overwrite) {
      alert('This repository already has a README file. Please check the confirmation box to authorize overwriting it.');
      return;
    }

    const originalText = modalConfirmBtn.innerHTML;
    modalConfirmBtn.disabled = true;
    modalConfirmBtn.innerHTML = '<span class="spinner"></span> Committing to GitHub...';

    try {
      const response = await fetch(`/api/github/repositories/${repoId}/readme/commit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
          content: content,
          commit_message: commitMessage,
          overwrite: overwrite,
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to commit README to GitHub.');
      }

      closeCommitModal();

      // Show Success Banner
      successBanner.style.display = 'flex';
      successText.textContent = data.message || 'README.md committed successfully to repository!';
      if (data.html_url) {
        successLink.href = data.html_url;
        successLink.style.display = 'inline-flex';
      } else {
        successLink.style.display = 'none';
      }

      // Reload analysis to reflect new score
      await loadDocumentationAnalysis();

    } catch (err) {
      console.error('Commit failed:', err);
      alert(err.message || 'Unable to commit README to GitHub.');
    } finally {
      modalConfirmBtn.disabled = false;
      modalConfirmBtn.innerHTML = originalText;
    }
  }

  // Escape HTML
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
  if (retryBtn) retryBtn.addEventListener('click', loadDocumentationAnalysis);
  if (generateBtn) generateBtn.addEventListener('click', generateReadme);
  if (loadExistingBtn) loadExistingBtn.addEventListener('click', loadExisting);
  if (editorTextarea) editorTextarea.addEventListener('input', updateCharCount);

  if (tabEditBtn) tabEditBtn.addEventListener('click', switchToEditTab);
  if (tabPreviewBtn) tabPreviewBtn.addEventListener('click', switchToPreviewTab);

  if (openCommitModalBtn) openCommitModalBtn.addEventListener('click', openCommitModal);
  if (modalCancelBtn) modalCancelBtn.addEventListener('click', closeCommitModal);
  if (modalConfirmBtn) modalConfirmBtn.addEventListener('click', commitReadme);

  // Close modal when clicking backdrop
  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) closeCommitModal();
    });
  }

  // Initial Load
  loadDocumentationAnalysis();

})();
