/**
 * Copies runtime assets from node_modules into static/ so the app runs
 * fully offline. Run once via `npm run vendor` (idempotent).
 */
import { copyFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const nm = (...p) => join(root, 'node_modules', ...p);
const dest = (...p) => {
  const full = join(root, ...p);
  mkdirSync(dirname(full), { recursive: true });
  return full;
};

// Icons (UMD build exposes window.lucide)
copyFileSync(nm('lucide', 'dist', 'umd', 'lucide.min.js'), dest('static', 'vendor', 'lucide.min.js'));

// Drag & drop sorting (exposes window.Sortable)
copyFileSync(nm('sortablejs', 'Sortable.min.js'), dest('static', 'vendor', 'Sortable.min.js'));

// Plus Jakarta Sans — latin subset, normal style, weights 400–800
for (const weight of [400, 500, 600, 700, 800]) {
  const file = `plus-jakarta-sans-latin-${weight}-normal.woff2`;
  copyFileSync(nm('@fontsource', 'plus-jakarta-sans', 'files', file), dest('static', 'fonts', file));
}

console.log('Vendored: lucide.min.js, Sortable.min.js, 5 font weights -> static/');
