---
name: LocalPDF Studio
description: A calm desktop PDF utility with clear type hierarchy, generous spacing, and interaction-only red.
colors:
  primary: "#d52b27"
  primary-hover: "#c42924"
  surface-light: "#ffffff"
  panel-light: "#f8fafc"
  surface-dark: "#1e293b"
  panel-dark: "#0f172a"
  ink-light: "#0f172a"
  body-light: "#475569"
  ink-dark: "#f8fafc"
  body-dark: "#cbd5e1"
  border-light: "#cbd5e1"
  border-dark: "#334155"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "clamp(2rem, 4vw, 3.25rem)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.6
  supporting:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  control: "9px"
  container: "12px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  compact: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  section: "44px"
  spacious: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface-light}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "12px 24px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary-light:
    backgroundColor: "{colors.panel-light}"
    textColor: "{colors.ink-light}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "12px 24px"
  button-secondary-dark:
    backgroundColor: "{colors.surface-dark}"
    textColor: "{colors.ink-dark}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "12px 24px"
  toolbar:
    height: "68px"
    typography: "{typography.label}"
  tool-panel:
    rounded: "{rounded.container}"
    padding: "24px"
---

# Design System: LocalPDF Studio

## Overview

**Creative North Star: "Clean desktop utility application"**

Apply Apple's principles of spacing and type hierarchy to LocalPDF Studio's identity. Clear size and weight contrasts, generous vertical whitespace, and flat tonal panels give practical document tasks room to breathe. Product controls stay compact and recognizable; the interface remains calm and useful rather than becoming a marketing page.

This is the intended system confirmed by the user, not a claim that the entire application already implements it. The supplied Apple DESIGN.md is a reference for principles only. Its fonts, blue palette, marketing layouts, blurred navigation, and card-shadow exception do not transfer to this project.

**Key Characteristics:**
- Plus Jakarta Sans throughout, using only weights 400, 600, and 800.
- Red reserved for interaction; content and structural surfaces remain neutral.
- Pill-shaped CTAs with flat, clearly distinguishable states.
- Generous section spacing and readable type hierarchy in both themes.
- Desktop-first utility workflows with semantic, keyboard-accessible controls.

## Colors

Use the normative frontmatter palette. Red identifies an action, not a section or a paragraph.

### Primary

`primary` is the action accent; `primary-hover` is its hover shade. Use these on actionable buttons, links, and focus indicators. A filled action button is an allowed interactive fill; a red panel, card surface, page background, decorative icon, badge, or body paragraph is not. Navigation may remain neutral.

### Neutral

Alternate `surface-light` and `panel-light` in light mode, and `surface-dark` and `panel-dark` in dark mode. Use the corresponding ink and body tokens for headings and supporting copy. Neutral border tokens serve inputs, necessary dividers, and control boundaries; they do not replace tonal section grouping.

**The Interaction-Only Rule.** Accent red is never a content color or structural surface. Every accent use must identify an actionable control or its interaction state.

Maintain at least 4.5:1 contrast for normal text and 3:1 for large text and essential control indicators. White labels on filled red buttons are the default in both themes. Do not assume red text passes on dark panels: use neutral link text with a red underline when necessary, and verify actual contrast. If a focus outline needs more separation, add a neutral offset rather than inventing a second accent.

## Typography

Use the locally bundled Plus Jakarta Sans for display, body, navigation, inputs, and buttons. The only permitted weights are 400 (reading), 600 (labels and emphasis), and 800 (highest-level headings). Do not introduce 500 or 700, or use Arial as an intentional second family.

The frontmatter defines the target role ladder. Display retains the current responsive headline scale; smaller roles adapt the reference's hierarchy to a utility interface. These roles are normative guidance, not measurements of every current component. Maintain obvious separation between page heading, section heading, tool title, body copy, and control label. Use size and weight before color to establish priority.

Keep paragraph line-height generous, tighten display leading modestly, and avoid copying SF Pro tracking mechanically into Plus Jakarta Sans. Avoid excessive uppercase or tracking on everyday controls. Keep useful text visible at browser zoom and avoid fixed-height text containers.

