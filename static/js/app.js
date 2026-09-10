/**
 * LocalPDF Studio - Global JavaScript Utilities
 */

// Theme manager: sinkron dengan guard script di <head> base.html
function initTheme() {
    const toggleBtn = document.getElementById('theme-toggle');

    const updateBtnTooltip = (dark) => {
        if (!toggleBtn) return;
        const tip = dark ? 'Ganti ke tema terang' : 'Ganti ke tema gelap';
        toggleBtn.setAttribute('title', tip);
        toggleBtn.setAttribute('aria-label', tip);
    };

    const applyTheme = (dark) => {
        document.documentElement.classList.toggle('dark', dark);
        try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (e) {}
        updateBtnTooltip(dark);
    };

    if (toggleBtn) {
        updateBtnTooltip(document.documentElement.classList.contains('dark'));
        toggleBtn.addEventListener('click', () => {
            applyTheme(!document.documentElement.classList.contains('dark'));
            lucide.createIcons(); // render ulang ikon sun/moon
        });
    }

    // Sinkron antar-tab
    window.addEventListener('storage', (e) => {
        if (e.key === 'theme' && e.newValue) {
            const dark = e.newValue === 'dark';
            document.documentElement.classList.toggle('dark', dark);
            updateBtnTooltip(dark);
        }
    });
}

initTheme();

// Toast Notification Manager
function showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium transition-all transform duration-300 translate-y-2 opacity-0 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200';

    let iconChip = '';
    let iconSvg = '';

    if (type === 'success') {
        iconChip = 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400';
        iconSvg = `<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`;
    } else if (type === 'error') {
        iconChip = 'bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400';
        iconSvg = `<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`;
    } else if (type === 'warning') {
        iconChip = 'bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-400';
        iconSvg = `<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>`;
    } else {
        iconChip = 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300';
        iconSvg = `<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
    }

    toast.innerHTML = `
        <span class="flex items-center justify-center w-8 h-8 rounded-lg ${iconChip} [&>svg]:w-4 [&>svg]:h-4">${iconSvg}</span>
        <span class="flex-1">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-300 p-0.5 rounded-lg">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    // Auto remove
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Format bytes helper
function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Natural Sort function for filenames in JavaScript
function naturalSortCompare(a, b) {
    return String(a || '').localeCompare(String(b || ''), undefined, { numeric: true, sensitivity: 'base' });
}

// Download Helper
function triggerDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    if (filename) a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Setup common dropzone drag-and-drop
function setupDropzone(dropzoneEl, fileInputEl, onFilesSelected) {
    if (!dropzoneEl || !fileInputEl) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzoneEl.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneEl.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzoneEl.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneEl.classList.remove('dragover');
        }, false);
    });

    dropzoneEl.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0 && typeof onFilesSelected === 'function') {
            onFilesSelected(Array.from(dt.files));
        }
    });

    // Clicking anywhere on the dropzone or its button triggers the file input dialog
    dropzoneEl.addEventListener('click', (e) => {
        if (e.target === fileInputEl) return;
        fileInputEl.click();
    });

    fileInputEl.addEventListener('change', () => {
        if (fileInputEl.files && fileInputEl.files.length > 0 && typeof onFilesSelected === 'function') {
            onFilesSelected(Array.from(fileInputEl.files));
        }
        fileInputEl.value = ''; // Reset so the user can re-select the same file(s)
    });
}

// Back-to-Top Button Manager
function initBackToTop() {
    const btn = document.getElementById('btn-back-to-top');
    if (!btn) return;

    const onScroll = () => {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBackToTop);
} else {
    initBackToTop();
}

/**
 * Membuka dialog native File Explorer modern di komputer lokal.
 * @param {Object} options { initialDir, title, triggerBtn }
 * @returns {Promise<string|null>} Path folder yang dipilih atau null jika dibatalkan
 */
