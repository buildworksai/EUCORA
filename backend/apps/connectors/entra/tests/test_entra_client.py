# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for Entra ID connector client."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.connectors.entra.auth import EntraAuth
from apps.connectors.entra.client import EntraConnector, EntraGroup, EntraUser


@pytest.fixture
def mock_auth():
    """Create a mock EntraAuth instance."""
    auth = MagicMock(spec=EntraAuth)
    auth.authenticate = AsyncMock()
    auth.refresh_token = AsyncMock()
    auth.get_auth_header.return_value = {"Authorization": "Bearer test-token"}
    auth.is_token_valid = True
    return auth


@pytest.fixture
def connector(mock_auth):
    """Create a connector with mock auth."""
    return EntraConnector(auth=mock_auth)


class TestEntraConnectorInit:
    """Tests for EntraConnector initialization."""

    def test_init_default_values(self, mock_auth):
        """Test initialization with default values."""
        connector = EntraConnector(auth=mock_auth)
        assert connector._timeout == 30.0
        assert connector._max_retries == 3
        assert connector._page_size == 100

    def test_init_custom_values(self, mock_auth):
        """Test initialization with custom values."""
        connector = EntraConnector(
            auth=mock_auth,
            timeout=60.0,
            max_retries=5,
            page_size=500,
        )
        assert connector._timeout == 60.0
        assert connector._max_retries == 5
        assert connector._page_size == 500

    def test_init_page_size_capped(self, mock_auth):
        """Test that page_size is capped at 999."""
        connector = EntraConnector(auth=mock_auth, page_size=2000)
        assert connector._page_size == 999


class TestEntraConnectorIdempotencyKey:
    """Tests for idempotency key generation."""

    def test_get_idempotency_key_same_params(self, connector):
        """Test same params produce same key."""
        key1 = connector._get_idempotency_key("sync_users", {"filter": "test"})
        key2 = connector._get_idempotency_key("sync_users", {"filter": "test"})
        assert key1 == key2

    def test_get_idempotency_key_different_params(self, connector):
        """Test different params produce different keys."""
        key1 = connector._get_idempotency_key("sync_users", {"filter": "test1"})
        key2 = connector._get_idempotency_key("sync_users", {"filter": "test2"})
        assert key1 != key2

    def test_get_idempotency_key_different_operations(self, connector):
        """Test different operations produce different keys."""
        key1 = connector._get_idempotency_key("sync_users", {"filter": "test"})
        key2 = connector._get_idempotency_key("sync_groups", {"filter": "test"})
        assert key1 != key2


