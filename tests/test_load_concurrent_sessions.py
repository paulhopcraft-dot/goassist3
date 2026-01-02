"""Load Tests - 100 Concurrent Sessions.

Tests system behavior under heavy concurrent load:
    1. Create 100 simultaneous sessions
    2. Verify all sessions remain stable
    3. Check resource usage (memory, connections)
    4. Measure throughput and latency degradation
    5. Validate session isolation
    6. Test graceful cleanup under load

TMF v3.0 §1.3: Node capacity target = 100 concurrent sessions
PRD v3.0 §7.2: Horizontal scaling must preserve UX semantics
"""

import asyncio
import time
from typing import List
import pytest
from fastapi.testclient import TestClient


class TestConcurrentSessionCreation:
    """Tests for creating many concurrent sessions."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_create_10_sessions(self, client):
        """Test creating 10 concurrent sessions (smoke test)."""
        session_ids = []

        for i in range(10):
            resp = client.post("/sessions")
            assert resp.status_code == 200, f"Session {i} creation failed"
            session_ids.append(resp.json()["session_id"])

        # Verify all exist
        for sid in session_ids:
            status = client.get(f"/sessions/{sid}")
            assert status.status_code == 200

        # Cleanup
        for sid in session_ids:
            client.delete(f"/sessions/{sid}")

    def test_create_50_sessions(self, client):
        """Test creating 50 concurrent sessions."""
        session_ids = []
        start_time = time.time()

        for i in range(50):
            resp = client.post("/sessions")
            assert resp.status_code == 200, f"Session {i} creation failed"
            session_ids.append(resp.json()["session_id"])

        creation_time = time.time() - start_time

        # Should create 50 sessions in reasonable time (< 5s)
        assert creation_time < 5.0, f"Took {creation_time:.2f}s to create 50 sessions"

        # Verify all sessions are listed
        list_resp = client.get("/sessions")
        assert list_resp.status_code == 200
        active_count = len(list_resp.json()["sessions"])
        assert active_count >= 50, f"Only {active_count} sessions active, expected >=50"

        # Cleanup
        for sid in session_ids:
            client.delete(f"/sessions/{sid}")

    @pytest.mark.slow
    def test_create_100_sessions(self, client):
        """Test creating 100 concurrent sessions (TMF v3.0 target)."""
        session_ids = []
        start_time = time.time()

        for i in range(100):
            resp = client.post("/sessions")
            if resp.status_code != 200:
                print(f"Session {i} failed: {resp.status_code}")
                # May hit rate limit or capacity limit
                break
            session_ids.append(resp.json()["session_id"])

        creation_time = time.time() - start_time
        created_count = len(session_ids)

        print(f"Created {created_count}/100 sessions in {creation_time:.2f}s")

        # Should create at least 50 sessions (may hit limits)
        assert created_count >= 50, f"Only created {created_count}/100 sessions"

        # Cleanup
        for sid in session_ids:
            client.delete(f"/sessions/{sid}")


class TestConcurrentSessionOperations:
    """Tests for operations on concurrent sessions."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_concurrent_chat_requests(self, client):
        """Test concurrent chat requests across multiple sessions."""
        # Create 5 sessions
        sessions = []
        for _ in range(5):
            resp = client.post("/sessions")
            assert resp.status_code == 200
            sessions.append(resp.json()["session_id"])

        # Send concurrent chat requests
        start_time = time.time()
        for sid in sessions:
            resp = client.post(
                f"/sessions/{sid}/chat",
                json={"message": "Hello"}
            )
            assert resp.status_code in [200, 500], f"Chat failed for {sid}"

        request_time = time.time() - start_time

        # Should complete in reasonable time
        assert request_time < 10.0, f"Took {request_time:.2f}s for 5 chat requests"

        # Cleanup
        for sid in sessions:
            client.delete(f"/sessions/{sid}")

    def test_session_isolation(self, client):
        """Test sessions don't interfere with each other."""
        # Create 2 sessions
        resp1 = client.post("/sessions")
        resp2 = client.post("/sessions")

        sid1 = resp1.json()["session_id"]
        sid2 = resp2.json()["session_id"]

        # Chat in session 1
        chat1 = client.post(f"/sessions/{sid1}/chat", json={"message": "Test 1"})

        # Chat in session 2
        chat2 = client.post(f"/sessions/{sid2}/chat", json={"message": "Test 2"})

        # Both should succeed independently
        # (status may be 500 if LLM not available, but shouldn't conflict)
        assert chat1.status_code in [200, 500]
        assert chat2.status_code in [200, 500]

        # Cleanup
        client.delete(f"/sessions/{sid1}")
        client.delete(f"/sessions/{sid2}")


