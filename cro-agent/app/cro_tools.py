import re
import urllib.parse
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup


def deep_crawl_and_extract_landing_page(url: str) -> str:
    """Performs deep extraction of a website's landing page and linked product/pricing pages.
    Extracts business model signals, product catalog/features, value propositions, pricing tiers,
    CTAs, social proof elements, customer testimonials, and friction points.

    Args:
        url: The website URL to research and audit (e.g. 'https://stripe.com' or 'example.com')

    Returns:
        Structured research data on the business, products, pricing, and page elements.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        with httpx.Client(timeout=14.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html = resp.text
            final_url = str(resp.url)
    except Exception as e:
        return f"Direct fetch error for {url} ({str(e)}). Proceeding with domain and contextual analysis."

    soup = BeautifulSoup(html, "html.parser")

    # Clean scripts, styles, svg
    for tag in soup(["script", "style", "svg", "noscript", "iframe"]):
        tag.decompose()

    # Meta & Title
    title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    # Headlines
    h1s = [h.get_text(" ", strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)][:4]
    h2s = [h.get_text(" ", strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)][:8]
    h3s = [h.get_text(" ", strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)][:8]

    # Discover navigation & product categories
    nav_links = []
    product_keywords = ["product", "feature", "solution", "pricing", "plan", "service", "case-study", "integrat"]
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        text = a.get_text(" ", strip=True)
        if not text or len(text) > 35:
            continue
        if any(pk in href.lower() or pk in text.lower() for pk in product_keywords):
            full_href = urllib.parse.urljoin(final_url, href)
            nav_links.append(f"{text} ({full_href})")
        if len(nav_links) >= 10:
            break

    # CTAs (Call to Actions)
    cta_candidates = []
    for el in soup.find_all(["button", "a"]):
        text = el.get_text(" ", strip=True)
        if not text or len(text) > 40:
            continue
        classes = " ".join(el.get("class", []))
        is_btn = el.name == "button" or any(c in classes.lower() for c in ["btn", "button", "cta", "primary"])
        triggers = ["start", "try", "buy", "get", "sign", "join", "book", "demo", "free", "order", "subscribe", "pricing", "talk", "quote", "shop"]
        if is_btn or any(t in text.lower() for t in triggers):
            if text not in cta_candidates:
                cta_candidates.append(text)
        if len(cta_candidates) >= 8:
            break

    # Social Proof & Authority Signals
    body_text = soup.get_text(" ", strip=True)
    social_proof_elements = []
    proof_regex = [
        r"(\d+(\.\d+)?\s*(/\s*5|\s*stars|\s*rating))",
        r"(\d+([,\.]\d+)?(\+)?\s*(customers|teams|users|clients|companies|brands|businesses|founders))",
        r"(trusted by|backed by|as seen in|featured in|g2|capterra|soc2|hipaa|gdpr|money[- ]back guarantee|cancel anytime)",
    ]
    for pattern in proof_regex:
        matches = re.findall(pattern, body_text, re.IGNORECASE)
        for m in matches:
            val = m[0] if isinstance(m, tuple) else m
            if val and val.strip() not in social_proof_elements:
                social_proof_elements.append(val.strip())

    # Pricing indicators
    pricing_matches = re.findall(r"(\$\s*\d+([,\.]\d+)?(\s*/\s*(mo|month|yr|year|user|seat))?)", body_text, re.IGNORECASE)
    pricing_found = list(set([p[0] for p in pricing_matches[:6]])) if pricing_matches else []

    # Form Fields & Friction Analysis
    forms = soup.find_all("form")
    input_fields = [inp.get("type", "text") for inp in soup.find_all("input") if inp.get("type") not in ("hidden", "submit")]

    # Sample paragraphs (first 6 substantive paragraphs)
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30][:6]

    structured_data = [
        f"=== DEEP PRODUCT & CRO RESEARCH FOR: {final_url} ===",
        f"Page Title: {title}",
        f"Meta Description: {meta_desc or 'None provided'}",
        f"Primary H1 Headlines: {' | '.join(h1s) if h1s else 'No H1 tags found'}",
        f"Subheadings (H2): {' | '.join(h2s[:5]) if h2s else 'None found'}",
        f"Feature Highlights (H3): {' | '.join(h3s[:5]) if h3s else 'None found'}",
        f"Discovered Product/Pricing Navigation: {', '.join(nav_links[:8]) if nav_links else 'None found'}",
        f"Detected Pricing / Plans: {', '.join(pricing_found) if pricing_found else 'No explicit pricing listed on landing page'}",
        f"Primary CTAs: {', '.join(cta_candidates) if cta_candidates else 'No explicit CTAs found'}",
        f"Detected Social Proof / Trust Signals: {', '.join(social_proof_elements[:8]) if social_proof_elements else 'No clear social proof detected'}",
        f"Forms & Inputs (Friction): {len(forms)} form(s), visible fields: {len(input_fields)} ({', '.join(input_fields[:6])})",
        f"Sample Core Copy:\n- " + "\n- ".join(paragraphs[:4]) if paragraphs else "Sample Core Copy: Sparse body text",
        f"Word Count: ~{len(body_text.split())} words",
    ]

    return "\n".join(structured_data)


def calculate_cro_revenue_lift(
    monthly_visitors: int,
    current_conversion_rate_pct: float,
    projected_conversion_rate_pct: float,
    average_order_value_usd: float,
) -> str:
    """Calculates the financial revenue lift and ROI of optimizing the landing page conversion rate.
    Emphasizes the core moto: 'Landing pages that pay for themselves'.

    Args:
        monthly_visitors: Number of unique monthly visitors hitting the landing page.
        current_conversion_rate_pct: Current conversion rate in percent (e.g. 1.5 for 1.5%).
        projected_conversion_rate_pct: Target conversion rate after CRO improvements (e.g. 3.0 for 3.0%).
        average_order_value_usd: Average revenue per conversion/customer in USD (e.g. 120.0).

    Returns:
        A detailed breakdown of monthly conversions, additional monthly revenue, annual revenue lift, and ROI.
    """
    curr_rate = max(current_conversion_rate_pct / 100.0, 0.0001)
    target_rate = max(projected_conversion_rate_pct / 100.0, curr_rate)

    curr_conversions = monthly_visitors * curr_rate
    target_conversions = monthly_visitors * target_rate
    lift_conversions = target_conversions - curr_conversions

    curr_monthly_rev = curr_conversions * average_order_value_usd
    target_monthly_rev = target_conversions * average_order_value_usd
    monthly_rev_lift = target_monthly_rev - curr_monthly_rev
    annual_rev_lift = monthly_rev_lift * 12

    pct_lift = ((target_rate - curr_rate) / curr_rate) * 100

    report = (
        f"--- CRO REVENUE IMPACT PROJECTION ---\n"
        f"Monthly Traffic: {monthly_visitors:,} visitors\n"
        f"Average Deal / Order Value: ${average_order_value_usd:,.2f}\n"
        f"Current Conversion Rate: {current_conversion_rate_pct:.2f}% ({int(curr_conversions):,} conversions/mo -> ${curr_monthly_rev:,.2f}/mo)\n"
        f"Projected Conversion Rate: {projected_conversion_rate_pct:.2f}% ({int(target_conversions):,} conversions/mo -> ${target_monthly_rev:,.2f}/mo)\n"
        f"Conversion Rate Relative Lift: +{pct_lift:.1f}%\n"
        f"Net Additional Monthly Conversions: +{int(lift_conversions):,} customers/mo\n"
        f"★ Net Additional Monthly Revenue: +${monthly_rev_lift:,.2f}\n"
        f"★ Projected Annual Revenue Gain: +${annual_rev_lift:,.2f}\n"
        f"Moto: 'Landing pages that pay for themselves' — this proves the exact ROI of addressing friction points."
    )
    return report
