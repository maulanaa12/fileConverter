const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
    constructor() {
        this.disabled = false;
        this.value = '';
        this.textContent = '';
        this.innerHTML = '';
        this.style = {};
        this.dataset = {};
        this.children = [];
        this.listeners = {};
        this.classes = new Set();
        this.classList = {
            add: name => this.classes.add(name),
            remove: name => this.classes.delete(name),
            contains: name => this.classes.has(name),
        };
    }
    addEventListener(name, callback) { this.listeners[name] = callback; }
    setAttribute(name, value) { this[name] = value; }
    removeAttribute(name) { delete this[name]; }
    querySelector() { return new Element(); }
    appendChild(child) { this.children.push(child); }
    replaceWith() {}
    focus() {}
    showModal() { this.open = true; }
    close() { this.open = false; }
}

const elements = new Map();
const getElement = id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
};
const toasts = [];
let request;
let respond;
const context = vm.createContext({
    document: {
        getElementById: getElement,
        createElement: () => new Element(),
        querySelectorAll: () => [...elements.values()],
    },
    FormData: class { append() {} },
    Sortable: class { destroy() {} option() {} },
    lucide: { createIcons() {} },
    setupDropzone() {},
    addReorderControls() {},
    showToast: (...args) => toasts.push(args),
    formatBytes: bytes => String(bytes),
    openResultModal() {},
    closeResultModal() {},
    console,
    fetch: (url, options) => {
        request = { url, options };
        return new Promise(resolve => { respond = data => resolve({ ok: true, json: async () => data }); });
    },
});
const template = fs.readFileSync(path.join(__dirname, '../templates/organize.html'), 'utf8');
vm.runInContext(template.match(/<script>([\s\S]*?)<\/script>/)[1], context);
const run = code => vm.runInContext(code, context);
const snapshot = () => JSON.parse(run('JSON.stringify(pageItems)'));

async function main() {
    run(`currentPdf = {tempPath: '/base.pdf'};
        appendPagesFromPdf({temp_path: '/base.pdf', filename: 'base.pdf', page_count: 3});
        appendPagesFromPdf({temp_path: '/other.pdf', filename: 'other.pdf', page_count: 2});
        rotatePage(1); toggleDeletePage(0);`);
    getElement('custom-page-order').value = '5-4,2,2';
    run('applyCustomOrder()');
    assert.deepEqual(snapshot().map(p => [p.sourcePath, p.pageNumber, p.rotation]), [
        ['/other.pdf', 2, 0], ['/other.pdf', 1, 0], ['/base.pdf', 2, 90], ['/base.pdf', 2, 90],
    ]);
    run('rotatePage(2)');
    assert.deepEqual(snapshot().map(p => p.rotation), [0, 0, 180, 90]);
    run('toggleDeletePage(0)');
    const unchanged = snapshot();
    for (const invalid of ['1', '0', '1-99999999999999999', '2,', 'no']) {
        getElement('custom-page-order').value = invalid;
        run('applyCustomOrder()');
        assert.deepEqual(snapshot(), unchanged);
    }
    run('openPagePreview(0)');
    assert.match(getElement('preview-page-count').textContent, /ditandai hapus/);
    assert.match(getElement('page-preview-image').src, /path=%2Fother.pdf&page=2&full=true/);
    run('stepPagePreview(-1); changePreviewZoom(0.2)');
    assert.equal(getElement('page-preview-image').style.transform, 'scale(1.2) rotate(90deg)');
    getElement('page-preview-image').listeners.error();
    assert.match(getElement('page-preview-status').textContent, /tidak dapat dimuat/);
    run('closePagePreview()');

    const adding = run("addPdfPages([{name: 'new.pdf'}])");
    run('resetTool(); reverseAllPages(); applyCustomOrder()');
    assert.deepEqual(snapshot(), unchanged);
    assert.equal(await run('processOrganize()'), undefined);
    assert.equal(request.url, '/api/upload');
    respond({success: true, files: [{temp_path: '/new.pdf', filename: 'new.pdf', page_count: 1}]});
    await adding;
    assert.equal(snapshot().length, 5);
    run('reverseAllPages()');
    const beforeSave = snapshot();
    const saving = run('processOrganize()');
    assert.equal(request.url, '/api/organize');
    const payload = JSON.parse(request.options.body);
    assert.deepEqual(payload.operations, beforeSave.map(p => ({source_path: p.sourcePath, page: p.pageNumber, rotation: p.rotation, delete: p.deleted})));
    run('rotateAllPages(); toggleDeletePage(0); resetTool()');
    assert.deepEqual(snapshot(), beforeSave);
    respond({success: true, total_pages: 4, file_size: 100, filename: 'out.pdf', download_url: '/download', save_warning: 'Folder gagal'});
    await saving;
    assert.equal(getElement('btn-download-result').href, '/download');
    assert.match(getElement('result-meta').textContent, /Folder gagal/);
    assert.equal(getElement('btn-save-organize').disabled, false);
    run('resetTool()');
    assert.deepEqual(snapshot(), []);
    assert.equal(getElement('page-preview-dialog').open, false);
    assert.equal(getElement('custom-page-order').value, '');
    console.log('Organize frontend: custom order, duplicates, preview, upload/save locks, payload, warning, reset passed.');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
