/**
 * DocuVault - Instant Live Search Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  initLiveSearch();
});

function initLiveSearch() {
  const searchInput = document.getElementById('globalSearchInput');
  const dropdown = document.getElementById('searchResultsDropdown');
  const searchForm = document.getElementById('globalSearchForm');

  if (!searchInput || !dropdown) return;

  let debounceTimer = null;

  searchInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    clearTimeout(debounceTimer);

    if (val.length < 2) {
      dropdown.classList.remove('active');
      dropdown.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(val)}`);
        const data = await res.json();
        renderDropdownResults(data.results, val);
      } catch (err) {
        console.error('Live search error:', err);
      }
    }, 250);
  });

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('active');
    }
  });

  function renderDropdownResults(results, query) {
    if (!results || results.length === 0) {
      dropdown.innerHTML = `
        <div style="padding:1rem; text-align:center; color:var(--text-muted); font-size:0.85rem;">
          No documents found matching "${escapeHtml(query)}"
        </div>
      `;
      dropdown.classList.add('active');
      return;
    }

    let html = '';
    results.forEach(doc => {
      html += `
        <a href="/documents/${doc.id}" class="search-result-item">
          <div style="width:32px; height:32px; border-radius:var(--radius-sm); background:var(--bg-subtle); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
            <i data-lucide="file-text" style="width:16px; height:16px; color:var(--primary);"></i>
          </div>
          <div style="flex:1; min-width:0;">
            <div style="font-weight:600; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(doc.title)}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); display:flex; gap:0.5rem; align-items:center;">
              <span style="text-transform:capitalize;">${doc.category}</span>
              <span>•</span>
              <span>${doc.formatted_size}</span>
            </div>
            ${doc.search_snippet ? `<div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(doc.search_snippet)}</div>` : ''}
          </div>
        </a>
      `;
    });

    html += `
      <div style="padding:0.6rem 1rem; background:var(--bg-subtle); text-align:center; border-top:1px solid var(--border-subtle);">
        <a href="/search?q=${encodeURIComponent(query)}" style="font-size:0.8rem; font-weight:600; color:var(--primary); text-decoration:none;">
          View all results for "${escapeHtml(query)}" →
        </a>
      </div>
    `;

    dropdown.innerHTML = html;
    dropdown.classList.add('active');
    if (window.lucide) lucide.createIcons();
  }
}
