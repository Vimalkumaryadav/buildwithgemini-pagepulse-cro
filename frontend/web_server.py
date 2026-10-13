"""Standalone Web Server & CRO Auditor for PagePulse: 'Landing pages that pay for themselves'.
Provides both direct REST audit endpoints with live URL extraction & heuristic scoring,
and integrates with the ADK agent.
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import Optional

# Add cro-agent app to sys.path so we can reuse CRO tools directly
sys.path.insert(0, "/config/Desktop/BuildWithGemini/cro-agent")
from app.cro_tools import deep_crawl_and_extract_landing_page, calculate_cro_revenue_lift

app = FastAPI(title="PagePulse - CRO Landing Page Auditor")

class AuditRequest(BaseModel):
    url: str
    monthly_visitors: Optional[int] = 10000
    current_cr_pct: Optional[float] = 1.5
    projected_cr_pct: Optional[float] = 3.0
    aov_usd: Optional[float] = 100.0

@app.post("/api/audit")
async def audit_endpoint(req: AuditRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
    
    # 1. Fetch & extract page data using the deep crawler
    extracted_summary = deep_crawl_and_extract_landing_page(url)
    
    # 2. Calculate projected financial lift
    lift_summary = calculate_cro_revenue_lift(
        monthly_visitors=req.monthly_visitors or 10000,
        current_conversion_rate_pct=req.current_cr_pct or 1.5,
        projected_conversion_rate_pct=req.projected_cr_pct or 3.0,
        average_order_value_usd=req.aov_usd or 100.0
    )
    
    return {
        "url": url,
        "extracted_summary": extracted_summary,
        "revenue_lift": lift_summary,
        "moto": "Landing pages that pay for themselves"
    }

# Mount static files for web UI
app.mount("/", StaticFiles(directory="/config/Desktop/BuildWithGemini/frontend/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
