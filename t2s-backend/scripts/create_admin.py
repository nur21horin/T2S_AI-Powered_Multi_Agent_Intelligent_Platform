"""One-time interactive bootstrap for the first platform administrator."""
from getpass import getpass
import sys
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import setup_logging
from app.db.session import create_db_engine
from app.schemas.auth import RegisterRequest
from app.services.user_service import UserService


def bootstrap_admin_interactively(
    settings: Settings,
    *,
    input_fn: Callable[[str], str] | None = None,
    password_fn: Callable[[str], str] | None = None,
) -> UUID:
    if not settings.admin_bootstrap_enabled:
        raise RuntimeError("ADMIN_BOOTSTRAP_ENABLED must be true for initial setup.")
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required for administrator bootstrap.")

    input_prompt = input if input_fn is None else input_fn
    read_password = getpass if password_fn is None else password_fn
    email = input_prompt("Administrator email: ")
    full_name = input_prompt("Administrator full name: ")
    password = read_password("Administrator password: ")
    confirmation = read_password("Confirm administrator password: ")
    if password != confirmation:
        raise ValueError("The entered passwords do not match.")
    request = RegisterRequest(email=email, full_name=full_name, password=password)

    engine = create_db_engine(settings)
    try:
        with Session(engine) as db:
            user = UserService(db).bootstrap_initial_admin(request)
            return user.id
    finally:
        engine.dispose()


def main(
    *,
    input_fn: Callable[[str], str] | None = None,
    password_fn: Callable[[str], str] | None = None,
) -> int:
    if len(sys.argv) != 1:
        print("This command accepts no arguments; enter credentials only at the prompts.")
        return 2
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        print("Run administrator bootstrap from an interactive terminal.")
        return 2
    settings = Settings()
    setup_logging(settings.log_level)
    try:
        admin_id = bootstrap_admin_interactively(
            settings, input_fn=input_fn, password_fn=password_fn
        )
    except Exception:
        # Do not print validation objects, DB errors, email input, or secrets.
        print("Administrator bootstrap failed; review configuration and database state.")
        return 1
    print(f"Initial administrator created (user id: {admin_id}).")
    print("Disable ADMIN_BOOTSTRAP_ENABLED after setup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
