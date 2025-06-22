from typing import Any, Dict
from fastapi.responses import JSONResponse

from decimal import Decimal

from datetime import datetime

def success_response(data: Any = None, message: str = "Success") -> JSONResponse:
    print("success response", data, message)
    if isinstance(data, list):
        data = [{**{k: float(v) if isinstance(v, Decimal) else v.isoformat() if isinstance(v, datetime) else v for k, v in item.items()}, 
                'created_at': item['created_at'].isoformat() if 'created_at' in item else None} for item in data]
    response = {
        "status_code": 200,
        "status": "success",
        "message": message,
        "data": data
    }
    return response

def error_response(message: str, status_code: int = 400, data: Any = None) -> JSONResponse:
    print("error from response file", message, status_code)
    if isinstance(message, list):
        message = [{**item, 'created_at': item['created_at'].isoformat() if 'created_at' in item else None} for item in message]
    response = {
        "status": "error",
        "message": message,
        "data": data
    }
    return JSONResponse(content=response, status_code=status_code)