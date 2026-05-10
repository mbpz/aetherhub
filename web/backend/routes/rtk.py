"""
RTK Token Savings Analytics Routes
"""
import json
import subprocess
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_db

router = APIRouter(prefix="/rtk", tags=["rtk"])

def ok(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}

@router.get("/analytics")
async def get_rtk_analytics():
    """
    Get RTK token savings analytics.
    Calls 'rtk gain --format json --all' and returns structured data.
    """
    try:
        result = subprocess.run(
            ['/opt/homebrew/bin/rtk', 'gain', '--format', 'json', '--all'],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return ok(data)
        else:
            return {"code": 5001, "message": "RTK command failed", "data": None}
    except FileNotFoundError:
        return {"code": 5002, "message": "RTK not found at /opt/homebrew/bin/rtk", "data": None}
    except json.JSONDecodeError:
        return {"code": 5003, "message": "Failed to parse RTK output", "data": None}
    except Exception as e:
        return {"code": 5004, "message": str(e), "data": None}

@router.get("/discover")
async def discover_missed_opportunities():
    """
    Get RTK discovered missed opportunities.
    Calls 'rtk discover --format json' and returns suggestions.
    """
    try:
        result = subprocess.run(
            ['/opt/homebrew/bin/rtk', 'discover', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return ok(data)
        else:
            return {"code": 5001, "message": "RTK discover failed", "data": None}
    except FileNotFoundError:
        return {"code": 5002, "message": "RTK not found", "data": None}
    except Exception as e:
        return {"code": 5004, "message": str(e), "data": None}