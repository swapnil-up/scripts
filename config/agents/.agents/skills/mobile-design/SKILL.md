---
name: mobile-design
description: Build distinctive, production-quality mobile application UIs that feel genuinely native and polished. Use this skill whenever the user is working on any mobile app UI — React Native, Expo, Flutter, SwiftUI, Jetpack Compose — or asks to design, build, improve, or review any mobile screen, component, navigation flow, or layout. Also trigger for "make this look better on mobile," "why does my app look cheap," styling a mobile component, or any interface destined for iOS or Android. Always consult this skill before writing any mobile UI code — it shapes every decision from layout to animations to safe areas.
---

Mobile is not a smaller screen. It's a different interaction model, a different physics, a different set of user expectations. This skill keeps you from accidentally building a website and calling it an app.

## Step 1: Identify Platform & Read the Reference

Before any code, establish the framework. Ask if unclear.

| Context | Framework |
|---|---|
| TypeScript/JS dev, cross-platform | React Native / Expo → `references/react-native.md` |
| Performance-critical, Dart, cross-platform | Flutter → `references/flutter.md` |
| iOS only, Swift, Apple ecosystem | SwiftUI → `references/swiftui.md` |
| Android only, Kotlin, Google ecosystem | Jetpack Compose → `references/compose.md` |

**Read the relevant reference file before writing any implementation code.** Framework choice shapes every API, every performance decision, every animation system.

---

## Step 2: Design Thinking for Mobile

Answer these before touching a layout:

- **One job per screen.** A mobile screen that tries to do three things does none of them well. What is the single user goal on this screen?
- **Who holds the phone?** Default to right-hand, single-thumb use. Your primary action belongs in the bottom natural zone — not the top right, not behind a menu.
- **What platform?** iOS users have muscle memory for swipe-back, bottom tab bars, and SF Symbols. Android users expect back gesture from edge, Material navigation, Material icons. Violating platform conventions feels wrong even when users can't name why.
- **What's the real environment?** Sunlight kills low-contrast UIs. A crowded subway train means no precision tapping. Cold hands, wet hands, one hand on a coffee cup. Design for physical reality.
- **Dark mode?** It's an expectation, not a feature. An app without dark mode looks unfinished in 2025.

---

## Step 3: Core Principles (Non-Negotiable)

### Touch Targets

- **Minimum 44×44pt (iOS) / 48×48dp (Android).** Always. A button can look small — pad invisibly.
- Destructive actions (delete, logout, send money) get larger targets + confirmation step.
- Never place two tappable elements closer than **8pt/dp** apart.

### Thumb Zones

```
┌─────────────────┐
│  ✗  HARD REACH  │  Top third — avoid primary CTAs here
│                 │
│  ⚡  STRETCH    │  Middle — secondary actions, info density
│                 │
│  ✓  NATURAL     │  Bottom third — PRIMARY CTAs, tab bar, FAB
└─────────────────┘
```

Bottom sheets, bottom tab bars, and FABs at bottom-right exist precisely because of this. Honor it.

### Safe Areas

**Always** wrap root content in the platform safe area container. Content must never hide behind:
- Status bar or Dynamic Island (top)
- Home indicator / gesture bar (bottom)
- Camera cutouts / notches (sides on landscape)
- Navigation bar (Android)

Ignoring this is the single most visible sign that an app was built by someone who doesn't use phones.

### Keyboard Handling

Any screen with a text input **must** handle keyboard appearance. The focused input must be visible when the keyboard appears. Test with both software keyboard and hardware keyboard (tablets, Bluetooth). See the platform reference file for the correct API to use.

### Screen Sizes & Pixel Density

- **Never hardcode layout in pixels.** Use `flex`, `%`, `dp`/`pt`, or responsive values.
- **Images must be provided at appropriate density:** @2x/@3x (iOS), xxhdpi/xxxhdpi (Android).
- **Tablets are real.** If your app runs on iPad or Android tablet, test it. A phone layout stretched to 12" looks abandoned.

---

## Step 4: Mobile Aesthetics

### Typography

Phones need **bigger type than you think**.

- Body text minimum: **16sp/pt.** Never use 12–14pt for anything users need to read.
- Support Dynamic Type (iOS) / font scaling (Android). Users who rely on this are real people.
- Limit to **two typeface families max.** One display/heading, one body/UI. More is noise.
- Line height: **1.4–1.6× for body copy,** tighter (1.1–1.2×) for display.
- Cap line width at ~65 characters using `maxWidth` or `width` constraints on wider screens.
- On mobile, type system = visual hierarchy. If your type is ambiguous, the whole layout is ambiguous.

