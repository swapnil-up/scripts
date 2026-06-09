---
name: mobile-design
description: Build distinctive, production-quality mobile application UIs that feel genuinely native and polished. Use this skill whenever the user is working on any mobile app UI in Kotlin Multiplatform (KMP) or Jetpack Compose — or asks to design, build, improve, or review any mobile screen, component, navigation flow, or layout. Also trigger for "make this look better on mobile," "why does my app look cheap," styling a mobile component, or any Compose/KMP interface destined for iOS or Android. Always consult this skill before writing any mobile UI code — it shapes every decision from layout to animations to safe areas.
---

Mobile is not a smaller screen. It's a different interaction model, a different physics, a different set of user expectations. This skill keeps you from accidentally building a website and calling it an app.

**Stack:** Kotlin Multiplatform + Jetpack Compose. All implementation details in `references/compose.md`.

---

## Step 1: Design Thinking for Mobile

Answer these before touching a layout:

- **One job per screen.** A mobile screen that tries to do three things does none of them well. What is the single user goal on this screen?
- **Who holds the phone?** Default to right-hand, single-thumb use. Your primary action belongs in the bottom natural zone — not the top right, not behind a menu.
- **What's the real environment?** Sunlight kills low-contrast UIs. A crowded subway train means no precision tapping. Cold hands, wet hands, one hand on a coffee cup. Design for physical reality.
- **Dark mode?** It's an expectation, not a feature. An app without dark mode looks unfinished in 2025.

---

## Step 2: Core Principles (Non-Negotiable)

### Touch Targets

- **Minimum 48×48dp.** Always. A button can look small — pad invisibly.
- Destructive actions (delete, logout, send money) get larger targets + confirmation step.
- Never place two tappable elements closer than **8dp** apart.

### Thumb Zones

```
┌─────────────────┐
│  ✗  HARD REACH  │  Top third — avoid primary CTAs here
│                 │
│  ⚡  STRETCH    │  Middle — secondary actions, info density
│                 │
│  ✓  NATURAL     │  Bottom third — PRIMARY CTAs, nav bar, FAB
└─────────────────┘
```

Bottom sheets, `NavigationBar`, and FABs at bottom-right exist precisely because of this. Honor it.

### Safe Areas

**Always** use `Scaffold` with `enableEdgeToEdge()` in your Activity. Content must never hide behind the status bar, gesture bar, or camera cutout. See compose.md → Window Insets.

### Keyboard Handling

Any screen with a text input must handle keyboard appearance. The focused input must stay visible when the keyboard appears. Use `WindowInsets.ime` with `imePadding()` modifier.

### Screen Sizes & Pixel Density

- **Never hardcode layout in pixels.** Use `dp`, `sp`, `fillMaxWidth`, `weight()`, or `WindowSizeClass`.
- **Vector drawables everywhere** — `ImageVector`, Material Symbols, or SVG-imported vectors. No raster icons.
- **WindowSizeClass** for tablet/foldable layouts: `Compact` / `Medium` / `Expanded`.

---

## Step 3: The Visual Constraint System

The beginner mistake is treating aesthetics as open choices. Every open choice is a chance to make a bad one. The fix is a constraint system where the tokens themselves make bad choices impossible.

**The default aesthetic for this skill is Neubrutalism.** Here's why it's the right default for solo developers:

- **Thick borders create visual separation automatically** — no calibrating subtle elevation or trying to pick the right blur radius
- **Hard, unblurred drop shadows look intentional at any level of polish** — no skill required to make them look good
- **Bold type hierarchy is obvious** — no agonizing between 16sp semi-bold and 17sp medium
- **A high-contrast 3-color palette literally cannot produce muddy or unreadable combinations**
- **The raw, honest aesthetic means imperfections read as deliberate** — this is the key advantage over Material Design, which punishes inconsistency

Material Design is a precision instrument. Neubrutalism is a sledgehammer. When you need something that looks good without a design team, reach for the sledgehammer.

---

### The Neubrut Token System

Copy these verbatim. Do not improvise from them — the rigidity is the point.

```
── BORDERS ──────────────────────────────────────────────
border:           2.5dp solid [INK]
border-radius:    8dp (cards), 0dp (flat panels), 9999dp (pills only)

── SHADOWS ──────────────────────────────────────────────
card shadow:      x:4  y:4  blur:0  color:[INK]     ← NO blur. Ever.
button shadow:    x:3  y:3  blur:0  color:[INK]
pressed state:    x:1  y:1  blur:0  color:[INK]     ← shadow shrinks on press

── SPACING (4dp grid — no other values) ─────────────────
4  8  12  16  20  24  32  40  48  64

── TYPE WEIGHTS ─────────────────────────────────────────
display / headline:   800–900 (Black / ExtraBold)
body:                 500–600 (Medium / SemiBold)
label / caption:      600–700 (SemiBold / Bold), ALL CAPS, letterSpacing: 0.08em

── COLOR SLOTS (3 colors maximum) ───────────────────────
[BG]     Background    #FAFAFA light  /  #0F0F0F dark
[INK]    Text/borders  #0A0A0A light  /  #F5F5F5 dark
[ACCENT] One loud hit  pick ONE from the palette below

── ACCENT PALETTE (pick exactly one, never mix) ─────────
#FFD60A  Volt Yellow    — energy, fitness, productivity
#FF6B35  Neon Orange    — food, social, marketplace
#00F5D4  Electric Mint  — finance, health, utilities
#FF3D6B  Hot Pink       — entertainment, lifestyle
#3D5AFE  Electric Blue  — tools, developer, technical
#ADFF2F  Acid Green     — gaming, sports, tracking
```

