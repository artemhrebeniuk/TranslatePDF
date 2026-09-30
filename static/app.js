/**
 * ReviseTranslate Studio • Frontend Controller
 * Conforming to ReviseCheck Design System & Spatial Inspection Specs
 */

// Application State
const state = {
  currentDocId: null,
  filename: 'Yeshchenko_MO_063758776_UKR_0.pdf',
  totalPages: 3,
  origPage: 1,
  transPage: 1,
  zoom: 1.0,
  rotation: 0, // Parallel document rotation in degrees: 0, 90, 180, 270
  viewMode: 'split', // 'split' | 'orig' | 'rev'
  sourceLang: 'uk',
  targetLang: 'en',
  mode: 'medical',
  segments: [],
  filteredSegments: [],
  activeCategory: 'all',
  searchQuery: '',
  isTranslating: false,
  isTranslated: false,
  pdfBase64: null,
  translatedPdfBase64: null,
  customEdits: {}
};

// DOM Cache
const dom = {
  // Presets
  btnPresetMedical: document.getElementById('btnPresetMedical'),
  btnPresetCadastral: document.getElementById('btnPresetCadastral'),
  
  // Controls & Workflow
  directionToggle: document.getElementById('directionToggle'),
  dirButtons: document.querySelectorAll('#directionToggle .pill-btn'),
  modeToggle: document.getElementById('modeToggle'),
  modeButtons: document.querySelectorAll('#modeToggle .pill-btn'),
  modeMedicalBtn: document.getElementById('modeMedicalBtn'),
  modeCadastralBtn: document.getElementById('modeCadastralBtn'),
  fileDropLabel: document.getElementById('fileDropLabel'),
  pdfFileInput: document.getElementById('pdfFileInput'),
  currentFileName: document.getElementById('currentFileName'),
  btnTranslate: document.getElementById('btnTranslate'),
  translateBtnText: document.getElementById('translateBtnText'),
  btnDownload: document.getElementById('btnDownload'),
  downloadBtnText: document.getElementById('downloadBtnText'),

  // Inspector Toolbar
  viewModeTabs: document.getElementById('viewModeTabs'),
  viewModeButtons: document.querySelectorAll('#viewModeTabs .mode-tab'),
  btnRotateCw: document.getElementById('btnRotateCw'),
  btnRotateReset: document.getElementById('btnRotateReset'),
  rotationBadge: document.getElementById('rotationBadge'),
  btnZoomOut: document.getElementById('btnZoomOut'),
  btnZoomIn: document.getElementById('btnZoomIn'),
  btnFitWidth: document.getElementById('btnFitWidth'),
  zoomLevelDisplay: document.getElementById('zoomLevelDisplay'),

  // Panes & Grid
  dualPanesGrid: document.getElementById('dualPanesGrid'),
  paneOrig: document.getElementById('paneOrig'),
  paneTrans: document.getElementById('paneTrans'),
  origBadge: document.getElementById('origBadge'),
  transBadge: document.getElementById('transBadge'),
  btnOrigPrev: document.getElementById('btnOrigPrev'),
  btnOrigNext: document.getElementById('btnOrigNext'),
  origPageIndicator: document.getElementById('origPageIndicator'),
  btnTransPrev: document.getElementById('btnTransPrev'),
  btnTransNext: document.getElementById('btnTransNext'),
  transPageIndicator: document.getElementById('transPageIndicator'),
  origImg: document.getElementById('origImg'),
  origEmpty: document.getElementById('origEmpty'),
  transImg: document.getElementById('transImg'),
  transEmpty: document.getElementById('transEmpty'),
  origViewport: document.getElementById('origViewport'),
  transViewport: document.getElementById('transViewport'),

  // Segments Table
  segmentsCountBadge: document.getElementById('segmentsCountBadge'),
  segmentFilterInput: document.getElementById('segmentFilterInput'),
  categoryPills: document.getElementById('categoryPills'),
  catPillButtons: document.querySelectorAll('#categoryPills .cat-pill'),
  btnApplyEdits: document.getElementById('btnApplyEdits'),
  segmentsTableBody: document.getElementById('segmentsTableBody')
};

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  // Automatically load the primary medical sample (DILA Lab Report)
  loadPresetSample('sample_medical');
});

