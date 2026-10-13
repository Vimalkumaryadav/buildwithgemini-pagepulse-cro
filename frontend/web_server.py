"""Unified Production Web Server & CRO Auditor for PagePulse:
'Landing pages that pay for themselves'.

Features:
1. Direct REST Audit Endpoint (/api/audit)
2. Interactive A2UI Agent Chat Endpoint (/api/chat) that talks directly to our ADK Agent
   and returns native A2UI cards + text responses.
3. Clean Web UI rendering on port 8080.
"""

import os
import sys
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Add cro-agent app to sys.path
sys.path.insert(0, "/config/Desktop/BuildWithGemini/cro-agent")
from app.cro_tools import deep_crawl_and_extract_landing_page, calculate_cro_revenue_lift
from app.agent import root_agent

app = FastAPI(title="PagePulse - CRO Landing Page Auditor & A2UI Agent")

class AuditRequest(BaseModel):
    url: str
    monthly_visitors: Optional[int] = 10000
    current_cr_pct: Optional[float] = 1.5
    projected_cr_pct: Optional[float] = 3.0
    aov_usd: Optional[float] = 100.0

class ChatRequest(BaseModel):
    message: str

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

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        # Run query directly through ADK Runner with in-memory session
        runner = Runner(
            agent=root_agent,
            session_service=InMemorySessionService(),
            app_name="pagepulse"
        )
        session = await runner.session_service.create_session(app_name="pagepulse", user_id="web-user")
        
        reply_texts = []
        a2ui_messages = []

        async for event in runner.run_async(
            session_id=session.id,
            user_id="web-user",
            new_message=types.Content(role="user", parts=[types.Part(text=msg)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        reply_texts.append(part.text)
                    elif getattr(part, "inline_data", None):
                        # A2UI rewrapped blob from a2ui_callback
                        import base64
                        raw = base64.b64decode(part.inline_data.data).decode("utf-8")
                        # Extract inner json
                        import re
                        m = re.search(r"<a2a_datapart_json>(.*?)</a2a_datapart_json>", raw)
                        if m:
                            try:
                                pkg = json.loads(m.group(1))
                                if "data" in pkg:
                                    a2ui_messages.append(pkg["data"])
                            except Exception:
                                pass

        parts = []
        for t in reply_texts:
            parts.append({"kind": "text", "text": t})
        for a in a2ui_messages:
            parts.append({"kind": "a2ui", "data": a})

        if not parts:
            parts.append({"kind": "text", "text": "Audit complete."})

        return {"parts": parts}
    except Exception as e:
        return {"parts": [{"kind": "text", "text": f"Agent query error: {str(e)}"}]}

# Mount static files for web UI
app.mount("/", StaticFiles(directory="/config/Desktop/BuildWithGemini/frontend/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