async function pickModernFolder(options = {}) {
    const triggerBtn = options.triggerBtn;
    let originalBtnHtml = '';

    if (triggerBtn && triggerBtn.tagName === 'BUTTON') {
        originalBtnHtml = triggerBtn.innerHTML;
        triggerBtn.disabled = true;
        triggerBtn.classList.add('opacity-80', 'cursor-wait');
        triggerBtn.innerHTML = `
            <span class="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            <span>Membuka...</span>
        `;
    }

    try {
        const initParam = options.initialDir ? encodeURIComponent(options.initialDir) : '';
        const titleParam = options.title ? encodeURIComponent(options.title) : '';
        const res = await fetch(`/api/pick-folder?initial_dir=${initParam}&title=${titleParam}`, {
            method: 'POST'
        });
        const data = await res.json();
        if (data.success && data.path) {
            return data.path;
        }
        return null;
    } catch (err) {
        console.error('Gagal membuka pemilih folder:', err);
        showToast('Gagal memunculkan dialog File Explorer.', 'error');
        return null;
    } finally {
        if (triggerBtn && triggerBtn.tagName === 'BUTTON') {
            triggerBtn.disabled = false;
            triggerBtn.classList.remove('opacity-80', 'cursor-wait');
            triggerBtn.innerHTML = originalBtnHtml;
            if (window.lucide) lucide.createIcons();
        }
    }
}

/**
 * Mengatur tombol dinamis pintar untuk input path folder lokal:
 * - Jika input KOSONG: tombol bertuliskan "Pilih Folder", klik membuka File Explorer pop-up.
 * - Jika input TERISI: tombol bertuliskan label aksi (misal "Pindai Gambar" / "Pindai Folder"), klik memanggil scanAction.
 */
function bindFolderInputSmartButton({ inputId, buttonId, scanAction, labelFilled = 'Pindai Folder', iconFilled = 'search' }) {
    const inputEl = document.getElementById(inputId);
    const btnEl = document.getElementById(buttonId);
    if (!inputEl || !btnEl) return;

    const updateState = () => {
        const val = inputEl.value.trim();
        if (!val) {
            // State A: Kosong -> Tombol "Pilih Folder"
            btnEl.innerHTML = `<i data-lucide="folder-search" class="w-4 h-4"></i><span>Pilih Folder</span>`;
            btnEl.title = "Buka File Explorer untuk memilih folder";
        } else {
            // State B: Terisi -> Tombol "Pindai Gambar" / "Pindai Folder"
            btnEl.innerHTML = `<i data-lucide="${iconFilled}" class="w-4 h-4"></i><span>${labelFilled}</span>`;
            btnEl.title = `Pindai file dari folder "${val}"`;
        }
        if (window.lucide) lucide.createIcons();
    };

    // Handle klik tombol
    btnEl.addEventListener('click', async (e) => {
        const val = inputEl.value.trim();
        if (!val) {
            // Tombol dalam mode "Pilih Folder"
            const selectedPath = await pickModernFolder({
                initialDir: val,
                title: 'Pilih Folder',
                triggerBtn: btnEl
            });
            if (selectedPath) {
                inputEl.value = selectedPath;
                inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                inputEl.dispatchEvent(new Event('change', { bubbles: true }));
                updateState();
                // Jalankan pemindaian otomatis
                if (typeof scanAction === 'function') {
                    scanAction();
                }
            }
        } else {
            // Tombol dalam mode "Pindai"
            if (typeof scanAction === 'function') {
                scanAction();
            }
        }
    });

    // Handle ketik / paste / hapus teks pada input
    inputEl.addEventListener('input', updateState);
    inputEl.addEventListener('change', updateState);

    // Handle tombol Enter pada keyboard
    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const val = inputEl.value.trim();
            if (val && typeof scanAction === 'function') {
                scanAction();
            }
        }
    });

    // Inisialisasi awal
    updateState();
}

/**
 * Helper untuk tombol pemilih folder output simpan langsung
 * @param {string} inputId ID elemen input target (misal: 'custom-output-dir')
 * @param {HTMLElement} [btnEl] Tombol pemicu
 */
async function selectCustomOutputDir(inputId, btnEl) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const trigger = btnEl || (typeof window !== 'undefined' && window.event ? (window.event.currentTarget || (window.event.target ? window.event.target.closest('button') : null)) : null);
    const selected = await pickModernFolder({
        initialDir: input.value.trim(),
        title: 'Pilih Folder Tujuan Simpan',
        triggerBtn: trigger
    });
    if (selected) {
        input.value = selected;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
}