function initEventListeners() {
  // Presets
  if (dom.btnPresetMedical) {
    dom.btnPresetMedical.addEventListener('click', () => {
      loadPresetSample('sample_medical');
    });
  }

  // Translation Direction Switching
  if (dom.dirButtons && dom.dirButtons.length > 0) {
    dom.dirButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        dom.dirButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.sourceLang = btn.dataset.src;
        state.targetLang = btn.dataset.tgt;
        updateBadges();
      });
    });
  }

  // Domain Mode Switching (if present)
  if (dom.modeButtons && dom.modeButtons.length > 0) {
    dom.modeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        dom.modeButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.mode = btn.dataset.mode;
      });
    });
  }

  // File Upload
  dom.pdfFileInput.addEventListener('change', handleFileUpload);

  // Drag and drop on the dropzone
  dom.fileDropLabel.addEventListener('dragover', (e) => {
    e.preventDefault();
    dom.fileDropLabel.style.borderColor = 'var(--emerald-primary)';
    dom.fileDropLabel.style.background = 'var(--emerald-surface)';
  });
  dom.fileDropLabel.addEventListener('dragleave', () => {
    dom.fileDropLabel.style.borderColor = '';
    dom.fileDropLabel.style.background = '';
  });
  dom.fileDropLabel.addEventListener('drop', (e) => {
    e.preventDefault();
    dom.fileDropLabel.style.borderColor = '';
    dom.fileDropLabel.style.background = '';
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  // Translate Action
  dom.btnTranslate.addEventListener('click', runTranslation);

  // Download Action
  if (dom.btnDownload) {
    dom.btnDownload.addEventListener('click', handleDownloadClick);
  }

  // View Mode Tabs
  dom.viewModeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dom.viewModeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      setViewMode(btn.dataset.view);
    });
  });

  // Parallel Synchronous Document Rotation Controls
  dom.btnRotateCw.addEventListener('click', () => {
    // Cycle: 0° -> 90° -> 180° -> 270° -> 0°
    state.rotation = (state.rotation + 90) % 360;
    applyRotationAndZoom();
  });

  dom.btnRotateReset.addEventListener('click', () => {
    state.rotation = 0;
    applyRotationAndZoom();
  });

  // Zoom Controls
  dom.btnZoomIn.addEventListener('click', () => {
    state.zoom = Math.min(2.5, Math.round((state.zoom + 0.15) * 100) / 100);
    applyRotationAndZoom();
  });

  dom.btnZoomOut.addEventListener('click', () => {
    state.zoom = Math.max(0.4, Math.round((state.zoom - 0.15) * 100) / 100);
    applyRotationAndZoom();
  });

  dom.btnFitWidth.addEventListener('click', () => {
    state.zoom = 1.0;
    applyRotationAndZoom();
  });

  // Pagination Controls
  dom.btnOrigPrev.addEventListener('click', () => changePage(-1, 'orig'));
  dom.btnOrigNext.addEventListener('click', () => changePage(1, 'orig'));
  dom.btnTransPrev.addEventListener('click', () => changePage(-1, 'trans'));
  dom.btnTransNext.addEventListener('click', () => changePage(1, 'trans'));

  // Segment Table Search & Filter (if present)
  if (dom.segmentFilterInput) {
    dom.segmentFilterInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.toLowerCase().trim();
      filterAndRenderSegments();
    });
  }

  if (dom.catPillButtons && dom.catPillButtons.length > 0) {
    dom.catPillButtons.forEach(pill => {
      pill.addEventListener('click', () => {
        dom.catPillButtons.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        state.activeCategory = pill.dataset.cat;
        filterAndRenderSegments();
      });
    });
  }

  if (dom.btnApplyEdits) {
    dom.btnApplyEdits.addEventListener('click', applyCustomSegmentEdits);
  }
}

