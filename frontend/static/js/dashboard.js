/**
 * LicenseLens — Security & Compliance Dashboard Controller
 * Asynchronously loads and renders dynamic metrics, charts, attention items,
 * recent scans, and GitHub health.
 */

document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
});

let dashboardData = null;

async function loadDashboard() {
  const refreshBtn = document.getElementById('dashRefreshBtn');
  if (refreshBtn) {
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '⟳ Refreshing...';
  }

  try {
    const response = await fetch('/api/dashboard/overview/', {
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    dashboardData = await response.json();
    renderDashboard(dashboardData);
  } catch (error) {
    console.error('Failed to load dashboard metrics:', error);
    showDashboardError(error.message);
  } finally {
    if (refreshBtn) {
      refreshBtn.disabled = false;
      refreshBtn.innerHTML = '⟳ Refresh';
    }
  }
}

function renderDashboard(data) {
  renderSummary(data.summary);
  renderSecurityOverview(data.vulnerabilities, data.project_health);
  renderAttentionItems(data.attention_required);
  renderRecentScans(data.recent_scans);
  renderGitHubHealth(data.github, data.repository_health);
}

function renderSummary(summary) {
  if (!summary) return;

  // 1. Projects
  const elProjCount = document.getElementById('kpiProjCount');
  const elProjSub = document.getElementById('kpiProjSubtext');
  if (elProjCount) elProjCount.innerText = summary.projects;
  if (elProjSub) {
    elProjSub.innerText = summary.scanned_today > 0 
      ? `${summary.scanned_today} scanned today`
      : 'All monitored repos';
  }

  // 2. Vulnerabilities
  const elVulnCount = document.getElementById('kpiVulnCount');
  const elVulnSub = document.getElementById('kpiVulnSubtext');
  if (elVulnCount) elVulnCount.innerText = summary.vulnerabilities;
  if (elVulnSub) {
    if (summary.vulnerabilities === 0) {
      elVulnSub.innerHTML = '<span class="kpi-badge good">✓ Clean</span>';
    } else {
      elVulnSub.innerHTML = `
        <span class="kpi-badge critical">${summary.critical_vulnerabilities} Critical</span>
        <span class="kpi-badge high">${summary.high_vulnerabilities} High</span>
      `;
    }
  }

  // 3. License Risks
  const elLicCount = document.getElementById('kpiLicCount');
  const elLicSub = document.getElementById('kpiLicSubtext');
  if (elLicCount) elLicCount.innerText = summary.license_risks;
  if (elLicSub) {
    if (summary.license_risks === 0) {
      elLicSub.innerHTML = '<span class="kpi-badge good">✓ Compliant</span>';
    } else {
      elLicSub.innerHTML = '<span class="kpi-badge high">Need Attention</span>';
    }
  }

  // 4. Security Score
  const elScoreVal = document.getElementById('kpiScoreVal');
  const elScoreBadge = document.getElementById('kpiScoreBadge');
  if (elScoreVal) elScoreVal.innerText = summary.security_score;
  if (elScoreBadge) {
    elScoreBadge.innerText = summary.rating_label || 'Good';
    elScoreBadge.className = `kpi-badge ${(summary.rating_label || 'good').toLowerCase().replace(' ', '-')}`;
  }
}

function renderSecurityOverview(vulns, health) {
  if (vulns) {
    const total = Math.max(1, vulns.total || (vulns.critical + vulns.high + vulns.medium + vulns.low));
    
    // Critical
    setDistBar('distCritBar', 'distCritCount', vulns.critical, total);
    // High
    setDistBar('distHighBar', 'distHighCount', vulns.high, total);
    // Medium
    setDistBar('distMedBar', 'distMedCount', vulns.medium, total);
    // Low
    setDistBar('distLowBar', 'distLowCount', vulns.low, total);
  }

  if (health) {
    const totalProjects = Math.max(1, health.total || (health.excellent + health.good + health.needs_attention + health.critical));
    
    // Excellent
    setDistBar('distExcelBar', 'distExcelCount', health.excellent, totalProjects);
    // Good
    setDistBar('distGoodBar', 'distGoodCount', health.good, totalProjects);
    // Needs Attention
    setDistBar('distAttnBar', 'distAttnCount', health.needs_attention, totalProjects);
    // Critical
    setDistBar('distCritProjBar', 'distCritProjCount', health.critical, totalProjects);
  }
}

function setDistBar(barId, countId, value, total) {
  const barEl = document.getElementById(barId);
  const countEl = document.getElementById(countId);
  if (countEl) countEl.innerText = value;
  if (barEl) {
    const pct = total > 0 ? Math.round((value / total) * 100) : 0;
    barEl.style.width = `${Math.min(100, pct)}%`;
  }
}

function renderAttentionItems(items) {
  const container = document.getElementById('attentionList');
  const badgeEl = document.getElementById('attentionCountBadge');
  if (!container) return;

  if (!items || items.length === 0) {
    if (badgeEl) badgeEl.style.display = 'none';
    container.innerHTML = `
      <div class="dash-empty-positive" style="grid-column: 1 / -1;">
        <div class="dash-empty-icon">🛡️</div>
        <div class="dash-empty-title">Everything looks good</div>
        <div class="dash-empty-desc">No projects currently require immediate security or license attention.</div>
      </div>
    `;
    return;
  }

  if (badgeEl) {
    badgeEl.style.display = 'inline-flex';
    badgeEl.innerText = `${items.length} Issue${items.length === 1 ? '' : 's'}`;
  }

  // Display top 3-5 items
  const displayItems = items.slice(0, 4);
  container.innerHTML = displayItems.map(item => {
    const sevClass = item.severity.toLowerCase();
    const reasonsHtml = item.reasons.map(r => `
      <div class="attention-reason-pill">
        <span>•</span> ${escapeHtml(r)}
      </div>
    `).join('');

    return `
      <div class="attention-item ${sevClass}">
        <div>
          <div class="attention-item-top">
            <div class="attention-project-name">
              <span>${sevClass === 'critical' ? '🔴' : sevClass === 'high' ? '🟠' : '🟡'}</span>
              ${escapeHtml(item.project_name)}
            </div>
            <span class="kpi-badge ${sevClass}">${item.severity}</span>
          </div>
          <div class="attention-reasons">
            ${reasonsHtml}
          </div>
        </div>
        <div class="attention-item-footer">
          <a href="/projects/${item.project_id}/" class="btn btn-secondary btn-sm" style="font-size: 11.5px; padding: 4px 10px;">
            View Project →
          </a>
        </div>
      </div>
    `;
  }).join('');
}

function renderRecentScans(scans) {
  const tbody = document.getElementById('recentScansTbody');
  if (!tbody) return;

  if (!scans || scans.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 28px; color: #64748b;">
          No scans run yet. Run an audit on a project or import a GitHub repository.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = scans.map(s => {
    const statusClass = (s.status_raw || '').toLowerCase();
    const riskClass = (s.risk_level || '').toLowerCase();

    return `
      <tr>
        <td>
          <a href="/projects/${s.project_id}/" class="project-link">
            ${escapeHtml(s.project_name)}
          </a>
        </td>
        <td><strong>${s.dependency_count}</strong> pkgs</td>
        <td>
          <span style="font-weight: 700; color: ${s.vulnerability_count > 0 ? '#ef4444' : '#10b981'};">
            ${s.vulnerability_count}
          </span>
        </td>
        <td>
          <span class="risk-pill ${riskClass}">${s.risk_level}</span>
        </td>
        <td>
          <span class="status-pill ${statusClass}">${s.status}</span>
        </td>
        <td style="color: #64748b; font-size: 12px;">${s.date}</td>
      </tr>
    `;
  }).join('');
}

function renderGitHubHealth(github, repoHealth) {
  const statusEl = document.getElementById('ghStatusIndicator');
  const userEl = document.getElementById('ghUsername');
  const countEl = document.getElementById('ghRepoCount');
  const actionBtn = document.getElementById('ghActionBtn');
  const healthGrid = document.getElementById('repoHealthGrid');

  if (!github || !github.connected) {
    if (statusEl) {
      statusEl.className = 'gh-status-badge disconnected';
      statusEl.innerText = '● Disconnected';
    }
    if (userEl) userEl.innerText = 'Account not connected';
    if (countEl) countEl.innerText = 'Connect GitHub to import & audit';
    if (actionBtn) {
      actionBtn.href = '/github/connect/';
      actionBtn.innerText = 'Connect GitHub';
      actionBtn.className = 'btn btn-primary btn-sm';
    }
    if (healthGrid) healthGrid.style.display = 'none';
    return;
  }

  // Connected state
  if (statusEl) {
    statusEl.className = 'gh-status-badge connected';
    statusEl.innerText = '✓ Connected';
  }
  if (userEl) userEl.innerText = `@${github.username}`;
  if (countEl) countEl.innerText = `${github.repository_count} repositories accessible`;
  if (actionBtn) {
    actionBtn.href = '/github/repositories/';
    actionBtn.innerText = 'View GitHub Repos →';
    actionBtn.className = 'btn btn-secondary btn-sm';
  }
  if (healthGrid) healthGrid.style.display = 'grid';

  // Render repository documentation & license health counters
  if (repoHealth) {
    const readmePresEl = document.getElementById('repoReadmePresent');
    const readmeMissEl = document.getElementById('repoReadmeMissing');
    const licPresEl = document.getElementById('repoLicensePresent');
    const licMissEl = document.getElementById('repoLicenseMissing');

    if (readmePresEl) readmePresEl.innerText = repoHealth.readme_present;
    if (readmeMissEl) readmeMissEl.innerText = repoHealth.readme_missing;
    if (licPresEl) licPresEl.innerText = repoHealth.license_present;
    if (licMissEl) licMissEl.innerText = repoHealth.license_missing;
  }
}

function showDashboardError(msg) {
  const banner = document.getElementById('dashErrorBanner');
  if (banner) {
    banner.style.display = 'flex';
    document.getElementById('dashErrorMsg').innerText = `Unable to load dashboard data: ${msg}`;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}
