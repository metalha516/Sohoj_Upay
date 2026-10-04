# Sohoj UI/UX Overhaul: Three.js 3D & 21st.dev Fintech Architecture Implementation Plan

**Goal:** Transform Sohoj from a generic template into an elite, tactile, and addictive fintech platform featuring an interactive 3D Gold Taka Coin, GPU particle wave, 21st.dev components (Spotlight cards, BorderBeam, Rolling Odometer, Magnetic buttons, Apple Card radial dial), and bespoke Plus Jakarta Sans + JetBrains Mono typography in the Upay MFS palette.

**Architecture:** A progressive hybrid client-server Next.js 14 architecture. Heavy 3D WebGL (Three.js) is isolated into dynamically loaded leaf canvas components with deterministic GPU disposal and mobile gyro fallback. Framer Motion powers tactile micro-interactions (spring physics, cursor attraction, and rolling odometers), wrapped in machined double-bezel (Doppelrand) surfaces with an 80/15/5 obsidian-to-gold lighting discipline.

**Tech Stack:** Next.js 14 (App Router), React 18, Three.js (modular tree-shaken imports), Framer Motion (`framer-motion`), Tailwind CSS, Lucide React, Plus Jakarta Sans (`next/font/google`), JetBrains Mono (`next/font/google`).

**Spec:** `docs/specs/2026-10-04-ui-ux-threejs-21stdev-spec.md`

## Global Constraints

- Primary Display Font: `Plus_Jakarta_Sans` (weights 300 to 800) loaded via `next/font/google`.
- Monospace Metric Font: `JetBrains_Mono` with `tabular-nums` for all financial currency amounts and percentages.
- Palette Ratio: Strictly 80% Obsidian Void (`#061325`), 15% Architectural Navy Glass (`#0A1C3C`), 5% Luminous Upay Gold (`#FFC709`).
- Contrast Standard: Upay Yellow CTAs MUST always use Navy-950 (`#061325`) text for a 12.8:1 WCAG AAA rating. White-on-yellow text is strictly banned.
- Three.js Optimization: Modular imports only (no `* as THREE`), clamped `devicePixelRatio <= 1.75`, dynamic import with `ssr: false`, and full WebGL memory disposal on unmount.
- Zero Em-Dash / En-Dash Rule: All text copy must use hyphens, colons, or restructured prose.
- Bengali Taka Currency Rule: Use the Deconstructed Currency Molecule (`CurrencyAmount.tsx`) to prevent baseline jumping.

## Review Focus

- WebGL context leak during route navigation or React Fast Refresh in development.
- Performance and framerate stability on low-tier mobile devices (respect `prefers-reduced-motion` and disable continuous WebGL loops).
- Mobile responsive collapse: all 3D canvases and bento grids must degrade gracefully to single-column without horizontal scroll.
- Accessibility: screen readers must receive semantic currency values rather than raw canvas or disjointed odometer numbers.
- Bundle size: Three.js and Framer Motion must not bloat the initial first-load JS beyond acceptable thresholds.

---

### Task 1: Foundation Setup — Dependencies, Fonts & Tailored Design Tokens

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Produces: `three` and `framer-motion` dependencies, `--font-sans` (Plus Jakarta Sans), `--font-mono` (JetBrains Mono), extended letter-spacing tokens, keyframe animations for border-beam.

- [ ] **Step 1: Install `three`, `@types/three`, and `framer-motion`**
Run: `npm install three framer-motion && npm install -D @types/three` in `frontend/`.

- [ ] **Step 2: Update `frontend/app/layout.tsx` with Plus Jakarta Sans & JetBrains Mono**
Configure `Plus_Jakarta_Sans` (`variable: "--font-sans"`) and `JetBrains_Mono` (`variable: "--font-mono"`). Apply class names to `<html>` and wrap body in `min-h-screen bg-navy-950 text-slate-100 font-sans`.

- [ ] **Step 3: Update `frontend/tailwind.config.js`**
Extend fontFamily to use `["var(--font-sans)"]` and `["var(--font-mono)"]`. Add tracking scales: `tighter: "-0.035em"`, `tight: "-0.02em"`, `widest: "0.20em"`. Add border-beam keyframes.

- [ ] **Step 4: Update `frontend/app/globals.css`**
Add `@keyframes border-beam { 100% { offset-distance: 100%; } }`. Add double-bezel and hardware lighting utility classes.

- [ ] **Step 5: Verify build passes**
Run: `npx next build` in `frontend/`. Expected: compiled successfully.

---

