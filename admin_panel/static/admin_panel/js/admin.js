/**
 * SENTRA Admin Console — Frontend JS Engine
 */

// CSRF Cookie Helper
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

const csrftoken = getCookie('csrftoken');

// Generic Confirmation Modal Handler
let activeActionCallback = null;

function openConfirmModal(title, message, confirmBtnText, isDanger, onConfirm) {
  const modal = document.getElementById('adminModal');
  if (!modal) return;

  document.getElementById('adminModalTitle').innerText = title;
  document.getElementById('adminModalBody').innerHTML = message;
  const confirmBtn = document.getElementById('adminModalConfirmBtn');
  confirmBtn.innerText = confirmBtnText || 'Confirm';

  if (isDanger) {
    confirmBtn.className = 'admin-btn admin-btn-danger';
  } else {
    confirmBtn.className = 'admin-btn admin-btn-primary';
  }

  activeActionCallback = onConfirm;
  modal.classList.add('active');
}

function closeConfirmModal() {
  const modal = document.getElementById('adminModal');
  if (modal) modal.classList.remove('active');
  activeActionCallback = null;
}

document.addEventListener('DOMContentLoaded', () => {
  const confirmBtn = document.getElementById('adminModalConfirmBtn');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
      if (typeof activeActionCallback === 'function') {
        activeActionCallback();
      }
      closeConfirmModal();
    });
  }

  const cancelBtn = document.getElementById('adminModalCancelBtn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', closeConfirmModal);
  }

  // Close on backdrop click
  const modalOverlay = document.getElementById('adminModal');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) closeConfirmModal();
    });
  }

  // Keyboard shortcut Ctrl+K to focus search
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const searchInput = document.getElementById('adminQuickSearch');
      if (searchInput) searchInput.focus();
    }
  });
});

// User Actions via REST API
function performUserAction(userId, action, reason = '') {
  let url = `/api/admin/users/${userId}/${action}/`;
  let body = {};
  if (action === 'suspend') {
    body.reason = reason;
  }

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken,
    },
    body: JSON.stringify(body)
  })
  .then(res => {
    if (!res.ok) {
      return res.json().then(data => { throw new Error(data.error || 'Action failed.'); });
    }
    return res.json();
  })
  .then(data => {
    window.location.reload();
  })
  .catch(err => {
    alert('Operation failed: ' + err.message);
  });
}

function confirmUserSuspend(userId, username) {
  openConfirmModal(
    `Suspend User @${username}?`,
    `<p>Suspending <strong>${username}</strong> will immediately disable platform access and invalidate active sessions.</p>
     <div style="margin-top: 12px;">
       <label style="display:block; font-size:12px; margin-bottom:4px; font-weight:600;">Suspension Reason (optional):</label>
       <input type="text" id="suspendReasonInput" class="admin-input" style="width:100%;" placeholder="e.g. Policy violation or suspicious activity" />
     </div>`,
    'Suspend Account',
    true,
    () => {
      const reason = document.getElementById('suspendReasonInput')?.value || '';
      performUserAction(userId, 'suspend', reason);
    }
  );
}

function confirmUserDeactivate(userId, username) {
  openConfirmModal(
    `Deactivate User @${username}?`,
    `<p>Deactivating <strong>${username}</strong> will prevent them from logging in.</p>`,
    'Deactivate',
    true,
    () => performUserAction(userId, 'deactivate')
  );
}

function confirmUserActivate(userId, username) {
  openConfirmModal(
    `Activate User @${username}?`,
    `<p>Activate access for <strong>${username}</strong>.</p>`,
    'Activate',
    false,
    () => performUserAction(userId, 'activate')
  );
}

function confirmUserReactivate(userId, username) {
  openConfirmModal(
    `Reactivate User @${username}?`,
    `<p>Reactivate <strong>${username}</strong> and restore standard platform privileges.</p>`,
    'Reactivate',
    false,
    () => performUserAction(userId, 'reactivate')
  );
}

function toggleStaffPrivilege(userId, username, currentIsStaff) {
  const newStaff = !currentIsStaff;
  openConfirmModal(
    `${newStaff ? 'Grant' : 'Revoke'} Admin Privilege?`,
    `<p>Are you sure you want to ${newStaff ? 'grant administrative staff privileges to' : 'revoke administrative staff privileges from'} <strong>${username}</strong>?</p>`,
    newStaff ? 'Grant Admin' : 'Revoke Admin',
    !newStaff,
    () => {
      fetch(`/api/admin/users/${userId}/toggle-staff/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ is_staff: newStaff })
      })
      .then(res => {
        if (!res.ok) return res.json().then(data => { throw new Error(data.error || 'Failed.'); });
        return res.json();
      })
      .then(data => window.location.reload())
      .catch(err => alert('Privilege change failed: ' + err.message));
    }
  );
}
