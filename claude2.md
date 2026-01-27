# YOTTANEST — AML Compliance Intelligence Platform
## Frontend Architecture Specification v1.0.0

---

## 1. Project Overview

**Yottanest** is an enterprise AML compliance platform for banking institutions with two core engines:
- **NetReport Engine**: Automated data scraping, business viability assessment, report generation
- **Smart Docs**: Document processing using OCR/NLP for invoices, contracts, KYC documents

### Target Users
| Role | Access Level | Functions |
|------|--------------|-----------|
| Compliance Analyst | Standard | Case review, document processing, alert triage |
| Senior Officer | Elevated | Report approval, risk threshold configuration |
| Manager | Administrative | Team oversight, audit trail, escalations |
| Admin | Full | User management, system configuration |

---

## 2. Technology Stack

```
Framework:          Next.js 14.x (App Router)
Language:           TypeScript 5.x (Strict Mode)
Styling:            Tailwind CSS 3.4.x + shadcn/ui
Icons:              Lucide React
Animation:          Framer Motion 10.x
Charts:             Recharts 2.x
Tables:             TanStack Table v8
Forms:              React Hook Form + Zod
State:              Zustand 4.x (client) + TanStack Query v5 (server)
Real-Time:          Socket.io Client
```

---

## 3. Design System

### 3.1 Color Palette

```css
/* Primary - Deep Navy */
--primary-500: #1A365D;
--primary-600: #152A4A;
--primary-700: #102038;

/* Secondary - Corporate Blue */
--secondary-500: #2C5282;
--secondary-400: #4299E1;

/* Risk Levels */
--risk-critical: #DC2626;   /* 90-100 */
--risk-high: #EA580C;       /* 70-89 */
--risk-medium: #CA8A04;     /* 40-69 */
--risk-low: #16A34A;        /* 20-39 */
--risk-clear: #0D9488;      /* 0-19 */

/* System States */
--success: #059669;
--warning: #D97706;
--error: #DC2626;
--info: #0284C7;

/* Neutrals */
--neutral-0: #FFFFFF;
--neutral-50: #F9FAFB;
--neutral-100: #F3F4F6;
--neutral-200: #E5E7EB;
--neutral-300: #D1D5DB;
--neutral-400: #9CA3AF;
--neutral-500: #6B7280;
--neutral-600: #4B5563;
--neutral-700: #374151;
--neutral-800: #1F2937;
--neutral-900: #111827;
```

### 3.2 Typography

```css
--font-family: 'Inter', -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 2rem;      /* 32px */
```

### 3.3 Spacing & Layout

```css
/* Spacing (base: 4px) */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */

/* Border Radius */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;

/* Shadows */
--shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
--shadow-md: 0 4px 6px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1);

/* Z-Index */
--z-dropdown: 1000;
--z-sticky: 1100;
--z-modal: 1400;
--z-tooltip: 1600;
--z-toast: 1700;

/* Breakpoints */
--bp-sm: 640px;
--bp-md: 768px;
--bp-lg: 1024px;
--bp-xl: 1280px;
--bp-2xl: 1536px;
```

---

## 4. Application Routes

```
/dashboard                    → Main dashboard
/dashboard/alerts             → Alert management
/dashboard/transactions       → Transaction monitoring
/dashboard/entities           → Entity list
/dashboard/entities/[id]      → Entity detail
/dashboard/reports            → Reports list
/dashboard/reports/new        → Report wizard
/dashboard/documents          → Smart Docs processing
/dashboard/documents/upload   → Upload interface
/dashboard/tasks              → Task management
/dashboard/cases              → Case management
/dashboard/risk-overview      → Risk analytics
/settings                     → User settings
/admin                        → Admin panel
/admin/users                  → User management
/admin/audit-log              → Audit trail
```

---

## 5. Layout Structure