## Layout

Keep the existing centered maximum-width container (1280px), with dashboard and toolbar content aligned. Use the spacing ladder for tight related groups and generous separation between tasks. Begin section spacing at `section` or `spacious`; use `sm` for icon-to-label gaps and `lg` for panel padding.

Whitespace is structural: give more space between sections than between a heading and its description. Preserve enough room around primary actions without turning every tool screen into an oversized hero. Maintain the existing responsive grids and a usable narrow-screen navigation fallback; desktop is the primary operating context.

Do not import the Apple reference's store carousels, five-column footer, photography-led layout, or fixed 44px navigation. Those belong to another product.

## Elevation & Depth

All surfaces are flat. Use no box shadows, text shadows, hover elevation, glows, or shadow-based focus rings. Separate sections with the theme's two tonal panels. Necessary neutral hairlines may define controls and dividers. Focus uses an outline, which remains distinct from elevation.

**The Flat Surface Rule.** No shadow exceptions for cards, navigation, dialogs, buttons, or hover states.

## Shapes

Every CTA, primary or secondary, is fully pill-shaped using `pill`. Navigation links, input fields, panels, and icon-only utility controls are not automatically CTAs; keep their appropriate compact rounding. A tool card remains a container even when it is clickable. Do not make every component pill-shaped or import Apple's 28px card radius as a requirement.

## Components

### Buttons

Primary CTAs use the accent fill with white, weight-600 labels; hover uses the supplied darker shade. Secondary CTAs use neutral tonal fills and matching theme text. Both use the pill radius, comfortable horizontal padding, and a minimum 44px target. Disabled states must be recognizable and genuinely disabled; processing actions retain visible progress and recovery feedback.

### Navigation

Keep the compact document mark and icon-plus-text shortcuts: All Tools, Merge, Split, Compress. Other tools stay available from the dashboard. Use a subtle neutral active background, weight 600, and `aria-current="page"`. Hover strengthens neutral contrast without movement. Separate the theme utility with spacing or a neutral divider. Any logo accent must obey the interaction-only rule; decorative surfaces stay neutral.

### Panels and tool cards

Use neutral tonal backgrounds, readable headings, and practical descriptions. No accent-tinted surfaces or shadows. Interactive cards require clear hover and keyboard focus; decorative content icons use neutral colors.

### Inputs and status

Use neutral surfaces, visible labels, and concise task-specific guidance. Preserve focus outlines and keyboard operation. Status text stays neutral and names the state explicitly; do not reuse the action accent as decorative error or success styling.

### Theme and motion

Apply the same hierarchy, shape, spacing, and interaction rules in light and dark modes. Retain the explicit saved theme preference and the theme toggle's label naming its next action. Use short 160ms color/background transitions, respect reduced motion, and avoid scale, glow, or floating effects.

### Implementation alignment

Documentation does not change application code. Current differences to address in a separate implementation task include the Arial body override; loaded/used 500 and 700 weights; non-pill processing buttons; residual shadow styles; red-tinted brand surfaces and decorative icons; the darker page background outside the requested two-tone dark palette; and focus colors that differ from the specified accent. Preserve existing behavior while bringing these styles into alignment.

Evidence: `static/css/style.css`, `tailwind.config.js`, `templates/base.html`, `templates/index.html`, and `static/js/app.js`. The user-supplied reference is `C:/Users/azmi maulana/Downloads/DESIGN.md`; the user's explicit hybrid rules take precedence over its instructions.

## Do's and Don'ts

### Do

- Use Plus Jakarta Sans with weights 400, 600, and 800 only.
- Reserve red for actions, links, and focus states.
- Make every CTA pill-shaped.
- Separate sections with neutral tonal panels and generous vertical whitespace.
- Verify contrast, keyboard focus, and the same component states in both themes.

### Don't

- Use accent red for body text, decorative content, or structural surfaces.
- Add shadows, glows, hover elevation, or blurred glass.
- Import Apple's SF Pro fonts, blue accent, marketing layouts, or shadow exceptions.
- Compress section spacing merely to fit more content into one viewport.
- Treat this document as evidence that the current UI already conforms.
