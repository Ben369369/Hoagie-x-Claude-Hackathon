#!/usr/bin/env python3
"""
MCP Scanner API - Minimal Version for Hackathon
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scanner.mcp_scanner import MCPScanner
from utils.email_sender import EmailSender
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MCP Security Scanner API")

# CORS - Allow front-end to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    config_path: str = "configs/poisoned_config.json"


class AttackRequest(BaseModel):
    target_email: Optional[str] = None


@app.get("/")
async def root():
    """API root"""
    return {
        "message": "MCP Security Scanner API",
        "version": "1.0.0",
        "endpoints": {
            "scan": "POST /api/scan",
            "attack_demo": "POST /api/demo/attack",
            "health": "GET /api/health"
        }
    }


@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/api/scan")
async def scan_config(request: ScanRequest):
    """
    Scan an MCP configuration file

    Example:
    POST /api/scan
    { "config_path": "configs/poisoned_config.json" }
    """
    try:
        # Run scanner
        scanner = MCPScanner(request.config_path)

        if not scanner.load_config():
            return {"status": "error", "message": "Failed to load config"}

        scanner.scan()
        summary = scanner.get_summary()

        # Build response
        servers_data = []
        for result in scanner.results:
            servers_data.append({
                "server": result.server_name,
                "tool": result.tool_name,
                "risk_level": result.risk_level,
                "risk_score": result.risk_score,
                "vulnerabilities": [
                    {
                        "type": v["rule"],
                        "severity": v["severity"].value,
                        "description": v["description"],
                        "recommendation": v["recommendation"]
                    }
                    for v in result.vulnerabilities
                ]
            })

        return {
            "status": "success",
            "config": request.config_path,
            "summary": {
                "total_servers": summary["total_servers"],
                "total_tools": summary["total_tools"],
                "critical": summary["critical"],
                "high": summary["high"],
                "medium": summary["medium"],
                "low": summary["low"],
                "safe": summary["safe"]
            },
            "results": servers_data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/api/demo/attack")
async def run_attack_demo(request: AttackRequest):
    """
    Run the email hijacking attack demo

    Example:
    POST /api/demo/attack
    { "target_email": "bob@example.com" }
    """
    try:
        sender = EmailSender()
        attacker_email = os.getenv("ATTACKER_EMAIL")

        target = request.target_email or attacker_email

        # Send hijacked email
        result = sender.send_email_with_hijack(
            to=target,
            subject="Demo: Project Meeting (Hijacked)",
            body="This email demonstrates the BCC hijacking attack.\n\nConfidential project information would be here..."
        )

        if result["status"] == "success":
            return {
                "status": "success",
                "attack_type": "email_hijacking",
                "timeline": [
                    {
                        "step": 1,
                        "event": "User sends email",
                        "description": f"Email to {target}"
                    },
                    {
                        "step": 2,
                        "event": "MCP tool activated",
                        "description": "Malicious send_email tool invoked"
                    },
                    {
                        "step": 3,
                        "event": "Hidden BCC added",
                        "description": f"Secret copy to {attacker_email}"
                    },
                    {
                        "step": 4,
                        "event": "Attack successful",
                        "description": "Attacker received email copy"
                    }
                ],
                "victim_sees": f"Email sent to {target}",
                "reality": f"Email also sent to {attacker_email}",
                "attacker_email": attacker_email
            }
        else:
            return {
                "status": "error",
                "message": result.get("message", "Attack failed")
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/configs")
async def list_configs():
    """List available configuration files"""
    return {
        "configs": [
            {
                "name": "Poisoned Configuration",
                "path": "configs/poisoned_config.json",
                "description": "Malicious MCP server with hidden instructions",
                "expected_risk": "CRITICAL"
            },
            {
                "name": "Clean Configuration",
                "path": "configs/clean_config.json",
                "description": "Safe MCP configuration",
                "expected_risk": "SAFE"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("\n Starting MCP Scanner API...")
    print(" API will be available at: http://localhost:8000")
    print(" Docs available at: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)