### 5.1 Top Navbar
```
Height: 64px
Background: white
Border Bottom: 1px solid neutral-200
Shadow: shadow-sm
Position: Fixed, top: 0
Z-Index: z-sticky
Padding: 0 24px

┌──────────────────────────────────────────────────────────────────┐
│ [≡] │ YOTTANEST │        [🔍 Search... ⌘K]        │ 🔔 │ 👤 ▾ │
└──────────────────────────────────────────────────────────────────┘

Elements:
- Sidebar Toggle: 40×40px, icon 20px
- Logo: height 32px, clickable → /dashboard
- Search: width 480px, height 40px, bg neutral-100, radius 8px
- Notification Bell: 40×40px, red badge if unread
- User Avatar: 36×36px, radius-full, dropdown on click
```

### 5.2 Sidebar Navigation
```
Width Expanded: 280px
Width Collapsed: 72px
Background: primary-500 (Deep Navy)
Position: Fixed, left: 0, top: 64px
Height: calc(100vh - 64px)
Padding: 16px 12px
Transition: width 300ms ease

Nav Item:
- Height: 44px
- Padding: 0 12px
- Radius: 8px
- Icon: 20×20px
- Gap: 12px
- Color: rgba(255,255,255,0.7)
- Hover: bg rgba(255,255,255,0.1), color 0.9
- Active: bg rgba(255,255,255,0.15), color white, border-left 3px secondary-400

Sections:
├─ MAIN
│  ├─ 📊 Dashboard
│  ├─ ⚠️ Alerts [badge]
│  ├─ 💹 Transactions
│  └─ 🏢 Entities
├─ INVESTIGATION
│  ├─ 📁 Cases [badge]
│  ├─ ✅ Tasks [badge]
│  └─ 📄 Reports
├─ DOCUMENTS
│  ├─ 📤 Upload
│  ├─ 📋 Processing [badge]
│  └─ ✓ Completed
├─ ANALYTICS
│  ├─ 📈 Risk Overview
│  └─ 🗺️ Geographic
├─ [Spacer]
├─ ⚙️ Settings
├─ ❓ Help
└─ [User Profile Card]
```

### 5.3 Main Content Area
```
Margin Left: 280px (72px collapsed)
Margin Top: 64px
Min Height: calc(100vh - 64px)
Background: neutral-50
Padding: 24px
Transition: margin-left 300ms ease

Grid: 12 columns, gap 24px
```

---

## 6. Core Components

### 6.1 Stat Card
```
┌─────────────────────┐
│ [icon] Label        │
│                     │
│ 1,247               │
│ ↑ +12.5% vs last wk │
└─────────────────────┘

Min Width: 200px
Height: 140px
Padding: 24px
Background: white
Border: 1px solid neutral-200
Radius: 12px
Shadow: shadow-sm

Icon Container: 40×40px, radius 10px, bg primary-50
Value: 32px, weight 700, color neutral-900
Trend: 13px, color success/error based on direction
```

### 6.2 Alert Card
```
┌─────────────────────────────────────────┐
│ 🔴 CRITICAL │ Unusual Wire Transfer     │
│             │ Entity: Meridian LLC      │
│             │ Amount: $4,250,000        │
│             │ [Investigate] [Dismiss]   │
└─────────────────────────────────────────┘

Padding: 16px 20px
Border Left: 4px solid (severity color)
Radius: 8px
Background: white
Shadow: shadow-xs → shadow-sm on hover
Severity Badge: 80×24px, uppercase, weight 700
```

### 6.3 Risk Score Badge
```
Circular: 48×48px
Border: 3px solid (risk color)
Font: 16px, weight 700
Background: risk color at 10% opacity

Critical (90-100): red
High (70-89): orange
Medium (40-69): yellow
Low (20-39): green
Clear (0-19): teal
```

### 6.4 Buttons
```
Sizes:
- sm: height 32px, padding 0 12px, font 13px
- md: height 40px, padding 0 16px, font 14px
- lg: height 48px, padding 0 20px, font 16px

Variants:
- Primary: bg primary-500, color white, hover primary-600
- Secondary: bg white, border neutral-300, hover neutral-50
- Danger: bg error, color white
- Ghost: bg transparent, hover neutral-100

Radius: 8px
Weight: 600 (primary/danger), 500 (others)
Transition: all 150ms ease
```

