# UX STRATEGIC REPORT: GreenCycle.de

## Executive Summary

GreenCycle.de serves as a primary touchpoint for the Schwarz Gruppe's environmental services. While the site effectively communicates its core mission—sustainability as a business foundation—it suffers from significant UX debt that hinders professional user engagement and conversion (inquiry) rates.

### Top 3 UX Risks:
1. **Aggressive Compliance Barriers:** The cookie banner (OneTrust) creates a literal wall that prevents immediate content scanning, alienating fast-paced professional users like Oscar.
2. **Task-Site Mismatch (The 'Phantom' Shop):** The lack of a clear product catalog or e-commerce capability for "sustainable products" mentioned in user tasks leads to profound frustration and trust erosion.
3. **Information Fragmentation:** Critical contact information and availability are scattered, requiring multiple clicks to locate basic service hours.

### Top 3 Opportunities:
1. **Integrated Service Catalog:** Transition from static "Tätigkeitsfelder" descriptions to an interactive, inquiry-driven product/service catalog.
2. **Streamlined Accessibility:** Optimize the compliance-to-content flow, reducing the "OneTrust wall" effect.
3. **Trust-Action Alignment:** Place certificates and mission statements directly alongside inquiry forms to reinforce trust at the point of decision.

**Expected impact if unresolved:** Continued brand dilution, high bounce rates from mobile/professional users, and lost lead generation opportunities to more agile competitors.

---

## Persona as Decision Instrument: Oscar

| Persona Need | Site Provides | Result |
|--------------|---------------|--------|
| Detail-oriented sustainability specs | High-level mission text | Skepticism |
| Fast-paced navigation | Blocking cookie banners | Frustration |
| Quality over cost alignment | Hidden certifications (footer/PDF) | Trust lag |

---

## Task Journey Highlights

Oscar's journey was characterized by initial friction and subsequent "content hunting."

- **The Wall:** Immediate encounter with the OneTrust banner. Oscar: *"I just wanted to check their mission, not sign a treaty."*
- **Search Struggles:** Using the search bar for "recycled materials" resulted in generic page results rather than specific material lists.
- **The B2B Realization:** Oscar expected a product catalog for "sustainable design products" but found a B2B service overview. This misalignment is the biggest conversion barrier.

---

## UX Failure Map

| Area | Design Issue | User Impact | Business Impact | Severity |
|------|--------------|-------------|-----------------|----------|
| Onboarding | Intrusive Cookie Banner | Blocked scanning | High bounce rate | High |
| Product | No direct catalog | Choice paralysis | Lost lead gen | Critical |
| Navigation | Nested contact info | Information lag | Increased support load | Medium |
| Trust | Certificates as PDFs only | "Homework" for user | Trust erosion | Medium |

---

## Evidence-Based UX Diagnosis

### 1. The Onboarding Barrier
- **Screenshot reference:** `screenshots/homepage.png` (OneTrust banner)
- **UX principle violated:** Low Barrier to Entry / Goal Gradient Effect
- **Persona reaction:** *"I'm in a hurry. Why is this grey box asking for my life story before I even see the logo?"*
- **Behavioral consequence:** User instinctively clicks 'Accept' without reading or leaves the site.
- **Business risk:** Brand perception as "bureaucratic" rather than "innovative."

### 2. The Missing Product Catalog
- **Screenshot reference:** `screenshots/taetigkeiten.png`
- **UX principle violated:** Match between system and the real world
- **Persona reaction:** *"They talk about products, but I see only paragraphs of text. Where is the 'Add to Project' button?"*
- **Behavioral consequence:** High bounce rate on service pages.
- **Business risk:** Missed opportunities for direct B2B inquiries.

---

## Priority Matrix

| Issue | Effort | Impact | ROI |
|-------|--------|--------|-----|
| Interactive Catalog | High | High | Very High |
| Banner Optimization | Low | Medium | High |
| Trust-Inquiry Alignment | Medium | High | High |

---

## ROI & PRODUCT ECONOMICS

### UX Friction Index

| Dimension | Score /20 |
|---------|-----------|
| Navigation | 12 |
| Content | 14 |
| Trust | 15 |
| Choice | 5 |
| Accessibility | 10 |
| **TOTAL** | **56/100** |

*Scoring Logic: High trust score due to ISO certifications; extremely low choice score due to lack of interactive catalog.*

### Conversion Opportunity Model
Baseline assumptions: 5,000 monthly B2B visitors.
Typical inquiry rate: 0.5%.

| Improvement | Expected Lift |
|------------|---------------|
| Product cards | +1% |
| Story section | +0.2% |
| Checkout flow | +1.5% |

**Projected revenue delta per month:** ~$2,500 - $10,000 (Based on average service contract value).

---

## Visual Strategy (Strategic UX Recommendations)

### Recommended Layout Architecture
```
[ TOP NAV ]
  → Inquiry Cart (Current: Missing)
  → Quick Search

[ HERO SECTION ]
  → Headline: "We Turn Waste into Your Next Resource"
  → Primary CTA: "View Material Catalog"

[ PROBLEM AREA: TÄTIGKEITSFELDER ]
  → Replace text blocks with Component Cards
  → Add "Inquire Now" button to each service
```

### Accessibility & Inclusive Design Snapshot

| WCAG Criteria | Issue Description | User Impact | Severity |
|---------------|-------------------|-------------|----------|
| 1.4.3 Contrast| Light grey text on footer | Vision-impaired users miss links | Medium |
| 2.1.1 Keyboard| OneTrust banner trap | Keyboard users get stuck | Critical |

---

## Strategic Summary

What happens if nothing changes?
GreenCycle will continue to be perceived as a "back-end vendor" for the Schwarz Gruppe rather than a leading "Umweltdienstleister" in the open market. User trust will stagnate as competitors adopt more user-centric, interactive digital experiences.

**This is not a design project. This is a revenue enablement and trust infrastructure initiative.**

---