class TestEntraConnectorListUsers:
    """Tests for list_users method."""

    @pytest.mark.asyncio
    async def test_list_users_basic(self, connector):
        """Test basic user listing."""
        mock_response = {
            "value": [
                {
                    "id": "user-1",
                    "userPrincipalName": "user1@example.com",
                    "displayName": "User One",
                    "accountEnabled": True,
                }
            ],
            "@odata.count": 1,
        }

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            users = await connector.list_users()

            assert len(users) == 1
            assert users[0].id == "user-1"
            assert users[0].user_principal_name == "user1@example.com"
            assert users[0].display_name == "User One"

    @pytest.mark.asyncio
    async def test_list_users_with_filter(self, connector):
        """Test user listing with filter."""
        mock_response = {"value": [], "@odata.count": 0}

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await connector.list_users(filter_query="department eq 'Engineering'")

            call_args = mock_request.call_args
            assert "$filter" in call_args.kwargs["params"]
            assert call_args.kwargs["params"]["$filter"] == "department eq 'Engineering'"

    @pytest.mark.asyncio
    async def test_list_users_pagination(self, connector):
        """Test user listing handles pagination."""
        page1_response = {
            "value": [{"id": "user-1", "userPrincipalName": "u1@ex.com", "displayName": "U1", "accountEnabled": True}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?$skiptoken=xxx",
        }
        page2_response = {
            "value": [{"id": "user-2", "userPrincipalName": "u2@ex.com", "displayName": "U2", "accountEnabled": True}],
        }

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [page1_response, page2_response]

            users = await connector.list_users()

            assert len(users) == 2
            assert mock_request.call_count == 2


class TestEntraConnectorGetUser:
    """Tests for get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, connector):
        """Test getting user by ID."""
        user_response = {
            "id": "user-123",
            "userPrincipalName": "test@example.com",
            "displayName": "Test User",
            "accountEnabled": True,
        }
        manager_response = {"id": "manager-456"}
        groups_response = {
            "value": [
                {"@odata.type": "#microsoft.graph.group", "id": "group-1"},
                {"@odata.type": "#microsoft.graph.group", "id": "group-2"},
            ]
        }

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [user_response, manager_response, groups_response]

            user = await connector.get_user("user-123")

            assert user is not None
            assert user.id == "user-123"
            assert user.manager_id == "manager-456"
            assert len(user.member_of) == 2

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, connector):
        """Test getting non-existent user returns None."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

            user = await connector.get_user("nonexistent")

            assert user is None


class TestEntraConnectorListGroups:
    """Tests for list_groups method."""

    @pytest.mark.asyncio
    async def test_list_groups_basic(self, connector):
        """Test basic group listing."""
        mock_response = {
            "value": [
                {
                    "id": "group-1",
                    "displayName": "Engineering",
                    "securityEnabled": True,
                    "mailEnabled": False,
                    "groupTypes": [],
                }
            ],
            "@odata.count": 1,
        }

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            groups = await connector.list_groups(include_member_count=False)

            assert len(groups) == 1
            assert groups[0].id == "group-1"
            assert groups[0].display_name == "Engineering"
            assert groups[0].security_enabled is True

    @pytest.mark.asyncio
    async def test_list_groups_security_only(self, connector):
        """Test listing security groups only."""
        mock_response = {"value": [], "@odata.count": 0}

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await connector.list_groups(security_only=True, include_member_count=False)

            call_args = mock_request.call_args
            assert "securityEnabled eq true" in call_args.kwargs["params"]["$filter"]


class TestEntraConnectorGetGroup:
    """Tests for get_group method."""

    @pytest.mark.asyncio
    async def test_get_group(self, connector):
        """Test getting a specific group."""
        mock_response = {
            "id": "group-123",
            "displayName": "Test Group",
            "securityEnabled": True,
            "mailEnabled": False,
            "groupTypes": [],
        }

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            group = await connector.get_group("group-123")

            assert group is not None
            assert group.id == "group-123"
            assert group.display_name == "Test Group"

    @pytest.mark.asyncio
    async def test_get_group_not_found(self, connector):
        """Test getting non-existent group returns None."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

            group = await connector.get_group("nonexistent")

            assert group is None


class TestEntraConnectorGetGroupMembers:
    """Tests for get_group_members method."""

    @pytest.mark.asyncio
    async def test_get_group_members(self, connector):
        """Test getting group members."""
        mock_response = {
            "value": [
                {"@odata.type": "#microsoft.graph.user", "id": "user-1"},
                {"@odata.type": "#microsoft.graph.user", "id": "user-2"},
                {"@odata.type": "#microsoft.graph.group", "id": "nested-group"},  # Should be filtered
            ]
        }

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            members = await connector.get_group_members("group-123")

            assert len(members) == 2
            assert "user-1" in members
            assert "user-2" in members
            assert "nested-group" not in members

    @pytest.mark.asyncio
    async def test_get_group_members_transitive(self, connector):
        """Test getting transitive group members."""
        mock_response = {"value": []}

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await connector.get_group_members("group-123", transitive=True)

            call_args = mock_request.call_args
            assert "transitiveMembers" in call_args.args[1]


class TestEntraConnectorSyncUsers:
    """Tests for sync_users method."""

    @pytest.mark.asyncio
    async def test_sync_users_success(self, connector):
        """Test successful user sync."""
        mock_users = [
            EntraUser(
                id="user-1",
                user_principal_name="u1@ex.com",
                display_name="U1",
                given_name="User",
                surname="One",
                mail="u1@ex.com",
                job_title=None,
                department=None,
                office_location=None,
                mobile_phone=None,
                account_enabled=True,
                created_datetime=None,
            )
        ]

        with patch.object(connector, "list_users", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_users

            result = await connector.sync_users()

            assert result.success is True
            assert result.records_processed == 1
            assert result.operation == "sync_users"

    @pytest.mark.asyncio
    async def test_sync_users_idempotent(self, connector):
        """Test that sync_users is idempotent."""
        mock_users = []

        with patch.object(connector, "list_users", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_users

            result1 = await connector.sync_users(filter_query="test")
            result2 = await connector.sync_users(filter_query="test")

            # Second call should return cached result
            assert mock_list.call_count == 1
            assert result1.correlation_id == result2.correlation_id

    @pytest.mark.asyncio
    async def test_sync_users_error(self, connector):
        """Test sync_users handles errors."""
        with patch.object(connector, "list_users", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("API Error")

            result = await connector.sync_users()

            assert result.success is False
            assert len(result.errors) == 1
            assert "API Error" in result.errors[0]["message"]


class TestEntraConnectorSyncGroups:
    """Tests for sync_groups method."""

    @pytest.mark.asyncio
    async def test_sync_groups_success(self, connector):
        """Test successful group sync."""
        mock_groups = [
            EntraGroup(
                id="group-1",
                display_name="Engineering",
                description=None,
                mail=None,
                mail_enabled=False,
                security_enabled=True,
                group_types=[],
                created_datetime=None,
            )
        ]

        with patch.object(connector, "list_groups", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_groups

            result = await connector.sync_groups()

            assert result.success is True
            assert result.records_processed == 1
            assert result.operation == "sync_groups"


class TestEntraConnectorTestConnection:
    """Tests for test_connection method."""

    @pytest.mark.asyncio
    async def test_connection_success(self, connector):
        """Test successful connection test."""
        mock_response = {
            "value": [
                {
                    "id": "tenant-123",
                    "displayName": "Test Tenant",
                    "verifiedDomains": [{"name": "example.com", "isDefault": True}],
                }
            ]
        }

        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await connector.test_connection()

            assert result["success"] is True
            assert result["tenant_id"] == "tenant-123"
            assert result["tenant_name"] == "Test Tenant"
            assert result["primary_domain"] == "example.com"

    @pytest.mark.asyncio
    async def test_connection_failure(self, connector):
        """Test connection test failure."""
        with patch.object(connector, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Connection refused")

            result = await connector.test_connection()

            assert result["success"] is False
            assert "Connection refused" in result["error"]


class TestEntraConnectorParseUser:
    """Tests for _parse_user method."""

    def test_parse_user_full(self, connector):
        """Test parsing user with all fields."""
        data = {
            "id": "user-123",
            "userPrincipalName": "test@example.com",
            "displayName": "Test User",
            "givenName": "Test",
            "surname": "User",
            "mail": "test@example.com",
            "jobTitle": "Engineer",
            "department": "Engineering",
            "officeLocation": "Building A",
            "mobilePhone": "+1234567890",
            "accountEnabled": True,
            "createdDateTime": "2024-01-15T10:30:00Z",
            "signInActivity": {"lastSignInDateTime": "2024-01-20T14:00:00Z"},
        }

        user = connector._parse_user(data)

        assert user.id == "user-123"
        assert user.user_principal_name == "test@example.com"
        assert user.given_name == "Test"
        assert user.surname == "User"
        assert user.job_title == "Engineer"
        assert user.department == "Engineering"
        assert user.created_datetime is not None
        assert user.last_sign_in_datetime is not None

    def test_parse_user_minimal(self, connector):
        """Test parsing user with minimal fields."""
        data = {
            "id": "user-123",
        }

        user = connector._parse_user(data)

        assert user.id == "user-123"
        assert user.user_principal_name == ""
        assert user.display_name == ""
        assert user.given_name is None


class TestEntraConnectorParseGroup:
    """Tests for _parse_group method."""

    def test_parse_group_full(self, connector):
        """Test parsing group with all fields."""
        data = {
            "id": "group-123",
            "displayName": "Engineering",
            "description": "Engineering team",
            "mail": "eng@example.com",
            "mailEnabled": True,
            "securityEnabled": True,
            "groupTypes": ["Unified"],
            "createdDateTime": "2024-01-15T10:30:00Z",
            "membershipRule": "user.department -eq 'Engineering'",
        }

        group = connector._parse_group(data)

        assert group.id == "group-123"
        assert group.display_name == "Engineering"
        assert group.description == "Engineering team"
        assert group.mail_enabled is True
        assert group.security_enabled is True
        assert group.membership_rule == "user.department -eq 'Engineering'"

    def test_parse_group_minimal(self, connector):
        """Test parsing group with minimal fields."""
        data = {
            "id": "group-123",
        }

        group = connector._parse_group(data)

        assert group.id == "group-123"
        assert group.display_name == ""
        assert group.description is None


class TestEntraConnectorRepr:
    """Tests for __repr__ method."""

    def test_repr(self, connector):
        """Test string representation."""
        repr_str = repr(connector)
        assert "EntraConnector" in repr_str
        assert "EntraAuth" in repr_str or "auth=" in repr_str
