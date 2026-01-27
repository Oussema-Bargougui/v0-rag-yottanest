# YOTTANEST — AML Compliance Intelligence Platform

## Frontend Architecture Specification v1.0.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Design System & Tokens](#3-design-system--tokens)
4. [Application Architecture](#4-application-architecture)
5. [Layout System](#5-layout-system)
6. [Component Specifications](#6-component-specifications)
7. [Dashboard Modules](#7-dashboard-modules)
8. [Data Visualization Standards](#8-data-visualization-standards)
9. [State Management](#9-state-management)
10. [API Integration Layer](#10-api-integration-layer)
11. [Real-Time Systems](#11-real-time-systems)
12. [Security Implementation](#12-security-implementation)
13. [Accessibility Standards](#13-accessibility-standards)
14. [Performance Optimization](#14-performance-optimization)
15. [File Structure](#15-file-structure)
16. [Development Guidelines](#16-development-guidelines)

---

## 1. Project Overview

### 1.1 Product Description

**Yottanest** is an enterprise-grade Anti-Money Laundering (AML) compliance intelligence platform designed for banking institutions. The platform integrates two core engines:

- **NetReport Engine**: Automated data scraping, business viability assessment, and regulatory report generation
- **Smart Docs**: Unstructured document processing utilizing OCR and NLP for invoice, contract, and KYC document analysis

### 1.2 Target Users

| User Role | Access Level | Primary Functions |
|-----------|--------------|-------------------|
| Compliance Analyst | Standard | Case review, document processing, alert triage |
| Senior Compliance Officer | Elevated | Report approval, risk threshold configuration |
| Compliance Manager | Administrative | Team oversight, audit trail review, escalation handling |
| System Administrator | Full | User management, system configuration, API access |

### 1.3 Core Objectives

- Reduce manual compliance workload by 70%
- Provide real-time risk visibility across all monitored entities
- Automate SAR (Suspicious Activity Report) and Risk Memo generation
- Ensure 100% regulatory compliance with GDPR, AML directives, and banking regulations
- Maintain complete data sovereignty through on-premise deployment

---

## 2. Technology Stack

### 2.1 Core Framework

```
Framework:          Next.js 14.x (App Router)
Runtime:            Node.js 20.x LTS
Language:           TypeScript 5.x (Strict Mode)
Package Manager:    pnpm 8.x
```

### 2.2 UI & Styling

```
Component Library:  shadcn/ui (Radix UI primitives)
Styling:            Tailwind CSS 3.4.x
Icons:              Lucide React
Animation:          Framer Motion 10.x
Charts:             Recharts 2.x / Tremor
Data Tables:        TanStack Table v8
Forms:              React Hook Form + Zod validation
```

### 2.3 State & Data

```
Client State:       Zustand 4.x
Server State:       TanStack Query v5
Real-Time:          Socket.io Client / WebSocket API
Date Handling:      date-fns 3.x
```

### 2.4 Development Tools

```
Linting:            ESLint 8.x + Prettier
Testing:            Vitest + React Testing Library + Playwright
Documentation:      Storybook 7.x
API Mocking:        MSW (Mock Service Worker)
```

---

## 3. Design System & Tokens

### 3.1 Color Palette

#### Primary Colors (Brand Identity)

```css
--color-primary-50:   #EBF4FF;   /* Lightest tint */
--color-primary-100:  #C3DAFE;
--color-primary-200:  #A3BFFA;
--color-primary-300:  #7F9CF5;
--color-primary-400:  #667EEA;
--color-primary-500:  #1A365D;   /* Primary brand - Deep Navy */
--color-primary-600:  #152A4A;
--color-primary-700:  #102038;
--color-primary-800:  #0B1526;
--color-primary-900:  #050A13;   /* Darkest shade */
```

#### Secondary Colors (Interactive Elements)

```css
--color-secondary-50:  #EBF8FF;
--color-secondary-100: #BEE3F8;
--color-secondary-200: #90CDF4;
--color-secondary-300: #63B3ED;
--color-secondary-400: #4299E1;
--color-secondary-500: #2C5282;  /* Corporate Blue */
--color-secondary-600: #2A4365;
--color-secondary-700: #1A365D;
--color-secondary-800: #153E75;
--color-secondary-900: #1A202C;
```

#### Semantic Colors (Status Indicators)

```css
/* Risk Levels */
--color-risk-critical:   #DC2626;  /* Red-600 - Critical/High Risk */
--color-risk-high:       #EA580C;  /* Orange-600 - Elevated Risk */
--color-risk-medium:     #CA8A04;  /* Yellow-600 - Medium Risk */
--color-risk-low:        #16A34A;  /* Green-600 - Low Risk */
--color-risk-clear:      #0D9488;  /* Teal-600 - Cleared/No Risk */

/* System States */
--color-success:         #059669;  /* Emerald-600 */
--color-warning:         #D97706;  /* Amber-600 */
--color-error:           #DC2626;  /* Red-600 */
--color-info:            #0284C7;  /* Sky-600 */

/* Background States */
--color-success-bg:      #ECFDF5;
--color-warning-bg:      #FFFBEB;
--color-error-bg:        #FEF2F2;
--color-info-bg:         #F0F9FF;
```

#### Neutral Colors (UI Foundation)

```css
--color-neutral-0:    #FFFFFF;   /* Pure White */
--color-neutral-50:   #F9FAFB;   /* Background Light */
--color-neutral-100:  #F3F4F6;   /* Card Background */
--color-neutral-200:  #E5E7EB;   /* Border Light */
--color-neutral-300:  #D1D5DB;   /* Border Default */
--color-neutral-400:  #9CA3AF;   /* Placeholder Text */
--color-neutral-500:  #6B7280;   /* Secondary Text */
--color-neutral-600:  #4B5563;   /* Body Text */
--color-neutral-700:  #374151;   /* Heading Text */
--color-neutral-800:  #1F2937;   /* Primary Text */
--color-neutral-900:  #111827;   /* Emphasis Text */
--color-neutral-950:  #030712;   /* Pure Black */
```

### 3.2 Typography System

#### Font Stack

```css
--font-family-display:  'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-family-body:     'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-family-mono:     'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

#### Type Scale

```css
/* Display & Headlines */
--text-display-2xl:     4.5rem;    /* 72px - Hero headlines */
--text-display-xl:      3.75rem;   /* 60px - Page titles */
--text-display-lg:      3rem;      /* 48px - Section headers */
--text-display-md:      2.25rem;   /* 36px - Card titles */
--text-display-sm:      1.875rem;  /* 30px - Subsection headers */

/* Headings */
--text-heading-xl:      1.5rem;    /* 24px - H1 */
--text-heading-lg:      1.25rem;   /* 20px - H2 */
--text-heading-md:      1.125rem;  /* 18px - H3 */
--text-heading-sm:      1rem;      /* 16px - H4 */
--text-heading-xs:      0.875rem;  /* 14px - H5 */

/* Body Text */
--text-body-lg:         1.125rem;  /* 18px */
--text-body-md:         1rem;      /* 16px - Default */
--text-body-sm:         0.875rem;  /* 14px */
--text-body-xs:         0.75rem;   /* 12px */

/* Utility Text */
--text-caption:         0.75rem;   /* 12px - Labels, captions */
--text-overline:        0.625rem;  /* 10px - Overlines, badges */
```

#### Font Weights

```css
--font-weight-regular:   400;
--font-weight-medium:    500;
--font-weight-semibold:  600;
--font-weight-bold:      700;
```

#### Line Heights

```css
--line-height-none:      1;
--line-height-tight:     1.25;
--line-height-snug:      1.375;
--line-height-normal:    1.5;
--line-height-relaxed:   1.625;
--line-height-loose:     2;
```

### 3.3 Spacing System

```css
/* Base unit: 4px */
--space-0:    0;
--space-px:   1px;
--space-0.5:  0.125rem;   /* 2px */
--space-1:    0.25rem;    /* 4px */
--space-1.5:  0.375rem;   /* 6px */
--space-2:    0.5rem;     /* 8px */
--space-2.5:  0.625rem;   /* 10px */
--space-3:    0.75rem;    /* 12px */
--space-3.5:  0.875rem;   /* 14px */
--space-4:    1rem;       /* 16px */
--space-5:    1.25rem;    /* 20px */
--space-6:    1.5rem;     /* 24px */
--space-7:    1.75rem;    /* 28px */
--space-8:    2rem;       /* 32px */
--space-9:    2.25rem;    /* 36px */
--space-10:   2.5rem;     /* 40px */
--space-11:   2.75rem;    /* 44px */
--space-12:   3rem;       /* 48px */
--space-14:   3.5rem;     /* 56px */
--space-16:   4rem;       /* 64px */
--space-20:   5rem;       /* 80px */
--space-24:   6rem;       /* 96px */
--space-28:   7rem;       /* 112px */
--space-32:   8rem;       /* 128px */
```

### 3.4 Border Radius

```css
--radius-none:    0;
--radius-sm:      0.125rem;   /* 2px */
--radius-default: 0.25rem;    /* 4px */
--radius-md:      0.375rem;   /* 6px */
--radius-lg:      0.5rem;     /* 8px */
--radius-xl:      0.75rem;    /* 12px */
--radius-2xl:     1rem;       /* 16px */
--radius-3xl:     1.5rem;     /* 24px */
--radius-full:    9999px;     /* Pill shape */
```

### 3.5 Shadow System

```css
/* Elevation Levels */
--shadow-xs:      0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-sm:      0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
--shadow-md:      0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg:      0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl:      0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
--shadow-2xl:     0 25px 50px -12px rgb(0 0 0 / 0.25);
--shadow-inner:   inset 0 2px 4px 0 rgb(0 0 0 / 0.05);

/* Colored Shadows (for cards) */
--shadow-primary: 0 4px 14px 0 rgb(26 54 93 / 0.15);
--shadow-danger:  0 4px 14px 0 rgb(220 38 38 / 0.15);
--shadow-success: 0 4px 14px 0 rgb(5 150 105 / 0.15);
```

### 3.6 Z-Index Scale

```css
--z-base:       0;
--z-dropdown:   1000;
--z-sticky:     1100;
--z-fixed:      1200;
--z-backdrop:   1300;
--z-modal:      1400;
--z-popover:    1500;
--z-tooltip:    1600;
--z-toast:      1700;
```

### 3.7 Transition & Animation

```css
/* Duration */
--duration-instant:   0ms;
--duration-fast:      100ms;
--duration-normal:    200ms;
--duration-slow:      300ms;
--duration-slower:    500ms;

/* Easing */
--ease-linear:        linear;
--ease-in:            cubic-bezier(0.4, 0, 1, 1);
--ease-out:           cubic-bezier(0, 0, 0.2, 1);
--ease-in-out:        cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce:        cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### 3.8 Breakpoints

```css
--breakpoint-sm:   640px;    /* Mobile landscape */
--breakpoint-md:   768px;    /* Tablet portrait */
--breakpoint-lg:   1024px;   /* Tablet landscape / Small desktop */
--breakpoint-xl:   1280px;   /* Desktop */
--breakpoint-2xl:  1536px;   /* Large desktop */
--breakpoint-3xl:  1920px;   /* Ultra-wide */
```

---

## 4. Application Architecture

### 4.1 Routing Structure

```
/                                    → Redirect to /dashboard
/dashboard                           → Main dashboard overview
/dashboard/risk-overview             → Risk analytics center
/dashboard/alerts                    → Real-time alert management
/dashboard/transactions              → Transaction monitoring
/dashboard/entities                  → Entity management
/dashboard/entities/[id]             → Entity detail view
/dashboard/entities/[id]/timeline    → Entity activity timeline
/dashboard/reports                   → Report management
/dashboard/reports/new               → Report generation wizard
/dashboard/reports/[id]              → Report detail view
/dashboard/documents                 → Document processing (Smart Docs)
/dashboard/documents/upload          → Document upload interface
/dashboard/documents/[id]            → Document analysis view
/dashboard/tasks                     → Task management
/dashboard/cases                     → Case management
/dashboard/cases/[id]                → Case detail & investigation
/settings                            → User settings
/settings/profile                    → Profile management
/settings/notifications              → Notification preferences
/settings/security                   → Security settings
/admin                               → Admin panel (elevated access)
/admin/users                         → User management
/admin/roles                         → Role & permission management
/admin/audit-log                     → System audit trail
/admin/system                        → System configuration
```

### 4.2 Layout Hierarchy

```
RootLayout (app/layout.tsx)
├── Providers (Theme, Auth, Query, Toast)
│   └── AuthGuard
│       └── DashboardLayout (app/dashboard/layout.tsx)
│           ├── TopNavbar (64px height)
│           ├── Sidebar (280px width, collapsible to 72px)
│           └── MainContent
│               ├── PageHeader
│               ├── ContentArea
│               └── Optional: RightPanel (320px width)
```

---

## 5. Layout System

### 5.1 Top Navbar Specification

#### Dimensions

```
Height:               64px
Background:           var(--color-neutral-0)
Border Bottom:        1px solid var(--color-neutral-200)
Shadow:               var(--shadow-sm)
Z-Index:              var(--z-sticky)
Position:             Fixed, top: 0
Padding Horizontal:   24px
```

#### Structure (Left to Right)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [≡] │ YOTTANEST │                    [🔍 Search...]                │ 🔔 │ 👤 │
│ 24px│   Logo    │                    Global Search                  │Bell│User│
└─────────────────────────────────────────────────────────────────────────────┘
```

##### Left Section (Gap: 16px)

| Element | Specification |
|---------|---------------|
| Sidebar Toggle | 40×40px, icon 20×20px, hover: bg-neutral-100, radius: 8px |
| Logo | SVG, height: 32px, width: auto, clickable → /dashboard |
| Breadcrumbs | font-size: 14px, color: neutral-500, separator: "/" |

##### Center Section

| Element | Specification |
|---------|---------------|
| Global Search | Width: 480px max, height: 40px, bg: neutral-100, radius: 8px |
| Search Icon | 16×16px, color: neutral-400, left padding: 12px |
| Placeholder | "Search entities, transactions, reports..." color: neutral-400 |
| Keyboard Shortcut | "⌘K" badge, right side, bg: neutral-200, font: mono, 10px |

##### Right Section (Gap: 8px)

| Element | Specification |
|---------|---------------|
| Notification Bell | 40×40px, icon: 20×20px, badge: red circle 8×8px if unread |
| User Avatar | 36×36px, radius: full, border: 2px solid neutral-200 |
| Dropdown Arrow | 12×12px, color: neutral-400 |

### 5.2 Sidebar Navigation Specification

#### Dimensions

```
Width (Expanded):     280px
Width (Collapsed):    72px
Background:           var(--color-primary-500)
Transition:           width 300ms var(--ease-in-out)
Position:             Fixed, left: 0, top: 64px
Height:               calc(100vh - 64px)
Z-Index:              var(--z-fixed)
Overflow Y:           Auto (custom scrollbar)
Padding:              16px 12px
```

#### Scrollbar Styling

```css
/* Custom scrollbar for sidebar */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
```

#### Navigation Items

##### Section Header

```
Font Size:            11px
Font Weight:          600
Text Transform:       Uppercase
Letter Spacing:       0.05em
Color:                rgba(255, 255, 255, 0.5)
Margin Bottom:        8px
Margin Top:           24px (except first)
Padding Left:         12px
```

##### Navigation Item (Default State)

```
Height:               44px
Padding:              0 12px
Border Radius:        8px
Display:              Flex, align-items: center
Gap:                  12px
Color:                rgba(255, 255, 255, 0.7)
Font Size:            14px
Font Weight:          500
Transition:           all 150ms ease
```

##### Navigation Item (Hover State)

```
Background:           rgba(255, 255, 255, 0.1)
Color:                rgba(255, 255, 255, 0.9)
```

##### Navigation Item (Active State)

```
Background:           rgba(255, 255, 255, 0.15)
Color:                #FFFFFF
Border Left:          3px solid var(--color-secondary-400)
```

##### Navigation Icon

```
Size:                 20×20px
Stroke Width:         1.5px
Flex Shrink:          0
```

##### Badge (Notification Count)

```
Min Width:            20px
Height:               20px
Padding:              0 6px
Border Radius:        10px
Background:           var(--color-danger)
Color:                #FFFFFF
Font Size:            11px
Font Weight:          600
```

#### Navigation Structure

```
┌────────────────────────────────────┐
│  [Logo Area - when collapsed]      │
├────────────────────────────────────┤
│  MAIN                              │
│  ├─ 📊 Dashboard                   │
│  ├─ ⚠️ Alerts              [12]    │
│  ├─ 💹 Transactions                │
│  └─ 🏢 Entities                    │
├────────────────────────────────────┤
│  INVESTIGATION                     │
│  ├─ 📁 Cases               [3]     │
│  ├─ ✅ Tasks               [8]     │
│  └─ 📄 Reports                     │
├────────────────────────────────────┤
│  DOCUMENTS                         │
│  ├─ 📤 Upload                      │
│  ├─ 📋 Processing          [5]     │
│  └─ ✓ Completed                    │
├────────────────────────────────────┤
│  ANALYTICS                         │
│  ├─ 📈 Risk Overview               │
│  ├─ 📊 Trends                      │
│  └─ 🗺️ Geographic                  │
├────────────────────────────────────┤
│                                    │
│  [Spacer - flex-grow: 1]           │
│                                    │
├────────────────────────────────────┤
│  ⚙️ Settings                       │
│  ❓ Help & Support                 │
├────────────────────────────────────┤
│  ┌──────────────────────────────┐  │
│  │ 👤 John Smith                │  │
│  │    Compliance Analyst        │  │
│  │    ▾ Dropdown                │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

### 5.3 Main Content Area

#### Dimensions

```
Margin Left:          280px (expanded) / 72px (collapsed)
Margin Top:           64px
Min Height:           calc(100vh - 64px)
Background:           var(--color-neutral-50)
Transition:           margin-left 300ms var(--ease-in-out)
Padding:              24px
```

#### Page Header

```
Height:               Auto (content-based)
Margin Bottom:        24px
Display:              Flex, justify-content: space-between, align-items: flex-start
```

##### Page Title Section

```
┌─────────────────────────────────────────────────────────────────┐
│  Dashboard Overview                              [+ New Report] │
│  Monitor real-time compliance metrics            [↓ Export]     │
│  Last updated: 2 minutes ago                                    │
└─────────────────────────────────────────────────────────────────┘
```

| Element | Specification |
|---------|---------------|
| Page Title | font-size: 24px, font-weight: 700, color: neutral-900 |
| Description | font-size: 14px, color: neutral-500, margin-top: 4px |
| Last Updated | font-size: 12px, color: neutral-400, margin-top: 8px |
| Action Buttons | Gap: 12px between buttons |

### 5.4 Grid System

```css
/* Content Grid */
.content-grid {
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(12, 1fr);
}

/* Column Spans */
.col-span-3  { grid-column: span 3; }   /* 25% - Quarter */
.col-span-4  { grid-column: span 4; }   /* 33% - Third */
.col-span-6  { grid-column: span 6; }   /* 50% - Half */
.col-span-8  { grid-column: span 8; }   /* 66% - Two-thirds */
.col-span-9  { grid-column: span 9; }   /* 75% - Three-quarters */
.col-span-12 { grid-column: span 12; }  /* 100% - Full */

/* Responsive Adjustments */
@media (max-width: 1280px) {
  .col-span-3 { grid-column: span 6; }
  .col-span-4 { grid-column: span 6; }
}

@media (max-width: 768px) {
  .col-span-3,
  .col-span-4,
  .col-span-6 { grid-column: span 12; }
}
```