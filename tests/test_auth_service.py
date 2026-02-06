"""
Test suite for Auth Service API endpoints.

Tests cover:
- Successful authentication flows
- Failed authentication scenarios
- Token refresh
- User management (admin operations)
- Authorization checks
"""

import pytest
from httpx import AsyncClient


@pytest.mark.auth
class TestAuthService:
    """Test suite for Auth Service endpoints."""

    # =========================================================================
    # Health Check Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_health_check(self, http_client: AsyncClient, auth_health_url: str):
        """Test health check endpoint."""
        response = await http_client.get(auth_health_url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data

    # =========================================================================
    # Login Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_credentials: dict,
    ):
        """Test successful login with valid credentials."""
        response = await http_client.post(
            f"{auth_base_url}/login",
            json=admin_credentials,
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_invalid_username(
        self, http_client: AsyncClient, auth_base_url: str
    ):
        """Test login with invalid username."""
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": "nonexistent", "password": "password"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_credentials: dict,
    ):
        """Test login with invalid password."""
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={
                "username": admin_credentials["username"],
                "password": "wrong_password",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_missing_fields(
        self, http_client: AsyncClient, auth_base_url: str
    ):
        """Test login with missing required fields."""
        # Missing password
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": "admin"},
        )
        assert response.status_code == 422

        # Missing username
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"password": "password"},
        )
        assert response.status_code == 422

        # Empty body
        response = await http_client.post(f"{auth_base_url}/login", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_validation_username_password_length(
        self, http_client: AsyncClient, auth_base_url: str
    ):
        """Test login with username/password length and format validation (422)."""
        # Username too short (< 3)
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": "ab", "password": "validpass"},
        )
        assert response.status_code == 422

        # Username too long (> 50)
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": "a" * 51, "password": "validpass"},
        )
        assert response.status_code == 422

        # Password too long (> 1024)
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": "admin", "password": "x" * 1025},
        )
        assert response.status_code == 422

        # Username with leading/trailing whitespace (rejected)
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": "  admin  ", "password": "validpass"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_rate_limit(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
    ):
        """After N login attempts for same username, next request returns 429."""
        # Use a dedicated username so we do not exhaust admin (used by other tests).
        # Test env uses LOGIN_RATE_LIMIT_PER_USER=100; production uses 5. Do 101 attempts
        # so we exceed limit in both (429 on the (limit+1)-th request).
        username = "ratelimit_test_user"
        limit = 101  # exceeds both 5 and 100
        for _ in range(limit - 1):
            await http_client.post(
                f"{auth_base_url}/login",
                json={"username": username, "password": "wrong"},
            )
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": username, "password": "wrong"},
        )
        # App returns 429 (rate limit) or 403 (lockout); nginx may return 503 when overloaded
        assert response.status_code in (429, 503, 403)
        data = response.json()
        assert "detail" in data or "message" in data

    @pytest.mark.asyncio
    async def test_lockout_after_failed_logins(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_headers: dict,
    ):
        """After N failed logins for a username, next login returns 403 (locked) or 429 (rate limit)."""
        # Use a dedicated user so we do not lock admin. Create user then 5 wrong logins, then 6th correct -> 403.
        username = "lockout_test_user"
        password = "LockoutTest@123"
        create_response = await http_client.post(
            f"{auth_base_url}/users",
            json={
                "username": username,
                "password": password,
                "email": "lockout_test@example.com",
                "full_name": "Lockout Test",
                "role": "user",
            },
            headers=admin_headers,
        )
        if create_response.status_code not in (200, 201, 400):
            pytest.skip("Could not create lockout test user")
        # 400 = user already exists from previous run; still run lockout test
        # Test env uses MAX_FAILED_LOGIN_ATTEMPTS=10; production uses 5. Do 10 failures
        # so the next (correct) login gets 403 in both.
        for _ in range(10):
            await http_client.post(
                f"{auth_base_url}/login",
                json={"username": username, "password": "wrong"},
            )
        response = await http_client.post(
            f"{auth_base_url}/login",
            json={"username": username, "password": password},
        )
        assert response.status_code in (403, 429)
        data = response.json()
        assert "detail" in data
        assert (
            "locked" in data["detail"].lower() or "too many" in data["detail"].lower()
        )
        # Teardown: remove the lockout test user
        list_resp = await http_client.get(
            f"{auth_base_url}/users",
            headers=admin_headers,
        )
        if list_resp.status_code == 200:
            for u in list_resp.json():
                if u.get("username") == username:
                    await http_client.delete(
                        f"{auth_base_url}/users/{u['id']}",
                        headers=admin_headers,
                    )
                    break

    # =========================================================================
    # Token Refresh Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_credentials: dict,
    ):
        """Test successful token refresh."""
        # First, login to get refresh token
        login_response = await http_client.post(
            f"{auth_base_url}/login",
            json=admin_credentials,
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = await http_client.post(
            f"{auth_base_url}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(
        self, http_client: AsyncClient, auth_base_url: str, invalid_token: str
    ):
        """Test token refresh with invalid refresh token."""
        response = await http_client.post(
            f"{auth_base_url}/refresh",
            json={"refresh_token": invalid_token},
        )
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_refresh_token_missing(
        self, http_client: AsyncClient, auth_base_url: str
    ):
        """Test token refresh with missing refresh token."""
        response = await http_client.post(
            f"{auth_base_url}/refresh",
            json={},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refresh_rate_limit(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_credentials: dict,
    ):
        """After M refresh requests for same user, next returns 429."""
        login_response = await http_client.post(
            f"{auth_base_url}/login",
            json=admin_credentials,
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        # Exceed limit: test env 100, production 20. Do 101 requests; last one is 429 (or 503 from nginx).
        response = None
        for _ in range(101):
            response = await http_client.post(
                f"{auth_base_url}/refresh",
                json={"refresh_token": refresh_token},
            )
            if response.status_code in (429, 503):
                break
        assert response is not None
        assert response.status_code in (429, 503)

    # =========================================================================
    # Logout Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_logout_revokes_token(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_credentials: dict,
    ):
        """After logout, same access token returns 401 on protected endpoint."""
        login_response = await http_client.post(
            f"{auth_base_url}/login",
            json=admin_credentials,
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_response = await http_client.post(
            f"{auth_base_url}/logout",
            headers=headers,
        )
        assert logout_response.status_code == 204
        me_response = await http_client.get(
            f"{auth_base_url}/me",
            headers=headers,
        )
        assert me_response.status_code == 401

    # =========================================================================
    # Current User Info Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_token: str,
    ):
        """Test getting current user info with valid token."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await http_client.get(
            f"{auth_base_url}/me",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "role" in data
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(
        self, http_client: AsyncClient, auth_base_url: str
    ):
        """Test getting current user info without token."""
        response = await http_client.get(f"{auth_base_url}/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        invalid_token: str,
    ):
        """Test getting current user info with invalid token."""
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = await http_client.get(
            f"{auth_base_url}/me",
            headers=headers,
        )
        assert response.status_code == 401

    # =========================================================================
    # User Management Tests (Admin Only)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_list_users_success(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_headers: dict,
    ):
        """Test listing all users as admin."""
        response = await http_client.get(
            f"{auth_base_url}/users",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least admin user
        assert len(data) > 0
        assert any(user["username"] == "admin" for user in data)

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        user_headers: dict,
    ):
        """Test listing users as regular user (should fail)."""
        response = await http_client.get(
            f"{auth_base_url}/users",
            headers=user_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_headers: dict,
    ):
        """Test creating a new user as admin."""
        import uuid

        # Use unique username to avoid conflicts from previous test runs
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "username": f"newuser_{unique_id}",
            "password": "NewUser@123",
            "email": f"newuser_{unique_id}@example.com",
            "full_name": "New User",
            "role": "user",
        }
        response = await http_client.post(
            f"{auth_base_url}/users",
            json=user_data,
            headers=admin_headers,
        )
        # Accept both 200 (created) and 201 (created) as success
        assert response.status_code in (
            200,
            201,
        ), f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]
        assert "id" in data
        # Teardown: remove the created test user
        await http_client.delete(
            f"{auth_base_url}/users/{data['id']}",
            headers=admin_headers,
        )

    @pytest.mark.asyncio
    async def test_create_user_duplicate(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_headers: dict,
    ):
        """Test creating a user with duplicate username."""
        user_data = {
            "username": "admin",  # Already exists
            "password": "Password@123",
            "email": "admin2@example.com",
            "role": "user",
        }
        response = await http_client.post(
            f"{auth_base_url}/users",
            json=user_data,
            headers=admin_headers,
        )
        # Should fail with 400 or 409
        assert response.status_code in [400, 409, 422]

    @pytest.mark.asyncio
    async def test_create_user_invalid_data(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        admin_headers: dict,
    ):
        """Test creating user with invalid data."""
        # Missing required fields
        response = await http_client.post(
            f"{auth_base_url}/users",
            json={"username": "test"},
            headers=admin_headers,
        )
        assert response.status_code == 422

        # Invalid email format
        response = await http_client.post(
            f"{auth_base_url}/users",
            json={
                "username": "testuser2",
                "password": "Test@123",
                "email": "invalid-email",
                "role": "user",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

        # Password too short
        response = await http_client.post(
            f"{auth_base_url}/users",
            json={
                "username": "testuser3",
                "password": "short",
                "email": "test@example.com",
                "role": "user",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_unauthorized(
        self,
        http_client: AsyncClient,
        auth_base_url: str,
        user_headers: dict,
    ):
        """Test creating user as regular user (should fail)."""
        user_data = {
            "username": "unauthorized_user",
            "password": "Password@123",
            "email": "unauthorized@example.com",
            "role": "user",
        }
        response = await http_client.post(
            f"{auth_base_url}/users",
            json=user_data,
            headers=user_headers,
        )
        assert response.status_code == 403

    # =========================================================================
    # Password reset
    # =========================================================================

    @pytest.mark.asyncio
    async def test_forgot_password_returns_200(
        self, http_client: AsyncClient, auth_base_url: str, admin_credentials: dict
    ):
        """Forgot password returns 200 and same message (no user enumeration)."""
        response = await http_client.post(
            f"{auth_base_url}/forgot-password",
            json={"username": admin_credentials["username"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(
        self, http_client: AsyncClient, auth_base_url: str
    ):
        """Reset password with invalid token returns 400."""
        response = await http_client.post(
            f"{auth_base_url}/reset-password",
            json={"token": "invalid-token", "new_password": "NewSecure@123"},
        )
        assert response.status_code == 400
        assert (
            "invalid" in response.json().get("detail", "").lower()
            or "expired" in response.json().get("detail", "").lower()
        )

    @pytest.mark.asyncio
    async def test_forgot_and_reset_password_flow(
        self, http_client: AsyncClient, auth_base_url: str, admin_credentials: dict
    ):
        """Request reset, then reset with token (when dev token in response is enabled)."""
        # Request reset
        r1 = await http_client.post(
            f"{auth_base_url}/forgot-password",
            json={"username": admin_credentials["username"]},
        )
        assert r1.status_code == 200
        data = r1.json()
        token = data.get("reset_token")
        # If token not in response (prod mode), skip reset step
        if not token:
            return
        # Reset with token
        r2 = await http_client.post(
            f"{auth_base_url}/reset-password",
            json={"token": token, "new_password": "NewSecure@123"},
        )
        assert r2.status_code == 204
        # Login with new password
        r3 = await http_client.post(
            f"{auth_base_url}/login",
            json={
                "username": admin_credentials["username"],
                "password": "NewSecure@123",
            },
        )
        assert r3.status_code == 200
        # Restore original password for other tests (optional)
        from services.common.auth import (
            create_password_reset_token,
            update_user_password,
        )
        from services.common.config import settings

        tok2 = create_password_reset_token(admin_credentials["username"])
        if tok2:
            update_user_password(admin_credentials["username"], settings.ADMIN_PASSWORD)

    # =========================================================================
    # Request body size (auth service 64KB limit)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_login_body_too_large(
        self, http_client: AsyncClient, auth_base_url: str
    ):
        """Request body larger than auth service limit (64KB) returns 413."""
        # Auth service rejects body > 64KB via middleware (Content-Length check)
        large_body = b"x" * (65 * 1024)
        response = await http_client.post(
            f"{auth_base_url}/login",
            content=large_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(large_body)),
            },
        )
        # 413 from auth service; 502/503 from nginx when overloaded or body too large
        assert response.status_code in (413, 404, 502, 503)