// Preset Switching
function setActivePreset(type) {
  if (type === 'medical') {
    dom.btnPresetMedical.classList.add('active');
    dom.btnPresetCadastral.classList.remove('active');
    // Set direction UKR -> EN
    setDirection('uk', 'en');
    setMode('medical');
  } else {
    dom.btnPresetCadastral.classList.add('active');
    dom.btnPresetMedical.classList.remove('active');
    // Set direction EN -> UKR
    setDirection('en', 'uk');
    setMode('cadastral');
  }
}

function setDirection(src, tgt) {
  state.sourceLang = src;
  state.targetLang = tgt;
  dom.dirButtons.forEach(btn => {
    if (btn.dataset.src === src && btn.dataset.tgt === tgt) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  updateBadges();
}

function setMode(mode) {
  state.mode = mode;
  dom.modeButtons.forEach(btn => {
    if (btn.dataset.mode === mode) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

function updateBadges() {
  const srcLabel = state.sourceLang === 'uk' ? 'UKR' : 'EN';
  const tgtLabel = state.targetLang === 'en' ? 'EN' : 'UKR';
  dom.origBadge.textContent = `Doc A • ${srcLabel}`;
  dom.transBadge.textContent = `Doc B • ${tgtLabel}`;
}

// Load Sample Document from Server
async function loadPresetSample(sampleId) {
  try {
    setLoadingState(true, 'Loading preset document...');
    const response = await fetch('/api/load_sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sample_id: sampleId })
    });
    const data = await response.json();
    handleLoadedDocument(data);
  } catch (err) {
    console.error('Failed to load preset sample:', err);
  } finally {
    setLoadingState(false);
  }
}

// Handle Custom PDF File Upload
function handleFileUpload(e) {
  const file = e.target.files?.[0];
  if (file) {
    uploadFile(file);
  }
}

async function uploadFile(file) {
  try {
    setLoadingState(true, 'Uploading and analyzing document layers...');
    
    // Read file as base64 for serverless multi-worker resilience
    const fileReader = new FileReader();
    fileReader.onload = () => {
      if (typeof fileReader.result === 'string') {
        state.pdfBase64 = fileReader.result.split(',')[1] || null;
      }
    };
    fileReader.readAsDataURL(file);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_lang', state.sourceLang);
    formData.append('target_lang', state.targetLang);
    formData.append('mode', state.mode);

    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    handleLoadedDocument(data);
  } catch (err) {
    console.error('Failed to upload PDF:', err);
  } finally {
    setLoadingState(false);
  }
}

// Set loaded document into state and UI
function handleLoadedDocument(data) {
  state.currentDocId = data.id;
  state.filename = data.filename;
  state.totalPages = data.pages;
  state.origPage = 1;
  state.transPage = 1;
  state.isTranslated = data.translated || false;
  state.segments = data.segments || [];
  state.origPreviews = data.orig_previews || [];
  state.transPreviews = data.trans_previews || [];
  if (data.pdf_base64) {
    state.translatedPdfBase64 = data.pdf_base64;
  }
  state.customEdits = {};

  dom.currentFileName.textContent = `${data.filename} (${data.pages} page${data.pages > 1 ? 's' : ''})`;
  dom.btnTranslate.disabled = false;
  
  updateDownloadButtonUI();

  updatePaginationDisplay();
  renderOriginalPreview();

  if (state.isTranslated) {
    renderTranslatedPreview();
  } else {
    dom.transImg.style.display = 'none';
    dom.transEmpty.style.display = 'flex';
    dom.transEmpty.innerHTML = '<span>Click "Translate Document" or "Download PDF" to generate translation</span>';
  }

  filterAndRenderSegments();
}

function updateDownloadButtonUI() {
  if (!dom.btnDownload) return;
  dom.btnDownload.disabled = false;
  if (state.isTranslated) {
    dom.btnDownload.title = 'Download translated PDF document';
    dom.btnDownload.style.opacity = '1';
    if (dom.downloadBtnText) dom.downloadBtnText.textContent = 'Download PDF';
  } else {
    dom.btnDownload.title = 'Translate & Download PDF';
    dom.btnDownload.style.opacity = '0.9';
    if (dom.downloadBtnText) dom.downloadBtnText.textContent = 'Download PDF';
  }
}

// Run Translation
async function runTranslation() {
  if (!state.currentDocId || state.isTranslating) return;

  try {
    state.isTranslating = true;
    dom.btnTranslate.disabled = true;
    dom.translateBtnText.textContent = 'Translating Layers...';

    const response = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doc_id: state.currentDocId,
        source_lang: state.sourceLang,
        target_lang: state.targetLang,
        mode: state.mode,
        file_base64: state.pdfBase64 || null,
        filename: state.filename || null
      })
    });

    const data = await response.json();
    state.isTranslated = true;
    state.segments = data.segments || [];
    state.transPreviews = data.trans_previews || [];
    if (data.pdf_base64) {
      state.translatedPdfBase64 = data.pdf_base64;
    }
    updateDownloadButtonUI();

    renderTranslatedPreview();
    filterAndRenderSegments();
  } catch (err) {
    console.error('Translation failed:', err);
    showNotification('Translation failed. Please try again.');
  } finally {
    state.isTranslating = false;
    dom.btnTranslate.disabled = false;
    dom.translateBtnText.textContent = 'Translate Document';
  }
}