### Color

- **Use semantic color tokens** that adapt between light and dark mode — not hardcoded hex values.
- **Contrast first:** WCAG AA minimum (4.5:1 body text, 3:1 large text). Pale text on light backgrounds that look soft on a design canvas become invisible in sunlight.
- **OLED black** (`#000000`) is a deliberate aesthetic choice — elements appear to float. Powerful when intentional; jarring when accidental.
- **One bold accent color** does more work than five brand colors. Keep it consistent. It should be your most saturated, most distinctive color.
- **System semantic colors first** (`systemBackground`, `Material Surface`, etc.) — they give you dark mode and accessibility automatically.

### Motion & Transitions

Native mobile motion has a specific grammar. Violating it makes your app feel like a website:

- **Duration:** UI transitions: 250–350ms. Micro-interactions: 100–200ms. Nothing over 500ms for routine interactions.
- **Easing:** Ease-in-out for most transitions. **Spring physics** for natural movement (drawers, cards, modals snapping into place). Linear only for progress indicators.
- **Navigation transitions:** Match the platform default unless you have a strong reason not to. iOS: right-to-left push. Android: bottom-up / shared element.
- **Reduced motion:** Always check the system accessibility setting and reduce or eliminate animation for users who need it.

### Polish Details That Separate Good from Great

- **Skeleton screens** over spinners for content-heavy lists — spinners say "I don't know my layout yet"
- **Haptic feedback** on actions that have weight: success confirmations, errors, destructive confirmations, selection
- **Empty states** that are designed and voice-appropriate — not a gray box with "No items"
- **Error states** that are human: tell the user what happened and what they can do about it
- **Elevation and depth:** iOS: blur/frosted glass (`.ultraThinMaterial`). Material 3: tonal color elevation. Use it consistently or not at all.
- **Consistent icon system:** SF Symbols (iOS), Material Symbols (Android), or one third-party set. Never mix icon families in the same app.

---

## Aesthetic Directions

Platform conventions give you 80% of the visual feel for free. Your job is the remaining 20% that expresses character. Pick a lane and execute it without compromise:

| Direction | Mobile Expression |
|---|---|
| **Platform-native** | SF Symbols + HIG (iOS) or Material 3 (Android). Maximum trust, minimum friction. |
| **Brand-forward** | Custom color tokens, custom type, custom icons — but safe areas, touch targets, and nav patterns are still respected. |
| **Minimalist/Premium** | Ultra-white or true-black, generous spacing, typographic hierarchy as the only decoration. |
| **Expressive/Playful** | Custom illustrations, spring animations, personality in empty states and error messages. Consumer apps. |
| **Cinematic/Immersive** | Full-bleed imagery, dark palette, glowing accents, cinematic transitions. Media, music, gaming. |

**Critical:** A vaguely-styled app looks worse than a strongly-styled one. Commit to the direction and execute every detail — spacing, shadow, icon weight, animation curve — as expressions of that single direction.

---

## Anti-Patterns: Never Do These

1. **Hamburger/sidebar nav on mobile** — use bottom tabs (≤5 items) or bottom sheet navigation
2. **Hover-only interactions** — no cursor on mobile; design for touch state, pressed state, disabled state
3. **Sub-44pt tap targets** — always pad to the minimum, even when the visual element is smaller
4. **No safe area handling** — content behind the notch/Dynamic Island/home indicator
5. **Fixed pixel layouts** — SE and iPad Pro run the same codebase; use flex and relative units
6. **Web-style transitions** (fade in/fade out for navigation) — it looks like a webpage
7. **Keyboard covering the input field** — the most common beginner oversight; always tested last
8. **Raster icons or 1× images** — pixelated on retina screens; use vectors or proper density buckets
9. **No loading state** — abrupt content arrival or a staring-at-nothing blank screen
10. **Ignoring dark mode** — forcing light-only in 2025
11. **Web navigation patterns** — breadcrumbs, top nav with many items, multi-level dropdowns
12. **Hardcoded text strings** — plan for i18n from day one; German and Arabic will break your layout

---

## Reference Files

Read the relevant file when implementing for a specific platform:

- `references/react-native.md` — StyleSheet, safe area, React Navigation, FlatList, Reanimated, Expo
- `references/flutter.md` — Widgets, Material 3, Cupertino, GoRouter, Riverpod, animations
- `references/swiftui.md` — ViewModifiers, property wrappers, NavigationStack, SF Symbols, animations
- `references/compose.md` — Composables, state hoisting, Material 3, Navigation Compose, LazyColumn