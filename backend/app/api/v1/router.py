"""V1 API Router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    anomalies,
    auth,
    behavior,
    chat,
    dashboard,
    forecast,
    goals,
    health,
    simulation,
    transactions,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(users.router)
api_router.include_router(transactions.router)
api_router.include_router(goals.router)
api_router.include_router(dashboard.router)
api_router.include_router(behavior.router)
api_router.include_router(anomalies.router)
api_router.include_router(forecast.router)
api_router.include_router(simulation.router)
api_router.include_router(chat.router)
