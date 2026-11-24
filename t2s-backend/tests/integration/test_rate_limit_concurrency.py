from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from redis import Redis
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.security.passwords import hash_password
from app.security.rate_limit import RateLimitRule, consume_rate_limit, consume_rate_limits
from app.services.user_service import UserService


def _independent_clients(test_redis, count=2):
    connection_kwargs = dict(test_redis.client.connection_pool.connection_kwargs)
    connection_kwargs.update(
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    return [Redis(**connection_kwargs) for _ in range(count)]


def test_concurrent_single_key_requests_have_no_lost_increments(test_redis):
    clients = _independent_clients(test_redis)
    key = test_redis.owned_rate_limit_key()
    calls = 24
    barrier = Barrier(calls)

    def consume(index):
        barrier.wait(timeout=10)
        return consume_rate_limit(
            clients[index % len(clients)], key=key, limit=calls, window_seconds=60
        )

    try:
        with ThreadPoolExecutor(max_workers=calls) as executor:
            results = list(executor.map(consume, range(calls), timeout=20))
        assert all(result.allowed for result in results)
        assert test_redis.client.get(key) == str(calls)
        assert 0 < test_redis.client.pttl(key) <= 60_000
    finally:
        for client in clients:
            client.close()


def test_concurrent_boundary_enforces_exact_single_key_limit(test_redis):
    clients = _independent_clients(test_redis)
    key = test_redis.owned_rate_limit_key()
    calls = 32
    limit = 11
    barrier = Barrier(calls)

    def consume(index):
        barrier.wait(timeout=10)
        return consume_rate_limit(
            clients[index % len(clients)], key=key, limit=limit, window_seconds=60
        )

    try:
        with ThreadPoolExecutor(max_workers=calls) as executor:
            results = list(executor.map(consume, range(calls), timeout=20))
        assert sum(result.allowed for result in results) == limit
        assert all(result.remaining == 0 for result in results if not result.allowed)
        assert test_redis.client.get(key) == str(calls)
        assert 0 < test_redis.client.pttl(key) <= 60_000
    finally:
        for client in clients:
            client.close()


def test_concurrent_multi_key_requests_share_state_and_preserve_ttls(test_redis):
    clients = _independent_clients(test_redis)
    email_key = test_redis.owned_rate_limit_key()
    ip_key = test_redis.owned_rate_limit_key()
    rules = (RateLimitRule(email_key, 30, 60), RateLimitRule(ip_key, 30, 60))
    assert test_redis.client.set(email_key, "0", px=20_000)
    assert test_redis.client.set(ip_key, "0", px=25_000)
    before = {
        email_key: test_redis.client.pttl(email_key),
        ip_key: test_redis.client.pttl(ip_key),
    }
    calls = 16
    barrier = Barrier(calls)

    def consume(index):
        barrier.wait(timeout=10)
        return consume_rate_limits(clients[index % len(clients)], rules=rules)

    try:
        with ThreadPoolExecutor(max_workers=calls) as executor:
            results = list(executor.map(consume, range(calls), timeout=20))
        assert all(result.allowed for result in results)
        assert test_redis.client.get(email_key) == str(calls)
        assert test_redis.client.get(ip_key) == str(calls)
        for key, original_ttl in before.items():
            ttl = test_redis.client.pttl(key)
            assert 0 < ttl <= original_ttl
    finally:
        for client in clients:
            client.close()


def test_concurrent_opposite_admin_demotions_leave_an_active_admin(test_database_url):
    """The shared transaction lock and actor recheck serialize role changes."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    engine = create_engine(test_database_url, poolclass=NullPool)
    emails = [f"admin-race-{uuid4().hex}@example.com" for _ in range(2)]
    try:
        with Session(engine) as db:
            actors = [
                User(
                    email=email,
                    full_name="Concurrent Admin Test",
                    password_hash=hash_password("concurrent-test-password-123"),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )
                for email in emails
            ]
            db.add_all(actors)
            db.commit()
            ids = [user.id for user in actors]

        barrier = Barrier(2)

        def demote(actor_id, target_id):
            with Session(engine) as db:
                barrier.wait(timeout=10)
                try:
                    UserService(db).assign_role(actor_id, target_id, UserRole.STUDENT)
                    return "changed"
                except ForbiddenError:
                    return "actor-no-longer-admin"

        pairs = [(ids[0], ids[1]), (ids[1], ids[0])]
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda pair: demote(*pair), pairs, timeout=20))

        assert sorted(outcomes) == ["actor-no-longer-admin", "changed"]
        with Session(engine) as db:
            remaining_roles = db.scalars(select(User.role).where(User.id.in_(ids))).all()
            assert remaining_roles.count(UserRole.ADMIN) == 1
            assert remaining_roles.count(UserRole.STUDENT) == 1
    finally:
        with Session(engine) as db, db.begin():
            user_ids = select(User.id).where(User.email.in_(emails))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        engine.dispose()
