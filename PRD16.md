# PRD 16: Landing Page & Marketing Site

## Introduction

Create SyncScript's production landing page following the Bitcoin DeFi aesthetic defined in CLAUDE.md. This is the first impression for potential users and must showcase the platform's value proposition through premium visuals, smooth animations, and clear CTAs. The page will feature an animated hero with 3D orb, stats ticker, features grid, how-it-works timeline, testimonials, pricing tiers, and a conversion-focused CTA section.

## Goals

- Create a visually stunning landing page matching Bitcoin DeFi aesthetic exactly
- Clearly communicate SyncScript's value proposition for collaborative research
- Drive conversions through strategic CTA placement
- Achieve excellent performance scores (90+ Lighthouse)
- Ensure full responsiveness across all device sizes
- Implement smooth scroll-triggered animations using Framer Motion

## User Stories

### US-001: Setup Marketing Route Group and Layout
**Description:** As a developer, I need the marketing route group structure so landing page components are isolated from the app.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/(marketing)/layout.tsx` with marketing-specific layout
- [x] Create `frontend/src/app/(marketing)/page.tsx` as landing page entry
- [x] Layout includes marketing navbar (logo, nav links, "Sign In", "Get Started" buttons)
- [x] Layout includes basic footer placeholder
- [x] Route group does not use app authentication providers
- [x] Typecheck passes

### US-002: Create Hero Section Background and Grid Pattern
**Description:** As a user, I want to see an impressive dark background with grid pattern so the page feels premium and crypto-native.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/HeroBackground.tsx`
- [x] Implement CSS grid pattern overlay (subtle white/5 lines)
- [x] Add radial gradient vignette fading to edges
- [x] Background color uses `--background: #030304`
- [x] Pattern is purely CSS (no images)
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-003: Create Animated 3D Orb Component
**Description:** As a user, I want to see an eye-catching animated orb so the hero section feels dynamic and futuristic.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/AnimatedOrb.tsx`
- [x] Orb is a gradient sphere (orange to gold: #F7931A to #FFD600)
- [x] Three orbital rings spinning at different speeds/angles using CSS keyframes
- [x] Subtle glow effect around orb (orange shadow)
- [x] Orb floats with gentle up/down animation (8s ease-in-out infinite)
- [x] Responsive sizing (smaller on mobile)
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-004: Create Floating Stat Cards Around Orb
**Description:** As a user, I want to see floating stat cards around the orb so I understand the platform's scale at a glance.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/FloatingStatCard.tsx`
- [x] Three cards positioned around orb: "Active Vaults", "Sources Indexed", "Researchers"
- [x] Cards have glass morphism style (`backdrop-blur-lg bg-white/5 border border-white/10`)
- [x] Each card has icon, number, and label
- [x] Cards have staggered bounce animation
- [x] Cards reposition to stack on mobile
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-005: Create Hero Content (Headlines and CTAs)
**Description:** As a user, I want to see compelling headlines and clear CTAs so I understand the value and can take action.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/HeroContent.tsx`
- [x] Headline: "Collaborative Research" on line 1
- [x] "Reimagined" on line 2 with gradient text (`bg-gradient-to-r from-[#F7931A] to-[#FFD600]`)
- [x] Subheadline describing value prop (muted text color)
- [x] "Start Free" button: primary gradient style, links to `/register`
- [x] "Watch Demo" button: outline style with border
- [x] Use Space Grotesk font for headlines
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-006: Create Video Demo Modal
**Description:** As a user, I want to watch a demo video in a modal so I can learn about the product without leaving the page.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/VideoModal.tsx`
- [x] Modal opens when "Watch Demo" is clicked
- [x] Uses Radix Dialog for accessibility
- [x] Dark overlay with backdrop blur
- [x] Embedded video player (YouTube/Vimeo iframe placeholder)
- [x] Close button in top-right corner
- [x] Closes on overlay click or Escape key
- [x] Video pauses when modal closes
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-007: Assemble Complete Hero Section
**Description:** As a developer, I need to combine all hero components into a cohesive section.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/HeroSection.tsx`
- [x] Integrates HeroBackground, AnimatedOrb, FloatingStatCards, HeroContent
- [x] Two-column layout on desktop (content left, orb right)
- [x] Stacked layout on mobile (content top, orb bottom)
- [x] Minimum height of viewport (`min-h-screen`)
- [x] Proper z-index layering
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-008: Create Stats Ticker Section
**Description:** As a user, I want to see impressive platform statistics so I trust the platform's credibility.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/StatsTicker.tsx`
- [x] Horizontal bar with `border-y border-white/10`
- [x] Three stats: "10,000+ Researchers", "50,000+ Sources", "1M+ Citations"
- [x] Each stat has Lucide icon
- [x] Numbers animate counting up when section enters viewport (Framer Motion)
- [x] Stats evenly distributed with flex justify-between
- [x] Stacks to 3 rows on mobile
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-009: Create Feature Card Component
**Description:** As a developer, I need a reusable feature card component for the features grid.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/FeatureCard.tsx`
- [x] Props: icon, title, description
- [x] Card style: `bg-[#0F1115] border border-white/10 rounded-2xl`
- [x] Icon container with orange glow effect
- [x] Large watermark icon in background (opacity-5)
- [x] Watermark reveals more on hover (opacity-10)
- [x] Hover: `-translate-y-1` and `border-[#F7931A]/50`
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-010: Create Features Grid Section
**Description:** As a user, I want to see SyncScript's key features so I understand what the platform offers.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/FeaturesSection.tsx`
- [x] Section heading with gradient text accent
- [x] 3x2 grid of FeatureCards on desktop
- [x] 6 features: Real-time Collaboration, Smart Citations, PDF Annotations, Knowledge Vaults, Team Permissions, AI Insights
- [x] Each feature has appropriate Lucide icon
- [x] Grid becomes 2x3 on tablet, 1x6 on mobile
- [x] Framer Motion stagger animation on scroll
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-011: Create How It Works Timeline Component
**Description:** As a user, I want to see how the platform works in simple steps so I understand the user journey.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/HowItWorksSection.tsx`
- [x] Section heading centered
- [x] Vertical gradient line (orange #F7931A to transparent)
- [x] 3 steps with circular numbered nodes on the line
- [x] Step cards with corner border accents (top-left and bottom-right)
- [x] Steps: 1) Create Vault, 2) Add Sources, 3) Collaborate
- [x] Alternating left/right layout on desktop
- [x] Stacked centered on mobile
- [x] Framer Motion fade-in on scroll
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-012: Create Testimonial Card Component
**Description:** As a developer, I need a testimonial card component for social proof.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/TestimonialCard.tsx`
- [x] Props: avatar, name, title, institution, quote
- [x] Glass morphism style (`backdrop-blur-lg bg-white/5 border border-white/10`)
- [x] Avatar as circular image (48px)
- [x] Quote with quotation marks styling
- [x] Name in white, title and institution in muted
- [x] Subtle hover lift effect
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-013: Create Testimonials Section with Carousel
**Description:** As a user, I want to see what other researchers say so I trust the platform.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/TestimonialsSection.tsx`
- [x] Section heading centered
- [x] Desktop: 3-column static grid showing all testimonials
- [x] Mobile: Horizontal carousel with swipe support
- [x] 3-4 placeholder testimonials with realistic research personas
- [x] Carousel has dot indicators on mobile
- [x] Smooth transition between carousel items
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-014: Create Pricing Card Component
**Description:** As a developer, I need a pricing card component for the pricing section.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/PricingCard.tsx`
- [x] Props: tier name, price, features list, isPopular, ctaLink
- [x] Card style matches design system
- [x] Popular tier: `scale-105`, orange border, "Popular" badge
- [x] Feature list with check icons for included, x icons for excluded
- [x] CTA button links to `/register?plan={tier}`
- [x] Primary gradient button for popular, outline for others
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-015: Create Pricing Section
**Description:** As a user, I want to see pricing options so I can choose the right plan.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/PricingSection.tsx`
- [x] Section heading centered with subtext
- [x] 3 tiers: Free ($0), Pro ($12/mo), Team ($29/mo)
- [x] Pro tier is highlighted as popular (center position)
- [x] Feature comparison appropriate for each tier
- [x] Responsive: stacks on mobile with popular tier first
- [x] Framer Motion scale animation on scroll
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-016: Create CTA Section
**Description:** As a user, I want a final compelling CTA so I'm motivated to sign up.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/CTASection.tsx`
- [x] Full-width gradient background (dark to orange tint)
- [x] Headline: "Start Your Research Journey Today"
- [x] Email input field with "Get Started" button
- [x] Form submits to `/register?email={input}`
- [x] Input style: bottom border, orange on focus
- [x] Button: primary gradient style
- [x] Centered layout with max-width constraint
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-017: Create Marketing Footer
**Description:** As a user, I want a comprehensive footer so I can navigate to other resources.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/Footer.tsx`
- [x] 4-column layout: Product, Resources, Company, Legal
- [x] Product: Features, Pricing, Demo, Changelog
- [x] Resources: Documentation, API, Blog, Help Center
- [x] Company: About, Careers, Contact, Press
- [x] Legal: Privacy, Terms, Security, Cookies
- [x] Social links row with icon buttons (Twitter, GitHub, LinkedIn, Discord)
- [x] Copyright line with dynamic year
- [x] Responsive: 2x2 grid on tablet, stacked on mobile
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-018: Create Marketing Navbar
**Description:** As a user, I want a sticky navbar so I can navigate while scrolling.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/marketing/Navbar.tsx`
- [x] Sticky positioning with backdrop blur on scroll
- [x] Logo on left linking to home
- [x] Nav links: Features, How It Works, Pricing (smooth scroll anchors)
- [x] Right side: "Sign In" text link, "Get Started" gradient button
- [x] Mobile: hamburger menu with slide-out drawer
- [x] Background becomes more opaque on scroll
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-019: Assemble Complete Landing Page
**Description:** As a developer, I need to combine all sections into the final landing page.

**Acceptance Criteria:**
- [x] Update `frontend/src/app/(marketing)/page.tsx`
- [x] Import and render all sections in order: Hero, Stats, Features, HowItWorks, Testimonials, Pricing, CTA
- [x] Add section IDs for smooth scroll navigation (#features, #how-it-works, #pricing)
- [x] Proper spacing between sections (`py-24`)
- [x] Smooth scroll behavior enabled
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-020: Add Framer Motion Scroll Animations
**Description:** As a user, I want smooth reveal animations so the page feels polished and professional.

**Acceptance Criteria:**
- [x] Install framer-motion if not present
- [x] Create `frontend/src/components/marketing/ScrollReveal.tsx` wrapper component
- [x] Fade up animation when elements enter viewport
- [x] Stagger children animation for grids/lists
- [x] Apply to: Features grid, How It Works steps, Testimonials, Pricing cards
- [x] Animations trigger once (not on every scroll)
- [x] Respect reduced motion preferences
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-021: Add SEO Metadata and OG Tags
**Description:** As a marketer, I need proper SEO so the page ranks well and shares nicely on social.

**Acceptance Criteria:**
- [x] Add metadata export to `(marketing)/page.tsx`
- [x] Title: "SyncScript - Collaborative Research Reimagined"
- [x] Description: compelling meta description under 160 chars
- [x] OG image placeholder (1200x630 dimensions noted)
- [x] Twitter card meta tags
- [x] Canonical URL
- [x] Add robots meta allowing indexing
- [x] Typecheck passes

### US-022: Optimize Performance and Lazy Loading
**Description:** As a user, I want fast page loads so I don't bounce before seeing the content.

**Acceptance Criteria:**
- [ ] Lazy load below-fold sections using dynamic imports
- [ ] Add loading="lazy" to any images
- [ ] Testimonial avatars use next/image with proper sizing
- [ ] Preload critical fonts (Space Grotesk, Inter)
- [ ] Verify no layout shift from lazy loaded content
- [ ] Add Suspense boundaries with skeleton fallbacks
- [ ] Typecheck passes
- [ ] Verify Lighthouse performance score 90+

## Non-Goals

- No backend API changes for this PRD
- No actual Stripe payment integration (links to /register with plan param only)
- No CMS integration for testimonials (hardcoded for now)
- No blog or documentation pages (just footer links)
- No A/B testing infrastructure
- No analytics integration (separate PRD)
- No internationalization/localization
- No dark/light mode toggle (always dark)

## Technical Considerations

### Dependencies
- `framer-motion` for scroll animations and complex transitions
- Existing Radix UI components for modal
- Lucide React for icons (already installed)
- next/image for optimized images

### File Structure
```
frontend/src/
├── app/(marketing)/
│   ├── layout.tsx
│   └── page.tsx
└── components/marketing/
    ├── Navbar.tsx
    ├── HeroSection.tsx
    ├── HeroBackground.tsx
    ├── HeroContent.tsx
    ├── AnimatedOrb.tsx
    ├── FloatingStatCard.tsx
    ├── VideoModal.tsx
    ├── StatsTicker.tsx
    ├── FeaturesSection.tsx
    ├── FeatureCard.tsx
    ├── HowItWorksSection.tsx
    ├── TestimonialsSection.tsx
    ├── TestimonialCard.tsx
    ├── PricingSection.tsx
    ├── PricingCard.tsx
    ├── CTASection.tsx
    ├── Footer.tsx
    └── ScrollReveal.tsx
```

### Design System Reference
All components must strictly follow CLAUDE.md design tokens:
- Background: `#030304`
- Surface: `#0F1115`
- Primary: `#F7931A`
- Accent: `#FFD600`
- Fonts: Space Grotesk (headings), Inter (body)

### Animation Guidelines
- Use CSS keyframes for continuous animations (orb spin, float)
- Use Framer Motion for scroll-triggered and interaction animations
- Always check `prefers-reduced-motion` media query
- Keep animations subtle and purposeful
