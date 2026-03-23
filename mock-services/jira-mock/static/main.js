/* ============================================================
   Jira Mock – main.js
   Handles: create modal, issue-type field toggling, keyboard traps
   ============================================================ */

// ── Create Issue Modal ────────────────────────────────────────

function openCreateModal() {
  const modal = document.getElementById('createModal');
  if (modal) {
    modal.classList.add('open');
    const summary = modal.querySelector('input[name="summary"]');
    if (summary) setTimeout(() => summary.focus(), 50);
  }
}

function closeCreateModal(e) {
  const modal = document.getElementById('createModal');
  if (!modal) return;
  if (!e || e.target === modal) {
    modal.classList.remove('open');
  }
}

// ── Issue Type Field Toggling (Create Modal) ──────────────────

function onIssueTypeChange(type) {
  const storyFields = document.getElementById('storyFields');
  const bugFields   = document.getElementById('bugFields');
  if (!storyFields || !bugFields) return;

  const t = (type || '').toLowerCase();
  storyFields.style.display = (t === 'story') ? 'block' : 'none';
  bugFields.style.display   = (t === 'bug')   ? 'block' : 'none';
}

// ── Keyboard: Esc closes any open modal ──────────────────────

document.addEventListener('keydown', function(e) {
  if (e.key !== 'Escape') return;
  ['createModal', 'editModal', 'deleteModal'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el && el.classList.contains('open')) el.classList.remove('open');
  });
});

// ── Init on DOM ready ─────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
  // Set correct initial state for issue-type fields in create modal
  var typeSelect = document.getElementById('modalIssueType');
  if (typeSelect) {
    onIssueTypeChange(typeSelect.value);
  }
});