// Previews & Page Navigation
function renderOriginalPreview() {
  if (!state.currentDocId) return;
  dom.origEmpty.style.display = 'none';
  dom.origImg.style.display = 'block';
  
  const b64 = state.origPreviews && state.origPreviews[state.origPage - 1];
  if (b64 && b64.startsWith('data:')) {
    dom.origImg.src = b64;
  } else {
    dom.origImg.src = `/api/preview/${state.currentDocId}/orig/${state.origPage}?t=${Date.now()}`;
  }
  applyRotationAndZoom();
}

function renderTranslatedPreview() {
  if (!state.currentDocId || !state.isTranslated) return;
  dom.transEmpty.style.display = 'none';
  dom.transImg.style.display = 'block';
  
  const b64 = state.transPreviews && state.transPreviews[state.transPage - 1];
  if (b64 && b64.startsWith('data:')) {
    dom.transImg.src = b64;
  } else {
    dom.transImg.src = `/api/preview/${state.currentDocId}/trans/${state.transPage}?t=${Date.now()}`;
  }
  applyRotationAndZoom();
}

function changePage(delta, target = 'both') {
  if (target === 'orig' || target === 'both') {
    const next = state.origPage + delta;
    if (next >= 1 && next <= state.totalPages) {
      state.origPage = next;
      // In synchronous mode, also change transPage
      if (state.isTranslated) {
        state.transPage = next;
      }
    }
  }

  if (target === 'trans') {
    const next = state.transPage + delta;
    if (next >= 1 && next <= state.totalPages) {
      state.transPage = next;
      state.origPage = next;
    }
  }

  updatePaginationDisplay();
  renderOriginalPreview();
  if (state.isTranslated) {
    renderTranslatedPreview();
  }
}

function updatePaginationDisplay() {
  dom.origPageIndicator.textContent = `Page ${state.origPage} of ${state.totalPages}`;
  dom.transPageIndicator.textContent = `Page ${state.transPage} of ${state.totalPages}`;
  
  dom.btnOrigPrev.disabled = state.origPage <= 1;
  dom.btnOrigNext.disabled = state.origPage >= state.totalPages;
  dom.btnTransPrev.disabled = state.transPage <= 1;
  dom.btnTransNext.disabled = state.transPage >= state.totalPages;
}