**Dark mode:** swap `[BG]` ↔ `[INK]`. The accent stays identical — it pops even harder on dark.

---

### Typography Rules

```
Screen title (H1):    28–32sp, weight 800, [INK], letterSpacing: -0.02em
Section header (H2):  20–24sp, weight 700, [INK]
Card title (H3):      16–18sp, weight 700, [INK]
Body:                 16sp,    weight 500, [INK] at 0.85 opacity
Label / tag:          11–12sp, weight 700, ALL CAPS, [INK] at 0.6 opacity, letterSpacing: 0.08em
Button text:          15–16sp, weight 700, ALL CAPS or Title Case
```

- **Maximum 2 typefaces.** One display (Archivo Black, Syne, Space Grotesk), one body (DM Sans, IBM Plex Sans, Inter).
- Body minimum 16sp. Anything smaller is invisible outdoors.
- **Tight lineHeight for headlines (1.0–1.15), normal for body (1.5).**

---

### Shadows & Borders — The Signature Move

The hard shadow is what makes neubrutalism identifiable. Apply consistently:

```
Every card:           border 2.5dp [INK] + shadow(4,4,0,[INK])
Every button:         border 2.5dp [INK] + shadow(3,3,0,[INK])
Every input field:    border 2.5dp [INK] + shadow(2,2,0,[INK])
Every modal/sheet:    border 2.5dp [INK] + shadow(6,6,0,[INK])
```

**The pressed interaction is built into the shadow (spring-animated):**
- Normal:  `offset(0,0)` + `shadow(3,3,0,[INK])`
- Pressed: `offset(2dp,2dp)` + `shadow(1,1,0,[INK])`

The element physically presses down. Satisfying every time. Uses spring animation — see compose.md → Spring Physics.

### Color Application Map

```
Screen background:     [BG]
NavigationBar:         [ACCENT]
Primary CTA button:    [ACCENT] fill, [INK] border + shadow, [INK] text
Secondary/ghost CTA:   [BG] fill, [INK] border, no shadow
Active tab / selected: [ACCENT] background
Card background:       [BG] default  OR  [ACCENT] (1 in 5 max — the 1-in-5 rule)
Tags / badges:         [ACCENT] bg, [INK] text
Error override:        #FF3B30
Success override:      #34C759
```

**1-in-5 rule:** No more than 1 in 5 cards in a list gets the accent fill. Otherwise the accent loses its punch.

---

## Step 4: The Six Quality Upgrades

These are the highest-ROI changes you can make to a working app. Audit every screen against this list before shipping. Full implementation for each in `references/compose.md`.

| # | Upgrade | Signal it's missing | Effort |
|---|---|---|---|
| **1** | **Spring physics** | Animations feel mechanical, linear, or sudden | 2h |
| **2** | **Skeleton screens** | Screen goes blank / spinner appears while data loads | 4h |
| **3** | **Haptics** | Tapping buttons feels like tapping glass | 3h |
| **4** | **Empty & error states** | Users see blank screens or generic "Error" text | 6h |
| **5** | **Shared element transitions** | List → detail navigation feels like a cut, not a flow | 4h |
| **6** | **Value-first onboarding** | Users hit a login or permission wall before seeing the app | 1–2d |

Check every screen against #1–#4. Every nav transition against #5. First-launch flow against #6.

---

## Anti-Patterns: Never Do These

### Universal
1. **Hamburger/sidebar nav** — use `NavigationBar` (≤5 items) or bottom sheet navigation
2. **Hover-only interactions** — no cursor on mobile; design for pressed state, focused state, disabled state
3. **Sub-48dp tap targets** — always pad to the minimum, even when the visual is smaller
4. **No safe area handling** — content behind status bar or gesture bar
5. **Fixed pixel layouts** — use `dp`, `fillMaxWidth`, `WindowSizeClass`
6. **Web-style transitions** (opacity-only fades for navigation) — it looks like a website
7. **Keyboard covering the input** — use `imePadding()` / `imeNestedScroll()`
8. **Raster icons** — use `ImageVector` or Material Symbols everywhere
9. **No loading state** — abrupt content arrival
10. **Ignoring dark mode** — forcing light-only

### Neubrut-specific
11. **Blurred drop shadows** — `blur > 0` breaks the aesthetic immediately
12. **More than 3 colors** — a fourth color dilutes every color
13. **Gradient fills** — neubrutalism is flat. No gradients, ever.
14. **Font weight under 500** — weight 300–400 disappears in this system
15. **Corner radius > 16dp on cards** — starts looking like a different aesthetic
16. **Inconsistent shadow direction** — all shadows go bottom-right. Mixing directions looks like a bug.

---

## Reference File

`references/compose.md` — full implementation of all the above: spring physics, shimmer skeletons, haptics event map, empty/error state patterns, shared element transitions, value-first onboarding, plus the Compose fundamentals.