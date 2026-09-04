# LocalPDF Studio - Development Guidelines

## Frontend & Templating Invariants

### 1. Theme Handling (Light / Dark Mode)
- **Default Theme**: LocalPDF Studio defaults to **Light Theme** for initial visits.
- **Explicit Preference Guard**: The anti-FOUC guard in `templates/base.html` must only activate dark mode if explicitly saved by the user (`localStorage.getItem('theme') === 'dark'`). Never force dark mode solely via OS media query (`prefers-color-scheme: dark`) without explicit user opt-in.
- **Toggle State & Affordance**:
  - In Light Theme, the toggle button displays the Moon icon with tooltip *"Ganti ke tema gelap"*.
  - In Dark Theme, the toggle button displays the Sun icon with tooltip *"Ganti ke tema terang"*.
  - Always update `title` and `aria-label` dynamically upon theme transition.

### 2. Static Assets & Cache Management
- **Cache Busting**: Any script or stylesheet referenced in `templates/base.html` (or other templates) must include a version query parameter (e.g., `/static/css/style.css?v=1.2`, `/static/js/app.js?v=1.2`).
- **Version Bumping**: Whenever modifying `static/js/app.js` or `static/css/style.css`, increment the version query parameter in the referencing template(s) to avoid stale browser cache issues.