### Task 2: Core Micro-Interaction Primitives (21st.dev Component Library)

**Files:**
- Create: `frontend/components/ui/CurrencyAmount.tsx`
- Create: `frontend/components/ui/SpotlightCard.tsx`
- Create: `frontend/components/ui/BorderBeam.tsx`
- Create: `frontend/components/ui/RollingOdometer.tsx`
- Create: `frontend/components/ui/MagneticButton.tsx`
- Create: `frontend/components/ui/PaymentDial.tsx`

**Interfaces:**
- Consumes: `framer-motion`, Tailwind design tokens.
- Produces:
  - `CurrencyAmount`: `<CurrencyAmount amount={number} size="sm"|"md"|"lg"|"hero" />`
  - `SpotlightCard`: `<SpotlightCard spotlightColor="...">...</SpotlightCard>`
  - `BorderBeam`: `<BorderBeam size={number} duration={number} />`
  - `RollingOdometer`: `<RollingOdometer value={number} prefix="৳" />`
  - `MagneticButton`: `<MagneticButton icon={<ArrowRight />}>Text</MagneticButton>`
  - `PaymentDial`: `<PaymentDial totalDue={number} onAmountChange={fn} />`

- [ ] **Step 1: Build `CurrencyAmount.tsx`**
Implement the deconstructed currency molecule separating `৳` into a sans-serif wrapper while formatting numbers in tabular JetBrains Mono.

- [ ] **Step 2: Build `SpotlightCard.tsx`**
Implement cursor-tracking radial spotlight glow (`rgba(255, 199, 9, 0.14)`) with inner glass enclosure and smooth opacity transition on hover.

- [ ] **Step 3: Build `BorderBeam.tsx`**
Implement continuous perimeter laser beam using CSS `offset-path: rect(...)` and radial gradient in Upay Yellow to Navy transition.

- [ ] **Step 4: Build `RollingOdometer.tsx`**
Implement vertical digit rolling columns with Framer Motion `useSpring({ stiffness: 120, damping: 18 })` and tabular monospace digits.

- [ ] **Step 5: Build `MagneticButton.tsx`**
Implement magnetic cursor attraction using `useMotionValue` and `useSpring`, with 1.6x multiplier on the trailing icon for kinetic depth.

- [ ] **Step 6: Build `PaymentDial.tsx`**
Implement the Apple Card inspired tactile SVG circular dial with drag interaction, real-time interest/savings calculation, and dynamic color progression.

- [ ] **Step 7: Verify unit tests**
Run: `npm test -- --run` in `frontend/`. Expected: All existing tests pass.

---

### Task 3: Three.js Interactive 3D Canvas Subsystem

**Files:**
- Create: `frontend/components/canvas/coinTexture.ts`
- Create: `frontend/components/canvas/GoldTakaCoinCanvas.tsx`
- Create: `frontend/components/canvas/ParticleWaveCanvas.tsx`
- Create: `frontend/components/canvas/ParallaxGlassCard.tsx`
- Create: `frontend/components/canvas/utils/disposeThreeScene.ts`

**Interfaces:**
- Consumes: `three`, browser WebGL, PointerEvent, DeviceOrientationEvent.
- Produces:
  - `GoldTakaCoinCanvas`: Dynamic interactive 3D Gold Taka token with drag-to-spin and specular highlights.
  - `ParticleWaveCanvas`: GPU vertex-shader wave simulation reacting to cursor repulsion.
  - `ParallaxGlassCard`: 3D tilt card with mobile gyroscope and holographic specular sheen.

- [ ] **Step 1: Implement `coinTexture.ts`**
Create procedural offscreen 2D canvas generator producing high-resolution normal/bump maps with Bengali Taka `৳`, milled rim, and Upay branding.

- [ ] **Step 2: Implement `disposeThreeScene.ts`**
Create bulletproof WebGL disposal helper that cleans all geometries, materials, textures, renderer context, and event listeners to prevent memory leaks.

- [ ] **Step 3: Implement `GoldTakaCoinCanvas.tsx`**
Create the 3D Gold Taka cylinder with `MeshPhysicalMaterial` (`metalness: 0.95`, `roughness: 0.22`, `clearcoat: 0.35`), 3-point Upay lighting, mouse hover tilt lerp, and momentum friction decay.

- [ ] **Step 4: Implement `ParticleWaveCanvas.tsx`**
Create GLSL vertex & fragment shader particle wave field with mouse plane intersection and Upay Yellow crest coloring.

