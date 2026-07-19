"""
Upbeat Attendance Management System — FastAPI Application.
Main entry point for the REST API.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import APP_NAME, APP_VERSION, ALLOWED_ORIGINS, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
from api.database import init_db, close_db, SessionLocal
from api.models import AdminUser, OfficeSettings
from api.security import hash_password

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def seed_defaults():
    """Seed default admin user and office settings on first run."""
    db = SessionLocal()
    try:
        # Seed default admin
        admin = db.query(AdminUser).filter(
            AdminUser.username == DEFAULT_ADMIN_USERNAME
        ).first()
        if not admin:
            admin = AdminUser(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            )
            db.add(admin)
            logger.info(f"Created default admin user: {DEFAULT_ADMIN_USERNAME}")

        # Seed default office settings
        settings = db.query(OfficeSettings).first()
        if not settings:
            settings = OfficeSettings(
                office_start_time="09:00",
                office_end_time="18:00",
                grace_period_minutes=15,
                late_threshold_minutes=30,
                sync_interval_seconds=300,
            )
            db.add(settings)
            logger.info("Created default office settings")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding defaults: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    init_db()
    logger.info("Database tables created")
    seed_defaults()
    logger.info("Default data seeded")

    yield

    # Shutdown
    close_db()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="REST API for the Upbeat Employee Attendance Management System",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from api.routers import attendance, employees, devices, reports, settings, dashboard, auth  # noqa

app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(employees.router)
app.include_router(devices.router)
app.include_router(reports.router)
app.include_router(settings.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def root():
    """API health check endpoint."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": APP_VERSION,
    }