// Parallel Synchronous Rotation & Zoom
function applyRotationAndZoom() {
  dom.rotationBadge.textContent = `${state.rotation}°`;
  dom.zoomLevelDisplay.textContent = `${Math.round(state.zoom * 100)}%`;

  const transformStyle = `rotate(${state.rotation}deg) scale(${state.zoom})`;

  // Apply to both Doc A and Doc B simultaneously
  if (dom.origImg) {
    dom.origImg.style.transform = transformStyle;
  }
  if (dom.transImg) {
    dom.transImg.style.transform = transformStyle;
  }

  // When rotated 90 or 270, adjust canvas padding so scrollbars work gracefully
  const isRotatedQuarter = state.rotation === 90 || state.rotation === 270;
  const paddingAmount = isRotatedQuarter ? '80px 40px' : '30px';
  dom.origViewport.style.padding = paddingAmount;
  dom.transViewport.style.padding = paddingAmount;
}

// View Mode Switching ('split' | 'orig' | 'rev')
function setViewMode(mode) {
  state.viewMode = mode;
  dom.dualPanesGrid.classList.remove('mode-orig', 'mode-rev');
  if (mode === 'orig') {
    dom.dualPanesGrid.classList.add('mode-orig');
  } else if (mode === 'rev') {
    dom.dualPanesGrid.classList.add('mode-rev');
  }
}

