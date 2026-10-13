import re
import urllib.parse
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup


def fetch_and_extract_landing_page(url: str) -> str:
    """Fetches a landing page URL and extracts critical CRO components such as
    the page title, meta description, headline tags (H1, H2), call-to-action buttons/links,
    social proof indicators, and form inputs.

    Args:
        url: The full landing page URL (e.g. 'https://stripe.com' or 'example.com')

    Returns:
        A structured breakdown of the page's copy, CTAs, and structure.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        with httpx.Client(timeout=12.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        return f"Unable to fetch URL {url} directly ({str(e)}). Proceeding with domain heuristic audit based on url: {url}."

    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, svg, noscript tags
    for tag in soup(["script", "style", "svg", "noscript", "iframe"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)][:3]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)][:5]

    # CTAs: Look for buttons and high-intent links
    cta_texts = []
    for btn in soup.find_all(["button", "a"]):
        classes = " ".join(btn.get("class", []))
        text = btn.get_text(strip=True)
        if not text or len(text) > 40:
            continue
        # Check if button or CTA-like link
        is_button = btn.name == "button" or any(kw in classes.lower() for kw in ["btn", "cta", "button", "primary"])
        keywords = ["start", "get", "try", "buy", "sign", "join", "book", "demo", "free", "order", "subscribe", "pricing", "download"]
        if is_button or any(kw in text.lower() for kw in keywords):
            if text not in cta_texts:
                cta_texts.append(text)
        if len(cta_texts) >= 6:
            break

    # Social Proof: testimonials, logos, ratings, reviews
    social_proof_hits = []
    text_content = soup.get_text(separator=" ", strip=True)
    patterns = [
        r"(\d+(\.\d+)?\s*(/\s*5|stars|rating))",
        r"(\d+([,\.]\d+)?(\+)?\s*(customers|teams|users|companies|businesses|founders))",
        r"(trusted by|as featured in|reviews|money[- ]back guarantee)",
    ]
    for p in patterns:
        matches = re.findall(p, text_content, re.IGNORECASE)
        for m in matches:
            val = m[0] if isinstance(m, tuple) else m
            if val and val.strip() not in social_proof_hits:
                social_proof_hits.append(val.strip())

    # Form Fields
    forms = soup.find_all("form")
    form_count = len(forms)
    inputs = [inp.get("type", "text") for inp in soup.find_all("input") if inp.get("type") not in ("hidden", "submit")]

    result = [
        f"--- LANDING PAGE AUDIT DATA: {url} ---",
        f"Page Title: {title}",
        f"Meta Description: {meta_desc or 'None found'}",
        f"H1 Headlines: {', '.join(h1s) if h1s else 'No H1 tags found'}",
        f"H2 Subheadings: {', '.join(h2s[:4]) if h2s else 'None found'}",
        f"Primary CTAs: {', '.join(cta_texts) if cta_texts else 'No clear CTAs found'}",
        f"Detected Social Proof / Numbers: {', '.join(social_proof_hits[:5]) if social_proof_hits else 'Minimal or none detected'}",
        f"Forms: {form_count} form(s) found, visible input fields: {len(inputs)} ({', '.join(inputs[:6])})",
        f"Rough text length: ~{len(text_content.split())} words",
    ]

    return "\n".join(result)


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
        current_conversion_rate_pct: Current conversion rate in percent (e.g. 1.8 for 1.8%).
        projected_conversion_rate_pct: Target conversion rate after CRO improvements (e.g. 3.2 for 3.2%).
        average_order_value_usd: Average revenue per conversion/sale/customer deal in USD (e.g. 85.0).

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
    monthly_rev_lift = target_conversions * average_order_value_usd - curr_monthly_rev
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
        f"Moto: This demonstrates how a high-converting landing page literally pays for itself many times over."
    )
    return report
