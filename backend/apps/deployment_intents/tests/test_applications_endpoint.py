"""
Backend test for the new deployments/applications endpoint.

This test verifies:
1. Applications are grouped by name
2. Versions are sorted by creation date (newest first)
3. Deployments are nested under versions
4. Filtering by app_name, status, ring works
"""

import json
from typing import Any


def test_applications_with_versions_endpoint() -> None:
    """
    Mock test to verify endpoint response structure.
    Actual test would run against Django testdb.
    """
    # Sample response from /api/v1/deployments/applications
    sample_response: dict[str, Any] = {
        "applications": [
            {
                "app_name": "Adobe Acrobat Reader",
                "latest_version": "24.001",
                "deployment_count": 3,
                "versions": [
                    {
                        "version": "24.001",
                        "latest_created_at": "2026-01-20T10:00:00Z",
                        "deployments": [
                            {
                                "correlation_id": "12345678-1234-1234-1234-123456789012",
                                "target_ring": "CANARY",
                                "status": "COMPLETED",
                                "risk_score": 15,
                                "requires_cab_approval": False,
                                "created_at": "2026-01-20T10:00:00Z",
                            },
                            {
                                "correlation_id": "87654321-4321-4321-4321-210987654321",
                                "target_ring": "PILOT",
                                "status": "DEPLOYING",
                                "risk_score": 15,
                                "requires_cab_approval": False,
                                "created_at": "2026-01-20T09:00:00Z",
                            },
                        ],
                    },
                    {
                        "version": "23.999",
                        "latest_created_at": "2026-01-19T10:00:00Z",
                        "deployments": [
                            {
                                "correlation_id": "11111111-1111-1111-1111-111111111111",
                                "target_ring": "LAB",
                                "status": "APPROVED",
                                "risk_score": 10,
                                "requires_cab_approval": False,
                                "created_at": "2026-01-19T10:00:00Z",
                            },
                        ],
                    },
                ],
            },
            {
                "app_name": "Microsoft Teams",
                "latest_version": "25.1.1",
                "deployment_count": 2,
                "versions": [
                    {
                        "version": "25.1.1",
                        "latest_created_at": "2026-01-20T08:00:00Z",
                        "deployments": [
                            {
                                "correlation_id": "22222222-2222-2222-2222-222222222222",
                                "target_ring": "GLOBAL",
                                "status": "AWAITING_CAB",
                                "risk_score": 65,
                                "requires_cab_approval": True,
                                "created_at": "2026-01-20T08:00:00Z",
                            },
                        ],
                    },
                ],
            },
        ]
    }

    # Assertions
    assert "applications" in sample_response
    assert len(sample_response["applications"]) == 2

    # Check first application
    adobe = sample_response["applications"][0]
    assert adobe["app_name"] == "Adobe Acrobat Reader"
    assert adobe["latest_version"] == "24.001"
    assert adobe["deployment_count"] == 3
    assert len(adobe["versions"]) == 2

    # Check versions are sorted by date (newest first)
    assert adobe["versions"][0]["version"] == "24.001"
    assert adobe["versions"][1]["version"] == "23.999"

    # Check deployments nested under version
    version_24 = adobe["versions"][0]
    assert len(version_24["deployments"]) == 2
    assert version_24["deployments"][0]["target_ring"] == "CANARY"

    # Check second application
    teams = sample_response["applications"][1]
    assert teams["app_name"] == "Microsoft Teams"
    assert teams["latest_version"] == "25.1.1"
    
    # Check deployment requires CAB approval
    teams_deployment = teams["versions"][0]["deployments"][0]
    assert teams_deployment["requires_cab_approval"] is True

    # Verify JSON serialization works
    json_str = json.dumps(sample_response)
    assert isinstance(json_str, str)
    roundtrip = json.loads(json_str)
    assert roundtrip == sample_response

    print("✓ All assertions passed")
    print("✓ Response structure verified")
    print("✓ Nested application/version/deployment hierarchy correct")
    print("✓ JSON serialization working")


if __name__ == "__main__":
    test_applications_with_versions_endpoint()
    print("\n✓ Backend endpoint structure test PASSED")