// Segments Review & Inline Editing
function filterAndRenderSegments() {
  if (!dom.segmentsTableBody) return;
  let list = state.segments;

  if (state.activeCategory !== 'all') {
    list = list.filter(s => s.category === state.activeCategory);
  }

  if (state.searchQuery) {
    list = list.filter(s => 
      (s.original && s.original.toLowerCase().includes(state.searchQuery)) ||
      (s.translated && s.translated.toLowerCase().includes(state.searchQuery))
    );
  }

  state.filteredSegments = list;
  dom.segmentsCountBadge.textContent = `${list.length} Segments`;

  if (list.length === 0) {
    dom.segmentsTableBody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align: center; color: #9ca3af; padding: 24px;">
          No matching segments found for this filter.
        </td>
      </tr>
    `;
    return;
  }

  // Render rows
  const html = list.map((seg, idx) => {
    const catClass = getCategoryClass(seg.category);
    const currentValue = state.customEdits[seg.original] !== undefined 
      ? state.customEdits[seg.original] 
      : seg.translated;

    return `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.72rem; color: #6b7280;">p.${seg.page}</td>
        <td><span class="category-tag ${catClass}">${escapeHtml(seg.category)}</span></td>
        <td style="font-size: 0.8rem; color: #111827; word-break: break-word;">${escapeHtml(seg.original)}</td>
        <td>
          <input 
            type="text" 
            class="table-edit-input" 
            value="${escapeHtml(currentValue)}" 
            data-orig="${escapeHtml(seg.original)}"
            onchange="handleSegmentEdit(this)"
          />
        </td>
      </tr>
    `;
  }).join('');

  dom.segmentsTableBody.innerHTML = html;
}

window.handleSegmentEdit = function(inputEl) {
  const origText = inputEl.getAttribute('data-orig');
  const newText = inputEl.value;
  state.customEdits[origText] = newText;
  dom.btnApplyEdits.disabled = false;
};

async function applyCustomSegmentEdits() {
  if (!state.currentDocId || Object.keys(state.customEdits).length === 0) return;

  try {
    dom.btnApplyEdits.disabled = true;
    dom.btnApplyEdits.textContent = 'Applying...';

    const response = await fetch('/api/update_segments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doc_id: state.currentDocId,
        custom_map: state.customEdits
      })
    });

    const data = await response.json();
    state.segments = data.segments || [];
    if (data.trans_previews) {
      state.transPreviews = data.trans_previews;
    }
    if (data.pdf_base64) {
      state.translatedPdfBase64 = data.pdf_base64;
    }
    renderTranslatedPreview();
    filterAndRenderSegments();
    dom.btnApplyEdits.textContent = 'Apply Edits';
    showNotification('Custom edits applied!');
  } catch (err) {
    console.error('Failed to apply custom edits:', err);
    dom.btnApplyEdits.disabled = false;
    dom.btnApplyEdits.textContent = 'Apply Edits';
    showNotification('Failed to apply edits');
  }
}

function getCategoryClass(category) {
  switch (category) {
    case 'Medical Test': return 'tag-medical';
    case 'Unit / Reference': return 'tag-unit';
    case 'Patient Demographics': return 'tag-patient';
    case 'Doctor / Authority': return 'tag-doctor';
    case 'Legal / Disclaimer': return 'tag-legal';
    default: return 'tag-general';
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function setLoadingState(isLoading, message = '') {
  if (isLoading) {
    dom.origEmpty.style.display = 'flex';
    dom.origEmpty.innerHTML = `<span>${escapeHtml(message)}</span>`;
  }
}

// Download Controller
async function handleDownloadClick() {
  if (!state.currentDocId) {
    showNotification('Please select or upload a document first.');
    return;
  }

  // If not yet translated, automatically run translation before downloading
  if (!state.isTranslated) {
    showNotification('Translating document before download...');
    await runTranslation();
    if (!state.isTranslated) {
      showNotification('Translation failed. Please try again.');
      return;
    }
  }

  await executeDownload();
}

function getDownloadFilename() {
  if (state.filename) {
    const base = state.filename.replace(/\.pdf$/i, '');
    const tgt = state.targetLang ? state.targetLang.toUpperCase() : 'EN';
    return `${base}_${tgt}_Translated.pdf`;
  }
  return 'Translated_Document.pdf';
}

function downloadBase64Pdf(base64Data, filename) {
  try {
    const binaryString = atob(base64Data);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: 'application/pdf' });
    downloadBlob(blob, filename);
  } catch (err) {
    console.error('Base64 decode failed, falling back to network fetch:', err);
    fetchAndDownloadPdf();
  }
}

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    if (a.parentNode) a.parentNode.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 1000);
}

async function fetchAndDownloadPdf() {
  const btnText = dom.downloadBtnText;
  const origText = btnText ? btnText.textContent : 'Download PDF';
  if (btnText) btnText.textContent = 'Downloading...';

  try {
    const response = await fetch(`/api/download/${state.currentDocId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_base64: state.pdfBase64 || null,
        filename: state.filename || null,
        source_lang: state.sourceLang,
        target_lang: state.targetLang,
        mode: state.mode,
        custom_translations: state.customEdits || null
      })
    });

    if (response.ok) {
      const blob = await response.blob();
      downloadBlob(blob, getDownloadFilename());
      showNotification('PDF downloaded successfully!');
      return;
    }

    // Secondary GET fallback
    const getResp = await fetch(`/api/download/${state.currentDocId}`);
    if (getResp.ok) {
      const blob = await getResp.blob();
      downloadBlob(blob, getDownloadFilename());
      showNotification('PDF downloaded successfully!');
      return;
    }

    throw new Error('Server returned ' + response.status);
  } catch (err) {
    console.error('Download error:', err);
    showNotification('Download issue detected. Using direct link fallback...');
    const a = document.createElement('a');
    a.href = `/api/download/${state.currentDocId}`;
    a.download = getDownloadFilename();
    a.target = '_blank';
    a.click();
  } finally {
    if (btnText) btnText.textContent = origText;
  }
}

async function executeDownload() {
  // 1. If base64 is already in memory, trigger instant 0ms download
  if (state.translatedPdfBase64) {
    downloadBase64Pdf(state.translatedPdfBase64, getDownloadFilename());
    showNotification('PDF downloaded successfully!');
    return;
  }

  // 2. Fetch using multi-worker serverless POST
  await fetchAndDownloadPdf();
}

function showNotification(message, duration = 3000) {
  let toast = document.getElementById('appToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'appToast';
    toast.className = 'app-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.display = 'flex';
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.display = 'none';
  }, duration);
}