### 6.5 Data Table
```
Container: bg white, border neutral-200, radius 12px

Header:
- bg neutral-50, border-bottom neutral-200
- font 12px, weight 600, uppercase, letter-spacing 0.05em
- padding 14px 16px

Row:
- border-bottom neutral-100
- padding 16px
- hover bg neutral-50

Footer:
- padding 12px 16px
- pagination buttons 32×32px
```

### 6.6 Form Elements
```
Input:
- Height: 40px
- Padding: 0 12px
- Border: 1px solid neutral-300
- Radius: 8px
- Focus: border primary-500, shadow 0 0 0 3px rgba(26,54,93,0.1)
- Error: border error, shadow error variant

Checkbox: 18×18px, radius 4px
Toggle: track 44×24px, thumb 20px
Select: same as input + chevron icon
```

### 6.7 Modal
```
Overlay: bg rgba(0,0,0,0.5), backdrop-blur 4px
Container: bg white, radius 16px, shadow-2xl, max-height 90vh

Sizes: sm 400px, md 560px, lg 720px, full 1200px

Header: padding 24px 24px 0
Body: padding 24px, overflow-y auto
Footer: padding 16px 24px 24px, flex justify-end, gap 12px
```

### 6.8 Toast
```
Position: fixed, bottom 24px, right 24px
Width: max 420px
Padding: 16px 20px
Radius: 12px
Shadow: shadow-lg
Border Left: 4px solid (type color)

Types: success (green), error (red), warning (amber), info (blue)
```

---

## 7. Dashboard Modules

### 7.1 Risk Overview Panel
```
┌─────────────────────────────────────────────────────────────┐
│ RISK OVERVIEW                                    [Refresh]  │
├─────────────────────────────────────────────────────────────┤
│ [Stat Card] [Stat Card] [Stat Card] [Stat Card]             │
│  Total       Critical    High        Medium                 │
│  2,847       24          156         423                    │
├─────────────────────────────────────────────────────────────┤
│ [Donut Chart]              │ [Line Chart - 30 Day Trend]    │
│  Risk Distribution         │  Risk Score Over Time          │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Transaction Table
```
┌─────────────────────────────────────────────────────────────┐
│ [Search...] [Date ▾] [Amount ▾] [Risk ▾] [Status ▾]         │
├────┬────────────┬────────────┬──────────┬──────┬──────┬─────┤
│ □  │ ID         │ Entity     │ Amount   │ Risk │Status│Time │
├────┼────────────┼────────────┼──────────┼──────┼──────┼─────┤
│ □  │ TXN-001    │ Acme Corp  │ $125,000 │ 🔴92 │Review│10:23│
│ □  │ TXN-002    │ Beta LLC   │ $45,200  │ 🟡56 │Clear │10:18│
└────┴────────────┴────────────┴──────────┴──────┴──────┴─────┘
│ Showing 1-10 of 1,247            [←] [1] [2] [3] ... [→]    │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Entity Detail View
```
┌─────────────────────────────────────────────────────────────┐
│ ← Back                                                      │
├─────────────────────────────────────────────────────────────┤
│ ACME CORPORATION                              ┌────────────┐│
│ Financial Services | Delaware, USA            │    87      ││
│ EIN: 12-3456789                               │ RISK SCORE ││
│ [Generate Report] [Export] [Escalate]         └────────────┘│
├─────────────────────────────────────────────────────────────┤
│ [Overview] [Transactions] [Documents] [Risk] [Timeline]     │
├─────────────────────────────────────────────────────────────┤
│ Company Info          │ Risk Breakdown                      │
│ ─────────────         │ Ownership    ████████░░ 78%         │
│ Legal Name: Acme Corp │ Transaction  ██████████ 92%         │
│ Status: Active        │ Geographic   ███████░░░ 65%         │
│ Industry: Finance     │ Sanctions    ██░░░░░░░░ 18%         │
├─────────────────────────────────────────────────────────────┤
│ Beneficial Owners                                           │
│ 👤 John Smith | CEO, 45% | Medium Risk                      │
│ 👤 Jane Doe | CFO, 30% | Low Risk                           │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 Document Upload (Smart Docs)
```
┌─────────────────────────────────────────────────────────────┐
│ DOCUMENT PROCESSING                                         │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                       📄                                │ │
│ │          Drag and drop files here                       │ │
│ │              or click to browse                         │ │
│ │      PDF, PNG, JPG, DOCX, XLSX (Max 25MB)              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ UPLOAD QUEUE                                                │
│ 📄 invoice_001.pdf      ████████████████░░░░ 85% ⏳         │
│ 📄 contract.docx        ████████████████████ 100% ✓        │
├─────────────────────────────────────────────────────────────┤
│ RECENTLY PROCESSED                              [View All]  │
│ bank_statement.pdf │ Financial │ Acme Corp │ ✓ Extracted   │
│ articles.pdf       │ Legal     │ Beta LLC  │ ✓ Verified    │
└─────────────────────────────────────────────────────────────┘

