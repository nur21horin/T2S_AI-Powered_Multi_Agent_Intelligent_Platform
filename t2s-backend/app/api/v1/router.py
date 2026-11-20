from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, evaluations, health, profiles, progress, rooms, submissions, tasks, projects, teams, hackathons

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(profiles.router)
api_router.include_router(rooms.router)
api_router.include_router(tasks.router)
api_router.include_router(submissions.router)
api_router.include_router(evaluations.router)
api_router.include_router(progress.router)
api_router.include_router(projects.router)
api_router.include_router(teams.router)
api_router.include_router(hackathons.router)
api_router.include_router(hackathons.registrations_router)
