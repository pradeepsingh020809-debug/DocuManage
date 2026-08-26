/**
 * DocuVault - Explorer Controller (Grid/List, Batch Selection, Actions)
 */

document.addEventListener('DOMContentLoaded', () => {
  initStarButtons();
  initBatchSelection();
});

// Star / Unstar
function initStarButtons() {
  document.querySelectorAll('.doc-star-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const docId = btn.getAttribute('data-doc-id');
      if (!docId) return;

      try {
        const response = await fetch(`/documents/${docId}/star`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.is_starred) {
            btn.classList.add('starred');
            btn.innerHTML = '<i data-lucide="star" style="width:16px; height:16px; fill:#f59e0b; color:#f59e0b;"></i>';
            showToast('Document added to Starred', 'success');
          } else {
            btn.classList.remove('starred');
            btn.innerHTML = '<i data-lucide="star" style="width:16px; height:16px;"></i>';
            showToast('Document removed from Starred', 'info');
          }
          if (window.lucide) lucide.createIcons();
        }
      } catch (err) {
        console.error('Star toggle failed', err);
      }
    });
  });
}

// Batch Document Selection
function initBatchSelection() {
  const selectAllCheckbox = document.getElementById('selectAllDocs');
  const docCheckboxes = document.querySelectorAll('.doc-select-checkbox');
  const batchBar = document.getElementById('batchActionsBar');
  const batchCount = document.getElementById('batchSelectedCount');
  const batchDeleteBtn = document.getElementById('batchDeleteBtn');
  const batchMoveBtn = document.getElementById('batchMoveBtn');
  const batchDownloadBtn = document.getElementById('batchDownloadBtn');
  const clearSelectionBtn = document.getElementById('clearSelectionBtn');

  function updateBatchState() {
    const selected = Array.from(docCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
    
    if (batchCount) batchCount.textContent = selected.length;

    if (selected.length > 0) {
      if (batchBar) batchBar.classList.add('active');
    } else {
      if (batchBar) batchBar.classList.remove('active');
      if (selectAllCheckbox) selectAllCheckbox.checked = false;
    }

    // Highlight card/row
    docCheckboxes.forEach(cb => {
      const card = cb.closest('.doc-card') || cb.closest('tr');
      if (card) {
        if (cb.checked) card.classList.add('selected');
        else card.classList.remove('selected');
      }
    });
  }

  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', () => {
      docCheckboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
      });
      updateBatchState();
    });
  }

  docCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      updateBatchState();
    });
  });

  if (clearSelectionBtn) {
    clearSelectionBtn.addEventListener('click', () => {
      docCheckboxes.forEach(cb => { cb.checked = false; });
      if (selectAllCheckbox) selectAllCheckbox.checked = false;
      updateBatchState();
    });
  }

  // Batch Delete
  if (batchDeleteBtn) {
    batchDeleteBtn.addEventListener('click', async () => {
      const selected = Array.from(docCheckboxes).filter(cb => cb.checked).map(cb => parseInt(cb.value));
      if (selected.length === 0) return;

      if (!confirm(`Move ${selected.length} selected document(s) to Trash?`)) return;

      try {
        const res = await fetch('/api/documents/batch-delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ doc_ids: selected })
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message, 'success');
          setTimeout(() => window.location.reload(), 600);
        } else {
          showToast(data.error || 'Batch delete failed', 'danger');
        }
      } catch (err) {
        showToast('Error executing batch delete', 'danger');
      }
    });
  }

  // Batch Move Modal trigger
  if (batchMoveBtn) {
    batchMoveBtn.addEventListener('click', () => {
      const selected = Array.from(docCheckboxes).filter(cb => cb.checked).map(cb => parseInt(cb.value));
      if (selected.length === 0) return;
      openModal('batchMoveModal');
    });
  }

  // Batch Move Form Submit
  const batchMoveForm = document.getElementById('batchMoveForm');
  if (batchMoveForm) {
    batchMoveForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const selected = Array.from(docCheckboxes).filter(cb => cb.checked).map(cb => parseInt(cb.value));
      const targetFolderId = document.getElementById('batchMoveFolderSelect').value;

      try {
        const res = await fetch('/api/documents/batch-move', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ doc_ids: selected, folder_id: targetFolderId })
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message, 'success');
          setTimeout(() => window.location.reload(), 600);
        } else {
          showToast(data.error || 'Batch move failed', 'danger');
        }
      } catch (err) {
        showToast('Error executing batch move', 'danger');
      }
    });
  }

  // Batch Download ZIP
  if (batchDownloadBtn) {
    batchDownloadBtn.addEventListener('click', () => {
      const selected = Array.from(docCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
      if (selected.length === 0) return;

      // Submit via hidden form to trigger browser download
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/api/documents/batch-download';
      form.style.display = 'none';

      selected.forEach(id => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'doc_ids';
        input.value = id;
        form.appendChild(input);
      });

      document.body.appendChild(form);
      form.submit();
      form.remove();
      showToast('Preparing ZIP download archive...', 'info');
    });
  }
}