- [ ] **Step 5: Implement `ParallaxGlassCard.tsx`**
Create the interactive 3D card supporting both desktop cursor parallax and mobile device gyroscope (`DeviceOrientationEvent`) with EMV gold chip and holographic glare.

- [ ] **Step 6: Verify Three.js canvases compile cleanly**
Run: `npx next build` in `frontend/`. Verify no webpack or SSR errors.

---

### Task 4: Landing Page Overhaul (`frontend/app/page.tsx`)

**Files:**
- Modify: `frontend/app/page.tsx`

**Interfaces:**
- Consumes: Dynamic Three.js canvases (`GoldTakaCoinCanvas`, `ParticleWaveCanvas`), `SpotlightCard`, `BorderBeam`, `RollingOdometer`, `MagneticButton`, `CurrencyAmount`.

- [ ] **Step 1: Hero Section Transformation**
  - Background: Integrate `ParticleWaveCanvas` with subtle additive blending behind the hero.
  - Right Column / Hero Centerpiece: Add dynamic `GoldTakaCoinCanvas` (3D coin spinning and floating).
  - Headline: Plus Jakarta Sans display typography with `-0.035em` tracking.
  - CTAs: Replace standard buttons with `MagneticButton` featuring trailing arrow parallax.

- [ ] **Step 2: Interactive Engine Playground Overhaul**
  - Integrate `RollingOdometer` into the maturity value display so projected wealth rolls smoothly as sliders are adjusted.
  - Wrap the simulator container in a double-bezel `SpotlightCard` with an active `BorderBeam`.
  - Add instant tariff comparison scrubber with animated savings callouts.

- [ ] **Step 3: Bento Grid Architecture for Core Pillars**
  - Redesign the 4 pillars into a high-variance Bento Grid with interactive micro-widgets inside each cell (live forecast graph, AI coach snippet, Rule of 72 doubling gauge, anomaly velocity tracker).

- [ ] **Step 4: Persona Showcase with 3D Holographic Parallax Card**
  - Display the `ParallaxGlassCard` alongside Sumaiya, Roksana, and Kamrul's profiles, updating card tier and balance dynamically as personas are switched.

- [ ] **Step 5: Clean Up Text Clutter & Verify Compliance**
  - Check for zero em-dashes (`—`), concise copy (subtitles <= 20 words), and verified 12.8:1 contrast on all buttons.

- [ ] **Step 6: Visual & Build Verification**
  - Run `npx next build` and capture screenshot in Chrome DevTools to verify visual appeal.

---

### Task 5: Dashboard & Inner Views Elevation

**Files:**
- Modify: `frontend/components/dashboard/BalanceCard.tsx`
- Modify: `frontend/components/dashboard/IncomeCard.tsx`
- Modify: `frontend/components/dashboard/ExpenseCard.tsx`
- Modify: `frontend/components/dashboard/SavingsCard.tsx`
- Modify: `frontend/app/simulator/page.tsx`
- Modify: `frontend/components/simulator/SimulatorView.tsx`

**Interfaces:**
- Consumes: `SpotlightCard`, `BorderBeam`, `RollingOdometer`, `PaymentDial`, `CurrencyAmount`.

- [ ] **Step 1: BalanceCard Upgrade**
  - Wrap BalanceCard in a double-bezel hardware shell with `BorderBeam` on the perimeter.
  - Replace static balance with `RollingOdometer` and `CurrencyAmount`.
  - Add quick-action magnetic buttons for "Record Cash-Out" and "Add Transaction".

- [ ] **Step 2: Income, Expense & Savings Cards**
  - Wrap in `SpotlightCard` with golden cursor auras.
  - Format all values with `CurrencyAmount` (tabular JetBrains Mono).

- [ ] **Step 3: SimulatorView Upgrade**
  - Integrate the `PaymentDial` / tactile circular scrubber for horizon and DPS deposit amounts.
  - Display real-time rolling numbers for compound maturity values.

- [ ] **Step 4: Run test suite & visual audit**
  - Run: `npm test -- --run` (all tests pass).
  - Open Chrome DevTools and verify desktop and mobile viewports.

---

### Task 6: Final Review, Polish & Git Push

**Files:**
- All modified frontend files.

- [ ] **Step 1: Full production build check**
Run: `npx next build` to guarantee 100% static generation without errors.

- [ ] **Step 2: Vitest test suite pass**
Run: `npm test -- --run` to ensure all 22+ tests pass cleanly.

- [ ] **Step 3: Git commit & push**
Run: `git add -A && git commit -m "feat(ui): 3D Three.js canvas, 21st.dev components, and Plus Jakarta Sans overhaul" && git push origin nayem`.
