---
name: Voltage Industrial
colors:
  surface: '#111317'
  surface-dim: '#111317'
  surface-bright: '#37393e'
  surface-container-lowest: '#0c0e12'
  surface-container-low: '#1a1c20'
  surface-container: '#1e2024'
  surface-container-high: '#282a2e'
  surface-container-highest: '#333539'
  on-surface: '#e2e2e8'
  on-surface-variant: '#c2caad'
  inverse-surface: '#e2e2e8'
  inverse-on-surface: '#2f3035'
  outline: '#8c9479'
  outline-variant: '#434933'
  surface-tint: '#a0d800'
  primary: '#ffffff'
  on-primary: '#253600'
  primary-container: '#b7f700'
  on-primary-container: '#506e00'
  inverse-primary: '#4b6700'
  secondary: '#fface8'
  on-secondary: '#5e0053'
  secondary-container: '#ff24e4'
  on-secondary-container: '#520049'
  tertiary: '#ffffff'
  on-tertiary: '#3c0090'
  tertiary-container: '#e9ddff'
  on-tertiary-container: '#7829ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#b7f700'
  primary-fixed-dim: '#a0d800'
  on-primary-fixed: '#141f00'
  on-primary-fixed-variant: '#374e00'
  secondary-fixed: '#ffd7f0'
  secondary-fixed-dim: '#fface8'
  on-secondary-fixed: '#3a0033'
  on-secondary-fixed-variant: '#840076'
  tertiary-fixed: '#e9ddff'
  tertiary-fixed-dim: '#d1bcff'
  on-tertiary-fixed: '#23005b'
  on-tertiary-fixed-variant: '#5700c9'
  background: '#111317'
  on-background: '#e2e2e8'
  surface-variant: '#333539'
typography:
  display-lg:
    fontFamily: Lexend
    fontSize: 64px
    fontWeight: '900'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Lexend
    fontSize: 40px
    fontWeight: '800'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Lexend
    fontSize: 32px
    fontWeight: '800'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Lexend
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '500'
    lineHeight: '1.5'
  body-md:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '700'
    lineHeight: '1.2'
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.4'
spacing:
  unit: 4px
  gutter: 24px
  margin-sm: 16px
  margin-md: 32px
  margin-lg: 48px
  stack-xs: 8px
  stack-md: 24px
  container-max: 1440px
---

## Brand & Style

The design system is an energetic fusion of **Neo-Brutalism** and high-performance **Industrial software**. It targets technical users (MLOps engineers, Data Scientists) who value precision but crave a UI that breaks the monotony of standard enterprise software. 

The aesthetic is characterized by:
- **Raw Confidence:** Unapologetic use of heavy strokes and saturated accents.
- **Structured Chaos:** A strict grid layout disrupted by oversized typography and vibrant "ink-trap" aesthetics.
- **Tactile Digitalism:** UI elements that feel like physical industrial toggles—heavy, responsive, and definitive.
- **Professional Edge:** While "funky," the system remains functional through high information density and clear state signaling.

## Colors

This design system utilizes a **High-Contrast Dark Mode** foundation. The palette is designed to pop against a deep slate background, ensuring that critical data points are impossible to miss.

- **Primary (Electric Lime):** Used for primary actions, success states, and critical active data paths.
- **Secondary (Hot Pink):** Reserved for highlights, notifications, and secondary interactive elements.
- **Tertiary (Electric Purple):** Used for data visualization clusters and decorative industrial accents.
- **Neutral (Deep Slate):** The "ink" of the system, used for backgrounds and surfaces to provide a heavy, grounded feel.
- **Borders:** Pure Black (#000000) is used exclusively for all component strokes to maintain the Neo-Brutalist edge.

## Typography

The typography strategy leverages "ink-trap" aesthetics and monospaced technicality to reinforce the industrial MLOps vibe.

- **Headlines:** Use **Lexend** at its heaviest weights (800-900). It provides the "oversized" look required for the Neo-Brutalist aesthetic while remaining highly legible.
- **Body:** **Space Grotesk** provides a technical yet approachable feel for long-form content and descriptions.
- **Labels & Data:** **JetBrains Mono** is used for all technical metadata, labels, and code snippets, grounding the system in a developer-centric reality.
- **Styling:** Use tight letter-spacing on display types to create a "blocked" look.

## Layout & Spacing

The layout follows a **Rigid Industrial Grid**. Everything is based on a 4px baseline, but spacing is intentionally generous ("chunky") to avoid visual clutter amidst the high-contrast elements.

- **Grid:** A 12-column fluid grid for desktop with heavy 24px gutters.
- **Borders as Spacing:** In this design system, borders are 4px thick. Spacing should be measured from the *outside* of the border to maintain alignment.
- **Reflow:** On mobile, margins reduce to 16px, and multi-column layouts collapse into a single vertical "stack" of heavy cards.
- **Hard-Edges:** Elements should align perfectly to the grid edges; avoid "floating" elements or soft centering.

## Elevation & Depth

This system rejects soft shadows and ambient light. Depth is communicated through **Hard Shadows** and **Tonal Displacement**.

- **Hard Shadows:** Use 100% opacity black shadows offset by 4px or 8px (e.g., `8px 8px 0px #000000`). This creates a "sticker" or "physical cutout" effect.
- **Interactive Depth:** When a button or card is "pressed," the shadow should disappear, and the element should translate (move) 4px down and to the right to simulate a physical click.
- **Tonal Layers:** High-priority containers use the `surface_color_hex`. Secondary containers use a simple 4px black outline with no fill (Ghost style) or a dark gray fill.
- **No Blurs:** Background blurs and soft glows are strictly prohibited.

## Shapes

The shape language is **Strictly Sharp (0px)**. 

- **Corners:** Every button, input, card, and modal must have 90-degree angles. This reinforces the industrial, brutalist aesthetic.
- **Strokes:** A uniform **4px black border** must be applied to all interactive elements and containers.
- **Icons:** Use thick-stroke (2px+) geometric icons. Avoid rounded icon sets; prefer sharp, blocky glyphs that match the Lexend typeface character.

## Components

### Buttons
- **Primary:** Electric Lime fill, 4px Black border, 4px Black hard shadow. Text is Black, Bold Lexend.
- **Secondary:** Hot Pink fill, 4px Black border, 4px Black hard shadow.
- **State Change:** On hover, the shadow grows to 8px. On active (click), the shadow is 0px and the button translates +4px.

### Input Fields
- **Default:** Transparent fill or Dark Slate fill, 4px Black border.
- **Focus:** Border remains Black, but a 4px "outer glow" (hard, no blur) in Electric Purple is added.
- **Labels:** Always use JetBrains Mono, uppercase, placed directly above the field.

### Cards
- **Industrial Container:** 4px Black border, Slate fill, 8px Black hard shadow.
- **Header:** Cards should have a distinct "header bar" separated by a 4px horizontal black line.

### Chips & Tags
- High-contrast fills (Electric Purple or Hot Pink) with Black text. No shadows for chips to keep them distinct from buttons.

### Progress Bars & Gauges
- **Track:** Heavy Black 4px border with a Dark Slate empty fill.
- **Indicator:** Solid Electric Lime fill. No gradients. Use "segmented" blocks for a more mechanical feel.

### Status Indicators
- Use a large, solid square (not a circle) in the status color (Lime for OK, Red for Error) with a 2px Black border.