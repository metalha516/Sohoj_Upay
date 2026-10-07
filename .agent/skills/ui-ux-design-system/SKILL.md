---
name: ui-ux-design-system
description: >-
  Provides comprehensive guidelines and component recipes for building world-class SaaS and fintech user interfaces inspired by 21st.dev, Linear, and Stripe, specifically tailored to Upay MFS brand standards (Deep Navy Blue #0A1C3C, Vibrant Upay Yellow #FFC709, Crisp White, Obsidian Dark #070D18). Use this skill when designing, styling, reviewing, or refactoring web pages, components, dashboards, cards, buttons, or design tokens.
---

# UI/UX Design System: Fintech SaaS & Upay MFS

This skill provides an authoritative reference and actionable design recipes for creating clean, minimalistic, informative, and SaaS-grade fintech interfaces aligned with the **upay MFS** identity.

---

## 1. Brand Tokens & Color Palette

The design system establishes a high-contrast hierarchy that balances serious institutional banking trust (Deep Navy) with playful, accessible micro-rewards (Vibrant Upay Yellow).

### Core Palette

| Role | Token | Hex Code | Tailwind Utility | Visual Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Canvas Dark** | `navy-950` | `#061325` | `bg-navy-950` | Landing page canvas & dark mode backdrops |
| **Brand Primary Navy** | `navy-900` | `#0A1C3C` | `bg-navy-900`, `text-navy-900` | Headers, balance card, primary text, dark buttons |
| **Card Surface Navy** | `navy-850` | `#0D234C` | `bg-navy-850` | Active dark card containers |
| **Border Dark Navy** | `navy-800` | `#0F2B5C` | `border-navy-800` | Borders for dark cards and pill controls |
| **Brand Accent Yellow**| `upay-500` | `#FFC709` | `bg-upay-yellow`, `text-upay-yellow` | Primary CTAs, active pills, badges, glow lines |
| **Hover Yellow** | `upay-400` | `#FFD338` | `hover:bg-upay-400` | Interactive hover feedback for yellow elements |
| **Active Press Yellow**| `upay-600` | `#E5B100` | `active:bg-upay-600` | Active button press state |
| **Obsidian Dark** | `onyx` | `#070D18` | `bg-onyx` | Deep background contrast |
| **Canvas Light** | `slate-50` | `#F8FAFC` | `bg-slate-50` | In-app dashboard view canvas |
| **Card Surface Light** | `white` | `#FFFFFF` | `bg-white` | In-app dashboard card containers |
| **Border Subtle Light**| `slate-200/80` | `#E2E8F0` | `border-slate-200/80` | Clean structural card dividers |

### Tailwind Extension (`tailwind.config.js`)
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#061325',
          900: '#0A1C3C',
          850: '#0D234C',
          800: '#0F2B5C',
          700: '#153A7A',
          600: '#1E4D9F',
        },
        upay: {
          500: '#FFC709',
          400: '#FFD338',
          600: '#E5B100',
          yellow: '#FFC709',
          accent: '#FFC709',
        },
        onyx: '#070D18',
        mfs: {
          upay: '#FFC709',
          bkash: '#E2136E',
          nagad: '#F7941D',
          rocket: '#8C3494',
        },
      },
      boxShadow: {
        'upay-glow': '0 0 25px -5px rgba(255, 199, 9, 0.35)',
        'navy-card': '0 10px 30px -10px rgba(10, 28, 60, 0.12)',
      },
    },
  },
};
```

---

## 2. Atmospheric Depth & Glassmorphism

To elevate an interface from generic corporate to premier fintech SaaS:

### Ambient Mesh Gradient
```css
/* Add to globals.css */
.mesh-gradient {
  background-image:
    radial-gradient(at 0% 0%, rgba(255, 199, 9, 0.08) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(15, 43, 92, 0.4) 0px, transparent 50%),
    radial-gradient(at 50% 100%, rgba(10, 28, 60, 0.5) 0px, transparent 50%);
}

.glass-card {
  background: rgba(10, 28, 60, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 199, 9, 0.18);
}
```

---

## 3. Core Component Recipes

### A. Live Telemetry Badge (Hero Section)
```tsx
<div className="inline-flex items-center gap-2 rounded-full border border-upay-yellow/30 bg-navy-900/80 px-4 py-1.5 shadow-sm backdrop-blur-md">
  <span className="h-2 w-2 rounded-full bg-upay-yellow animate-pulse" />
  <span className="text-xs font-bold text-upay-yellow">
    Bangladesh&apos;s First AI Financial Copilot
  </span>
  <span className="text-slate-500">|</span>
  <span className="text-xs font-semibold text-slate-300">
    Upay MFS Intelligence
  </span>
</div>
```

### B. High-Converting CTA Buttons
* **Primary (Upay Yellow)**:
  ```tsx
  <button className="inline-flex items-center gap-2 rounded-xl bg-upay-yellow px-6 py-3 text-sm font-extrabold text-navy-950 shadow-md shadow-upay-yellow/20 hover:bg-upay-400 active:bg-upay-600 transition-all">
    Launch Dashboard <ArrowRight className="h-4 w-4" />
  </button>
  ```
* **Secondary (Navy Dark / Border Ghost)**:
  ```tsx
  <button className="inline-flex items-center gap-2 rounded-xl border border-navy-700 bg-navy-900/80 px-6 py-3 text-sm font-bold text-white hover:border-upay-yellow/40 hover:bg-navy-800 transition-all">
    Try Live Simulator
  </button>
  ```

### C. MFS Provider Pill Badges
```tsx
{provider === 'upay' ? (
  <span className="inline-flex items-center rounded-full bg-upay-yellow/20 px-2.5 py-0.5 text-[10px] font-black text-navy-950 border border-upay-yellow/50">
    Upay
  </span>
) : (
  <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-semibold uppercase text-slate-600">
    {provider}
  </span>
)}
```

---

## 4. UI/UX Rules of Thumb
1. **Never use generic green/emerald**: Use Upay Navy `#0A1C3C` for primary balance/inflow indicators, and Upay Yellow `#FFC709` for savings and positive badges.
2. **Text Hierarchy**: Large numerals (`text-2xl` to `text-4xl`) must always use `font-black` or `font-extrabold`. Labels must use uppercase `text-[10px]` or `text-xs font-bold tracking-wider text-slate-500`.
3. **Responsive Padding**: Always wrap dashboards in `px-4 sm:px-6 lg:px-8` and use `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6`.