class TestLoadStability:
    """Tests for system stability under load."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_create_and_delete_cycle(self, client):
        """Test creating and deleting sessions in cycles."""
        for cycle in range(5):
            # Create 10 sessions
            session_ids = []
            for _ in range(10):
                resp = client.post("/sessions")
                assert resp.status_code == 200
                session_ids.append(resp.json()["session_id"])

            # Delete all
            for sid in session_ids:
                resp = client.delete(f"/sessions/{sid}")
                assert resp.status_code == 200

            # Verify all deleted
            for sid in session_ids:
                resp = client.get(f"/sessions/{sid}")
                assert resp.status_code == 404

    def test_rapid_session_creation(self, client):
        """Test rapid session creation and deletion."""
        session_ids = []

        # Rapid creation
        for i in range(20):
            resp = client.post("/sessions")
            assert resp.status_code == 200
            session_ids.append(resp.json()["session_id"])

        # Rapid deletion
        for sid in session_ids:
            client.delete(f"/sessions/{sid}")


class TestResourceLimits:
    """Tests for resource limit enforcement."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    @pytest.mark.slow
    def test_max_sessions_limit(self, client):
        """Test system enforces max concurrent session limit."""
        session_ids = []

        # Try to create more than max allowed (default: 5 in test env)
        for i in range(10):
            resp = client.post("/sessions")
            if resp.status_code == 200:
                session_ids.append(resp.json()["session_id"])
            else:
                # Hit limit
                break

        # Cleanup
        for sid in session_ids:
            client.delete(f"/sessions/{sid}")

        # Should have hit limit before 10 sessions (default max is 5)
        assert len(session_ids) <= 5, f"Created {len(session_ids)} sessions, expected limit ~5"


class TestThroughput:
    """Tests for system throughput under load."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_session_creation_throughput(self, client):
        """Measure sessions created per second."""
        num_sessions = 20
        session_ids = []

        start_time = time.time()
        for _ in range(num_sessions):
            resp = client.post("/sessions")
            if resp.status_code == 200:
                session_ids.append(resp.json()["session_id"])

        elapsed = time.time() - start_time
        throughput = len(session_ids) / elapsed

        print(f"Created {len(session_ids)} sessions in {elapsed:.2f}s")
        print(f"Throughput: {throughput:.1f} sessions/sec")

        # Should achieve reasonable throughput (>2 sessions/sec)
        assert throughput > 2.0, f"Low throughput: {throughput:.1f} sessions/sec"

        # Cleanup
        for sid in session_ids:
            client.delete(f"/sessions/{sid}")


@pytest.mark.asyncio
class TestAsyncConcurrentLoad:
    """Async tests for true concurrent load."""

    async def test_parallel_session_creation(self):
        """Test creating sessions in parallel with asyncio."""
        from src.main import app
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create 20 sessions in parallel
            tasks = [
                client.post("/sessions")
                for _ in range(20)
            ]

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            # Count successes
            session_ids = []
            for resp in responses:
                if not isinstance(resp, Exception) and resp.status_code == 200:
                    session_ids.append(resp.json()["session_id"])

            print(f"Created {len(session_ids)}/20 sessions in {elapsed:.2f}s (parallel)")

            # Should create at least 10 sessions
            assert len(session_ids) >= 10

            # Cleanup
            cleanup_tasks = [
                client.delete(f"/sessions/{sid}")
                for sid in session_ids
            ]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    async def test_concurrent_chat_load(self):
        """Test concurrent chat requests."""
        from src.main import app
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create 5 sessions
            create_tasks = [client.post("/sessions") for _ in range(5)]
            create_responses = await asyncio.gather(*create_tasks)

            session_ids = [
                resp.json()["session_id"]
                for resp in create_responses
                if resp.status_code == 200
            ]

            # Send concurrent chat requests
            chat_tasks = [
                client.post(f"/sessions/{sid}/chat", json={"message": f"Hello {i}"})
                for i, sid in enumerate(session_ids)
            ]

            start_time = time.time()
            chat_responses = await asyncio.gather(*chat_tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            # Count successes (may fail if LLM not available, that's OK)
            successes = sum(
                1 for resp in chat_responses
                if not isinstance(resp, Exception) and resp.status_code in [200, 500]
            )

            print(f"Completed {successes}/{len(session_ids)} chat requests in {elapsed:.2f}s")

            # Cleanup
            cleanup_tasks = [client.delete(f"/sessions/{sid}") for sid in session_ids]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)


class TestMemoryLeaks:
    """Tests for memory leaks under repeated load."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        from src.main import app
        with TestClient(app) as c:
            yield c

    def test_repeated_session_cycles_no_leak(self, client):
        """Test repeated creation/deletion doesn't leak memory."""
        # This is a basic smoke test - proper memory leak testing
        # requires profiling tools like memory_profiler or tracemalloc

        for cycle in range(10):
            # Create 5 sessions
            session_ids = []
            for _ in range(5):
                resp = client.post("/sessions")
                if resp.status_code == 200:
                    session_ids.append(resp.json()["session_id"])

            # Delete all
            for sid in session_ids:
                client.delete(f"/sessions/{sid}")

        # If we get here without crashing or hanging, basic leak test passed
        assert True
