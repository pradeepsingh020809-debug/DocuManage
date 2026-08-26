/**
 * DocuVault - Drag & Drop File Uploader Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  initUploader();
});

function initUploader() {
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('fileUploadInput');
  const queueList = document.getElementById('uploadQueueList');
  const uploadBtn = document.getElementById('startUploadBtn');
  const uploadForm = document.getElementById('uploadForm');

  if (!dropzone || !fileInput) return;

  let selectedFiles = [];

  // Dropzone click
  dropzone.addEventListener('click', () => fileInput.click());

  // Drag events
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    handleFiles(files);
  });

  fileInput.addEventListener('change', () => {
    handleFiles(fileInput.files);
  });

  function handleFiles(files) {
    for (let i = 0; i < files.length; i++) {
      selectedFiles.push(files[i]);
    }
    renderQueue();
  }

  function renderQueue() {
    if (!queueList) return;
    queueList.innerHTML = '';

    if (selectedFiles.length === 0) {
      if (uploadBtn) uploadBtn.disabled = true;
      return;
    }

    if (uploadBtn) uploadBtn.disabled = false;

    selectedFiles.forEach((file, index) => {
      const item = document.createElement('div');
      item.className = 'upload-queue-item';
      item.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.5rem; overflow:hidden;">
          <i data-lucide="file" style="width:16px; height:16px; flex-shrink:0;"></i>
          <span style="font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${file.name}</span>
          <span style="color:var(--text-muted); font-size:0.75rem;">(${formatBytes(file.size)})</span>
        </div>
        <button type="button" style="background:none; border:none; color:var(--danger); cursor:pointer;" onclick="removeUploadFile(${index})">
          <i data-lucide="trash-2" style="width:14px; height:14px;"></i>
        </button>
      `;
      queueList.appendChild(item);
    });

    if (window.lucide) lucide.createIcons();
  }

  window.removeUploadFile = function(index) {
    selectedFiles.splice(index, 1);
    renderQueue();
  };

  // Upload Submission
  if (uploadForm) {
    uploadForm.addEventListener('submit', (e) => {
      e.preventDefault();

      if (selectedFiles.length === 0) {
        showToast('Please select at least one file.', 'warning');
        return;
      }

      const formData = new FormData(uploadForm);
      // Remove any previous file inputs in form data and append actual files
      formData.delete('files');
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

      const progressBar = document.getElementById('uploadProgressBar');
      const progressContainer = document.getElementById('uploadProgressContainer');
      if (progressContainer) progressContainer.style.display = 'block';
      if (uploadBtn) uploadBtn.disabled = true;

      const xhr = new XMLHttpRequest();
      xhr.open('POST', uploadForm.action, true);
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && progressBar) {
          const percent = Math.round((e.loaded / e.total) * 100);
          progressBar.style.width = `${percent}%`;
        }
      };

      xhr.onload = () => {
        if (xhr.status === 200) {
          showToast('Upload completed successfully!', 'success');
          setTimeout(() => {
            window.location.reload();
          }, 800);
        } else {
          let err = 'Upload failed. Please try again.';
          try {
            const res = JSON.parse(xhr.responseText);
            if (res.error) err = res.error;
          } catch (_) {}
          showToast(err, 'danger');
          if (uploadBtn) uploadBtn.disabled = false;
        }
      };

      xhr.onerror = () => {
        showToast('Network error during upload.', 'danger');
        if (uploadBtn) uploadBtn.disabled = false;
      };

      xhr.send(formData);
    });
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
