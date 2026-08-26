/**
 * DocuVault - Universal In-Browser Document Previewer
 */

document.addEventListener('DOMContentLoaded', () => {
  initDocumentPreview();
});

function initDocumentPreview() {
  document.querySelectorAll('[data-preview-doc-id]').forEach(elem => {
    elem.addEventListener('click', (e) => {
      e.preventDefault();
      const docId = elem.getAttribute('data-preview-doc-id');
      if (docId) openDocumentPreview(docId);
    });
  });
}

async function openDocumentPreview(docId) {
  const modal = document.getElementById('previewModal');
  const titleElem = document.getElementById('previewDocTitle');
  const bodyElem = document.getElementById('previewBody');
  const downloadLink = document.getElementById('previewDownloadBtn');
  const detailsLink = document.getElementById('previewDetailsBtn');

  if (!modal || !bodyElem) return;

  // Show modal with loading state
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
  bodyElem.innerHTML = '<div class="preview-spinner"></div>';
  if (titleElem) titleElem.textContent = 'Loading preview...';

  try {
    const res = await fetch(`/documents/${docId}/preview-data`);
    if (!res.ok) throw new Error('Unable to fetch preview data');
    const doc = await res.json();

    if (titleElem) titleElem.textContent = doc.title || doc.filename;
    if (downloadLink) downloadLink.href = doc.download_url;
    if (detailsLink) detailsLink.href = `/documents/${doc.id}`;

    renderPreviewContent(doc, bodyElem);

  } catch (err) {
    bodyElem.innerHTML = `
      <div style="text-align:center; padding:3rem; color:var(--text-muted);">
        <i data-lucide="alert-circle" style="width:48px; height:48px; color:var(--danger); margin-bottom:1rem;"></i>
        <h3 style="margin-bottom:0.5rem;">Preview Not Available</h3>
        <p style="font-size:0.9rem;">This file format cannot be previewed directly in the browser.</p>
        <a href="/documents/${docId}/download" class="btn btn-primary" style="margin-top:1rem;">
          <i data-lucide="download"></i> Download File
        </a>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
  }
}

function renderPreviewContent(doc, container) {
  const ext = doc.extension.toLowerCase();
  const category = doc.category;

  // 1. PDF
  if (ext === 'pdf') {
    container.innerHTML = `
      <iframe src="${doc.stream_url}" class="preview-pdf-frame"></iframe>
    `;
  }
  // 2. Images
  else if (category === 'image' || ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'].includes(ext)) {
    container.innerHTML = `
      <div class="preview-image-container">
        <img src="${doc.stream_url}" alt="${doc.title}">
      </div>
    `;
  }
  // 3. Markdown
  else if (['md', 'markdown'].includes(ext)) {
    container.innerHTML = `
      <div class="preview-markdown-container">
        ${doc.rendered_html || `<pre>${escapeHtml(doc.raw_text || '')}</pre>`}
      </div>
    `;
  }
  // 4. Spreadsheets (CSV / TSV)
  else if (['csv', 'tsv'].includes(ext) && doc.table_rows) {
    let tableHtml = '<div class="preview-csv-container"><table class="preview-csv-table">';
    doc.table_rows.forEach((row, rIdx) => {
      tableHtml += '<tr>';
      row.forEach(cell => {
        if (rIdx === 0) {
          tableHtml += `<th>${escapeHtml(cell)}</th>`;
        } else {
          tableHtml += `<td>${escapeHtml(cell)}</td>`;
        }
      });
      tableHtml += '</tr>';
    });
    tableHtml += '</table></div>';
    container.innerHTML = tableHtml;
  }
  // 5. Code & Text
  else if (category === 'code' || category === 'text' || doc.raw_text !== undefined) {
    container.innerHTML = `
      <div class="preview-code-container">
        <pre><code>${escapeHtml(doc.raw_text || 'File is empty.')}</code></pre>
      </div>
    `;
  }
  // 6. Audio / Video
  else if (category === 'audio') {
    container.innerHTML = `
      <div style="text-align:center;">
        <audio controls src="${doc.stream_url}" style="width:400px; max-width:100%;"></audio>
      </div>
    `;
  }
  else if (category === 'video') {
    container.innerHTML = `
      <div style="max-width:900px; width:100%;">
        <video controls src="${doc.stream_url}" style="width:100%; border-radius:var(--radius-md);"></video>
      </div>
    `;
  }
  else {
    container.innerHTML = `
      <div style="text-align:center; padding:3rem;">
        <i data-lucide="file" style="width:48px; height:48px; color:var(--primary); margin-bottom:1rem;"></i>
        <h3>Preview Not Available</h3>
        <p style="font-size:0.9rem; color:var(--text-muted);">This file type (${ext.toUpperCase()}) cannot be rendered directly in the preview.</p>
        <a href="${doc.download_url}" class="btn btn-primary" style="margin-top:1.25rem;">
          <i data-lucide="download"></i> Download File (${doc.size})
        </a>
      </div>
    `;
  }

  if (window.lucide) lucide.createIcons();
}

function closePreview() {
  const modal = document.getElementById('previewModal');
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
    const bodyElem = document.getElementById('previewBody');
    if (bodyElem) bodyElem.innerHTML = '';
  }
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