Drop Zone:
- Height: 200px
- Border: 2px dashed neutral-300
- Radius: 16px
- Hover/Drag: border primary-500, bg primary-50
```

### 7.5 Report Wizard
```
┌─────────────────────────────────────────────────────────────┐
│ GENERATE REPORT                                             │
├─────────────────────────────────────────────────────────────┤
│     ●────────●────────○────────○────────○                   │
│     1        2        3        4        5                   │
│   Select  Configure  Review  Generate  Complete             │
├─────────────────────────────────────────────────────────────┤
│ SELECT REPORT TYPE                                          │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│ │     📋      │ │     ⚠️      │ │     📊      │             │
│ │ SAR Report  │ │ Risk Memo   │ │ Due Diligence│            │
│ └─────────────┘ └─────────────┘ └─────────────┘             │
│                                                             │
│                              [Cancel]  [Next Step →]        │
└─────────────────────────────────────────────────────────────┘

Step Indicator:
- Circle: 32px, line height 2px
- Active: primary-500
- Complete: success
- Inactive: neutral-300

Report Card:
- Width: 200px, Height: 160px
- Padding: 24px
- Border: 2px solid neutral-200
- Selected: border primary-500, bg primary-50
```

### 7.6 Task Kanban
```
┌─────────────────────────────────────────────────────────────┐
│ MY TASKS                          [+ New] [Filter] [Sort]   │
├─────────────────────────────────────────────────────────────┤
│ TO DO (5)    │ IN PROGRESS (3)│ IN REVIEW (2) │ DONE (8)    │
│ ┌──────────┐ │ ┌──────────┐   │ ┌──────────┐  │             │
│ │Review SAR│ │ │Verify KYC│   │ │Approve   │  │             │
│ │#TK-2401  │ │ │#TK-2398  │   │ │Risk Memo │  │             │
│ │🔴 High   │ │ │🟡 Medium │   │ │#TK-2395  │  │             │
│ │Due: Today│ │ │Due: 2d   │   │ │🟡 Medium │  │             │
│ │👤 JSmith │ │ │👤 JDoe   │   │ │Due: 3d   │  │             │
│ └──────────┘ │ └──────────┘   │ └──────────┘  │             │
└─────────────────────────────────────────────────────────────┘

Column: width 280px, bg neutral-100, radius 12px, padding 12px
Task Card: bg white, radius 8px, padding 12px, shadow-xs
Drag: shadow-lg, opacity 0.9, rotate 3deg
```

---

## 8. State Management

### Query Keys
```typescript
export const queryKeys = {
  entities: {
    all: ['entities'],
    list: (filters) => ['entities', 'list', filters],
    detail: (id) => ['entities', 'detail', id],
  },
  transactions: {
    all: ['transactions'],
    list: (filters) => ['transactions', 'list', filters],
  },
  alerts: {
    all: ['alerts'],
    realtime: () => ['alerts', 'realtime'],
    unreadCount: () => ['alerts', 'unread-count'],
  },
  dashboard: {
    overview: () => ['dashboard', 'overview'],
    riskTrend: (period) => ['dashboard', 'risk-trend', period],
  },
};
```

### Zustand Store
```typescript
interface AppState {
  ui: {
    sidebarCollapsed: boolean;
    theme: 'light' | 'dark';
    activeModal: string | null;
  };
  filters: {
    transactions: TransactionFilters;
    entities: EntityFilters;
    dateRange: DateRange;
  };
  notifications: {
    items: Notification[];
    unreadCount: number;
  };
}
```

---

## 9. API Endpoints

```
Authentication:
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
GET    /auth/me

