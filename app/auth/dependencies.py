"""Resolve reviewer identity exclusively from an authenticated browser cookie."""
from fastapi import Request, HTTPException
from app.contracts.common import Principal
from app.auth.github import AuthDenied

async def require_reviewer(request: Request) -> Principal:
    services=request.app.state.services
    cookie=request.cookies.get('finance_session','')
    if request.method not in {'GET','HEAD','OPTIONS'}:
        if (request.headers.getlist('origin') != ['http://127.0.0.1:8765']
                or not services.sessions.verify_csrf(cookie,request.headers.get('x-csrf-token',''))):
            raise HTTPException(403, 'csrf_required')
    try:
        return services.sessions.require(cookie,services.clock())
    except AuthDenied:
        raise HTTPException(401,'authentication_required') from None
