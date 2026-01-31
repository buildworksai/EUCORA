# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
License Management Demo Data Seeder

Seeds:
- Vendors (Microsoft, VMware, Adobe, etc.)
- License SKUs (product codes with license models)
- Entitlements (purchased/contracted licenses)
- Consumption Signals (usage data)
"""
import logging
import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def seed_license_management_data(clear_existing: bool = False) -> dict:  # noqa: C901
    """
    Seed license management demo data.

    Returns:
        Dictionary with seeding statistics
    """
    from apps.license_management.models import (
        ConsumptionSignal,
        Entitlement,
        EntitlementStatus,
        LicenseModelType,
        LicenseSKU,
        PrincipalType,
        Vendor,
    )

    stats = {
        "vendors": 0,
        "skus": 0,
        "entitlements": 0,
        "consumption_signals": 0,
    }

    try:
        if clear_existing:
            logger.info("Clearing existing license data...")
            with transaction.atomic():
                # Delete in reverse dependency order
                ConsumptionSignal.objects.filter(source_system="DEMO_SEEDER").delete()
                Entitlement.objects.filter(contract_id__startswith="DEMO-").delete()
                LicenseSKU.objects.filter(sku_code__startswith="DEMO-").delete()
                Vendor.objects.filter(identifier__startswith="DEMO_").delete()
            logger.info("License data cleared")

        # Create vendors
        logger.info("Creating vendors...")
        vendors_data = [
            {
                "name": "Microsoft Corporation",
                "identifier": "DEMO_MSFT",
                "website": "https://www.microsoft.com",
                "support_contact": "licensing@microsoft.com",
                "notes": "Enterprise Agreement with Software Assurance",
            },
            {
                "name": "VMware by Broadcom",
                "identifier": "DEMO_VMWARE",
                "website": "https://www.vmware.com",
                "support_contact": "licensing@vmware.com",
                "notes": "Enterprise License Agreement",
            },
            {
                "name": "Adobe Inc.",
                "identifier": "DEMO_ADOBE",
                "website": "https://www.adobe.com",
                "support_contact": "licensing@adobe.com",
                "notes": "Creative Cloud for Enterprise",
            },
            {
                "name": "Atlassian Corporation",
                "identifier": "DEMO_ATLASSIAN",
                "website": "https://www.atlassian.com",
                "support_contact": "licensing@atlassian.com",
                "notes": "Server and Cloud licenses",
            },
            {
                "name": "Oracle Corporation",
                "identifier": "DEMO_ORACLE",
                "website": "https://www.oracle.com",
                "support_contact": "licensing@oracle.com",
                "notes": "Database and Middleware licenses",
            },
        ]

        vendors = []
        for vendor_data in vendors_data:
            # Try to get by identifier first, then by name
            try:
                vendor = Vendor.objects.get(identifier=vendor_data["identifier"])
                created = False
            except Vendor.DoesNotExist:
                try:
                    vendor = Vendor.objects.get(name=vendor_data["name"])
                    # Update identifier to match demo data
                    vendor.identifier = vendor_data["identifier"]
                    created = False
                except Vendor.DoesNotExist:
                    vendor = Vendor.objects.create(**vendor_data)
                    created = True

            if not created:
                # Update existing vendor with demo data
                for key, value in vendor_data.items():
                    setattr(vendor, key, value)
                vendor.save()

            vendors.append(vendor)
            stats["vendors"] += 1

        logger.info(f"Created/updated {stats['vendors']} vendors")

        # Create license SKUs
        logger.info("Creating license SKUs...")
        skus_data = [
            # Microsoft SKUs
            {
                "vendor": vendors[0],  # Microsoft
                "sku_code": "DEMO-M365-E5",
                "name": "Microsoft 365 E5",
                "description": "Complete productivity and security suite",
                "license_model_type": LicenseModelType.USER,
                "cost_per_unit": Decimal("57.00"),
                "currency": "USD",
            },
            {
                "vendor": vendors[0],
                "sku_code": "DEMO-WIN-ENT",
                "name": "Windows Enterprise E3",
                "description": "Windows Enterprise with extended security",
                "license_model_type": LicenseModelType.DEVICE,
                "cost_per_unit": Decimal("7.00"),
                "currency": "USD",
            },
            {
                "vendor": vendors[0],
                "sku_code": "DEMO-SQL-STD",
                "name": "SQL Server Standard (Core)",
                "description": "SQL Server Standard Edition per core",
                "license_model_type": LicenseModelType.CORE,
                "cost_per_unit": Decimal("3717.00"),
                "currency": "USD",
            },
            # VMware SKUs
            {
                "vendor": vendors[1],  # VMware
                "sku_code": "DEMO-VSPHERE-ENT",
                "name": "vSphere Enterprise Plus",
                "description": "Advanced virtualization platform",
                "license_model_type": LicenseModelType.CORE,
                "cost_per_unit": Decimal("4295.00"),
                "currency": "USD",
            },
            {
                "vendor": vendors[1],
                "sku_code": "DEMO-VSAN-ENT",
                "name": "vSAN Enterprise",
                "description": "Software-defined storage solution",
                "license_model_type": LicenseModelType.CORE,
                "cost_per_unit": Decimal("2995.00"),
                "currency": "USD",
            },
            # Adobe SKUs
            {
                "vendor": vendors[2],  # Adobe
                "sku_code": "DEMO-CC-ALL-APPS",
                "name": "Creative Cloud All Apps",
                "description": "Complete Creative Cloud suite",
                "license_model_type": LicenseModelType.USER,
                "cost_per_unit": Decimal("54.99"),
                "currency": "USD",
            },
            # Atlassian SKUs
            {
                "vendor": vendors[3],  # Atlassian
                "sku_code": "DEMO-JIRA-DC",
                "name": "Jira Data Center",
                "description": "Project tracking and agile development",
                "license_model_type": LicenseModelType.USER,
                "cost_per_unit": Decimal("12.50"),
                "currency": "USD",
            },
            {
                "vendor": vendors[3],
                "sku_code": "DEMO-CONFLUENCE-DC",
                "name": "Confluence Data Center",
                "description": "Team collaboration and documentation",
                "license_model_type": LicenseModelType.USER,
                "cost_per_unit": Decimal("10.00"),
                "currency": "USD",
            },
            # Oracle SKUs
            {
                "vendor": vendors[4],  # Oracle
                "sku_code": "DEMO-DB-ENT",
                "name": "Oracle Database Enterprise Edition",
                "description": "Enterprise database management system",
                "license_model_type": LicenseModelType.CORE,
                "cost_per_unit": Decimal("47500.00"),
                "currency": "USD",
            },
        ]

        skus = []
        for sku_data in skus_data:
            sku, created = LicenseSKU.objects.get_or_create(
                vendor=sku_data["vendor"],
                sku_code=sku_data["sku_code"],
                defaults={k: v for k, v in sku_data.items() if k not in ["vendor", "sku_code"]},
            )
            if not created:
                # Update existing SKU
                for key, value in sku_data.items():
                    if key not in ["vendor", "sku_code"]:
                        setattr(sku, key, value)
                sku.save()
            skus.append(sku)
            stats["skus"] += 1

        logger.info(f"Created/updated {stats['skus']} SKUs")

        # Create entitlements
        logger.info("Creating entitlements...")
        entitlements_data = [
            # Microsoft entitlements
            {
                "sku": skus[0],  # M365 E5
                "contract_id": "DEMO-EA-2025-001",
                "entitled_quantity": 5000,
                "start_date": timezone.now().date() - timedelta(days=180),
                "end_date": timezone.now().date() + timedelta(days=185),
                "status": EntitlementStatus.ACTIVE,
            },
            {
                "sku": skus[1],  # Windows Enterprise
                "contract_id": "DEMO-EA-2025-001",
                "entitled_quantity": 20000,
                "start_date": timezone.now().date() - timedelta(days=180),
                "end_date": timezone.now().date() + timedelta(days=185),
                "status": EntitlementStatus.ACTIVE,
            },
            {
                "sku": skus[2],  # SQL Server
                "contract_id": "DEMO-EA-2024-003",
                "entitled_quantity": 128,
                "start_date": timezone.now().date() - timedelta(days=365),
                "end_date": timezone.now().date() + timedelta(days=365),
                "status": EntitlementStatus.ACTIVE,
            },
            # VMware entitlements
            {
                "sku": skus[3],  # vSphere
                "contract_id": "DEMO-VMWARE-2025",
                "entitled_quantity": 200,
                "start_date": timezone.now().date() - timedelta(days=200),
                "end_date": timezone.now().date() + timedelta(days=165),
                "status": EntitlementStatus.ACTIVE,
            },
            {
                "sku": skus[4],  # vSAN
                "contract_id": "DEMO-VMWARE-2025",
                "entitled_quantity": 200,
                "start_date": timezone.now().date() - timedelta(days=200),
                "end_date": timezone.now().date() + timedelta(days=165),
                "status": EntitlementStatus.ACTIVE,
            },
            # Adobe entitlements
            {
                "sku": skus[5],  # Creative Cloud
                "contract_id": "DEMO-ADOBE-2025",
                "entitled_quantity": 500,
                "start_date": timezone.now().date() - timedelta(days=90),
                "end_date": timezone.now().date() + timedelta(days=275),
                "status": EntitlementStatus.ACTIVE,
            },
            # Atlassian entitlements
            {
                "sku": skus[6],  # Jira
                "contract_id": "DEMO-ATLASSIAN-2025",
                "entitled_quantity": 2000,
                "start_date": timezone.now().date() - timedelta(days=150),
                "end_date": timezone.now().date() + timedelta(days=215),
                "status": EntitlementStatus.ACTIVE,
            },
            {
                "sku": skus[7],  # Confluence
                "contract_id": "DEMO-ATLASSIAN-2025",
                "entitled_quantity": 2000,
                "start_date": timezone.now().date() - timedelta(days=150),
                "end_date": timezone.now().date() + timedelta(days=215),
                "status": EntitlementStatus.ACTIVE,
            },
            # Oracle entitlements
            {
                "sku": skus[8],  # Oracle Database
                "contract_id": "DEMO-ORACLE-2024",
                "entitled_quantity": 50,
                "start_date": timezone.now().date() - timedelta(days=300),
                "end_date": timezone.now().date() + timedelta(days=65),
                "status": EntitlementStatus.ACTIVE,
            },
        ]

        entitlements = []
        for ent_data in entitlements_data:
            # Use contract_id and SKU as unique identifier
            entitlement, created = Entitlement.objects.get_or_create(
                contract_id=ent_data["contract_id"],
                sku=ent_data["sku"],
                defaults={k: v for k, v in ent_data.items() if k not in ["contract_id", "sku"]},
            )
            if not created:
                # Update existing entitlement
                for key, value in ent_data.items():
                    if key not in ["contract_id", "sku"]:
                        setattr(entitlement, key, value)
                entitlement.save()
            entitlements.append(entitlement)
            stats["entitlements"] += 1

        logger.info(f"Created/updated {stats['entitlements']} entitlements")

        # Create consumption signals
        logger.info("Creating consumption signals...")
        consumption_data = []

        # Create consumption for each SKU
        for idx, sku in enumerate(skus):
            # Find the entitlement for this SKU
            entitlement = next((e for e in entitlements if e.sku == sku), None)
            if not entitlement:
                continue

            # Determine consumption based on license type
            if sku.license_model_type == LicenseModelType.USER:
                # User licenses: 70-95% utilization
                total_consumed = int(entitlement.entitled_quantity * random.uniform(0.70, 0.95))
                principal_type = PrincipalType.USER
            elif sku.license_model_type == LicenseModelType.DEVICE:
                # Device licenses: 80-98% utilization
                total_consumed = int(entitlement.entitled_quantity * random.uniform(0.80, 0.98))
                principal_type = PrincipalType.DEVICE
            elif sku.license_model_type == LicenseModelType.CORE:
                # Core licenses: 60-90% utilization
                total_consumed = int(entitlement.entitled_quantity * random.uniform(0.60, 0.90))
                principal_type = PrincipalType.DEVICE
            else:
                total_consumed = int(entitlement.entitled_quantity * random.uniform(0.70, 0.90))
                principal_type = PrincipalType.USER

            # Create 5-10 consumption signals per SKU to show distribution
            num_signals = min(total_consumed, random.randint(5, 10))

            for i in range(num_signals):
                # Generate unique principal ID
                if principal_type == PrincipalType.USER:
                    principal_id = f"user{idx:03d}{i:03d}@demo.example.com"
                    principal_name = f"Demo User {idx:03d}-{i:03d}"
                else:
                    principal_id = f"device-{idx:03d}-{i:03d}"
                    principal_name = f"Demo Device {idx:03d}-{i:03d}"

                consumption_data.append(
                    ConsumptionSignal(
                        source_system="DEMO_SEEDER",
                        raw_id=f"demo-signal-{uuid.uuid4().hex[:8]}",
                        timestamp=timezone.now() - timedelta(hours=random.randint(0, 72)),
                        principal_type=principal_type,
                        principal_id=principal_id,
                        principal_name=principal_name,
                        sku=sku,
                        confidence=1.0,
                        raw_payload_hash="",
                        raw_payload={
                            "source": "demo_seeder",
                            "entitlement_id": str(entitlement.id),
                            "entitled_quantity": entitlement.entitled_quantity,
                        },
                        is_processed=True,
                        processed_at=timezone.now(),
                    )
                )

        # Bulk create consumption signals
        ConsumptionSignal.objects.bulk_create(consumption_data, batch_size=500, ignore_conflicts=True)
        stats["consumption_signals"] = len(consumption_data)

        logger.info(f"Created {stats['consumption_signals']} consumption signals")

        logger.info("License management demo data seeded successfully")
        return stats

    except Exception as e:
        logger.error(f"Error seeding license data: {e}", exc_info=True)
        return stats


def license_data_stats() -> dict:
    """Get current license data statistics."""
    from apps.license_management.models import ConsumptionSignal, Entitlement, LicenseSKU, Vendor

    return {
        "vendors": Vendor.objects.filter(identifier__startswith="DEMO_").count(),
        "skus": LicenseSKU.objects.filter(sku_code__startswith="DEMO-").count(),
        "entitlements": Entitlement.objects.filter(contract_id__startswith="DEMO-").count(),
        "consumption_signals": ConsumptionSignal.objects.filter(source_system="DEMO_SEEDER").count(),
    }