Entities:
GET    /entities
POST   /entities
GET    /entities/:id
PATCH  /entities/:id
GET    /entities/:id/risk-factors
POST   /entities/:id/recalculate-risk
GET    /entities/:id/transactions
GET    /entities/:id/timeline

Transactions:
GET    /transactions
GET    /transactions/:id
POST   /transactions/:id/flag
POST   /transactions/:id/clear
POST   /transactions/:id/escalate

Alerts:
GET    /alerts
GET    /alerts/unread-count
POST   /alerts/:id/acknowledge
POST   /alerts/:id/dismiss
POST   /alerts/:id/escalate

Reports:
GET    /reports
POST   /reports
GET    /reports/:id
POST   /reports/:id/generate
GET    /reports/:id/download

Documents:
POST   /documents/upload
GET    /documents/:id
POST   /documents/:id/process
GET    /documents/:id/extracted-data

Dashboard:
GET    /dashboard/overview
GET    /dashboard/risk-distribution
GET    /dashboard/risk-trend
```

---

## 10. WebSocket Events

```typescript
// Incoming
'alert:new'           → New alert created
'alert:updated'       → Alert status changed
'transaction:flagged' → Transaction flagged
'document:processed'  → Document OCR complete
'entity:risk-changed' → Risk score updated

// Outgoing
'subscribe:alerts'    → Subscribe to alerts
'subscribe:entity'    → Subscribe to entity updates
'unsubscribe:all'     → Unsubscribe from all
```

---

## 11. File Structure

```
src/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   ├── alerts/
│   │   ├── entities/
│   │   ├── transactions/
│   │   ├── reports/
│   │   ├── documents/
│   │   ├── tasks/
│   │   └── risk-overview/
│   ├── settings/
│   ├── admin/
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/              # shadcn components
│   ├── layout/          # Navbar, Sidebar
│   ├── dashboard/       # Dashboard widgets
│   ├── entities/        # Entity components
│   ├── transactions/    # Transaction components
│   ├── alerts/          # Alert components
│   ├── reports/         # Report components
│   ├── documents/       # Document components
│   ├── charts/          # Chart components
│   └── common/          # Shared components
├── hooks/
│   ├── useAuth.ts
│   ├── useRealTimeAlerts.ts
│   └── queries/         # TanStack Query hooks
├── lib/
│   ├── api-client.ts
│   ├── websocket.ts
│   ├── utils.ts
│   └── validators.ts
├── stores/
│   └── index.ts         # Zustand stores
├── types/
│   └── index.ts
└── constants/
    └── index.ts
```

---

## 12. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘/Ctrl + K` | Open global search |
| `⌘/Ctrl + /` | Toggle sidebar |
| `⌘/Ctrl + N` | Create new |
| `Escape` | Close modal |
| `J / K` | Navigate list |
| `Enter` | Open selected |
| `?` | Show shortcuts |

---

## 13. Performance Targets

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| First Input Delay | < 100ms |
| Cumulative Layout Shift | < 0.1 |
| Initial Bundle Size | < 200KB gzipped |

---

## 14. Accessibility

- WCAG 2.1 AA compliance
- All interactive elements keyboard accessible
- Focus indicators: 2px solid primary-500, offset 2px
- Color contrast: 4.5:1 minimum
- ARIA labels on all icons and controls
- Skip navigation link
- Semantic HTML structure

---

**© 2024 Yottanest. All Rights Reserved.**