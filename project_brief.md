# My agent: PagePulse (Landing Pages that Pay for Themselves)
One-liner: A conversational CRO agent that audits landing page URLs against battle-tested conversion heuristics, delivers an actionable CRO score breakdown, calculates revenue impact & ROI lift, and produces A2UI scorecard cards and wireframe visual mockups.

Moto: "Landing pages that pay for themselves"

Tool coverage:
- Memory: Remembers client industry/niche, target audience, conversion goals (SaaS trial, lead gen, e-commerce checkout), historical audit scores, and baseline conversion metrics.
- Tools:
  - `fetch_landing_page`: Scrapes and extracts copy, hero headline, value props, CTAs, social proof elements, form fields, and page structure.
  - `audit_cro_factors`: Analyzes 5 core CRO dimensions (Value Proposition & Clarity, Friction & Cognitive Load, Visual Hierarchy & CTA Prominence, Trust & Social Proof, Urgency & Risk Reversal) to produce scores (0-100) and weighted overall conversion index.
  - `calculate_conversion_lift`: Projects financial ROI and revenue upside using traffic, average order value/deal size, current conversion rate vs optimized conversion rate in a sandbox/math calculator.
  - `generate_high_converting_hero_copy`: Generates high-converting A/B copy variants (headlines, subheadlines, CTA button labels).
- Catalog/UI: Renders structured A2UI cards for CRO Audit Scorecard, conversion leaks breakdown, and A/B test recommendation checklist.
- Image gen: Generates optimized visual mockup ideas for high-converting hero sections (`gemini-3.1-flash-lite-image` / Imagen).
- Sandbox: Code sandbox / python calculation for conversion revenue impact modeling (e.g. "If monthly visitors = 50,000, AOV = $120, conversion rate lifts from 1.8% to 3.2% -> Net additional monthly revenue = $84,000").

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for CRO financial lift calculator, A2UI interactive scorecards, automated hero visual redesign.
