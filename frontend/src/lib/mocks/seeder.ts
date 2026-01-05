import { faker } from '@faker-js/faker';

export interface Asset {
    id: string;
    name: string;
    type: 'Laptop' | 'Desktop' | 'Virtual Machine' | 'Mobile' | 'Server';
    os: 'Windows 11' | 'Windows 10' | 'macOS Sonoma' | 'macOS Ventura' | 'Ubuntu 22.04' | 'iOS 17' | 'Android 14';
    location: string;
    status: 'Active' | 'Inactive' | 'Retired' | 'Maintenance';
    complianceScore: number;
    lastCheckin: Date;
    owner: string;
    // Detailed fields
    serialNumber: string;
    ipAddress: string;
    diskEncryption: boolean;
    firewallEnabled: boolean;
    installedApps: Application[];
    // DEX & Green IT metrics
    dexScore: number; // 0-10
    bootTime: number; // seconds
    carbonFootprint: number; // kg CO2e per year
    userSentiment: 'Positive' | 'Neutral' | 'Negative';
}

export interface Application {
    id: string;
    name: string;
    vendor: string;
    version: string;
    type: 'Packaged' | 'Unpackaged' | 'SaaS';
    installCount: number;
    complianceRate: number;
    riskScore: number;
}

export interface ChangeRequest {
    id: string;
    ticketNumber: string;
    title: string;
    description: string;
    requester: string;
    status: 'New' | 'Assessing' | 'CAB Review' | 'Approved' | 'Rejected' | 'Scheduled' | 'Completed';
    priority: 'Low' | 'Medium' | 'High' | 'Critical';
    riskScore: number;
    impact: 'Individual' | 'Department' | 'Global';
    createdDate: Date;
    scheduledDate: Date;
}

export interface AuditLog {
    id: string;
    timestamp: Date;
    actor: string;
    action: string;
    resource: string;
    details: string;
    status: 'Success' | 'Failure' | 'Warning';
    ipAddress: string;
}

// Deterministic seed for consistent UX testing
faker.seed(123);

export const generateApplications = (count: number): Application[] => {
    return Array.from({ length: count }, () => {
        return {
            id: faker.string.uuid(),
            name: faker.helpers.arrayElement([
                'Google Chrome', 'Adobe Acrobat', 'Zoom', 'Slack', 'Microsoft Office 365',
                'Visual Studio Code', 'Docker Desktop', 'Notion', 'Figma', 'Spotify'
            ]) + ' ' + faker.system.semver(),
            vendor: faker.company.name(),
            version: faker.system.semver(),
            type: faker.helpers.arrayElement(['Packaged', 'Unpackaged', 'SaaS']) as Application['type'],
            installCount: faker.number.int({ min: 100, max: 45000 }),
            complianceRate: faker.number.float({ min: 60, max: 99.9, multipleOf: 0.1 }),
            riskScore: faker.number.int({ min: 0, max: 100 }),
        };
    });
};

const appsPool = generateApplications(50); // Small pool for linking

export const generateAssets = (count: number): Asset[] => {
    return Array.from({ length: count }, () => {
        const type = faker.helpers.arrayElement(['Laptop', 'Desktop', 'Virtual Machine', 'Mobile', 'Server']) as Asset['type'];
        let os: Asset['os'] = 'Windows 11';

        if (type === 'Mobile') {
            os = faker.helpers.arrayElement(['iOS 17', 'Android 14']) as Asset['os'];
        } else if (type === 'Server' || type === 'Virtual Machine') {
            os = 'Ubuntu 22.04';
        } else {
            os = faker.helpers.arrayElement(['Windows 11', 'Windows 10', 'macOS Sonoma']) as Asset['os'];
        }

        // Random subset of apps
        const installed = faker.helpers.arrayElements(appsPool, { min: 3, max: 10 });

        // DEX logic
        const dexScore = faker.number.float({ min: 4, max: 10, multipleOf: 0.1 });
        const bootTime = faker.number.int({ min: 15, max: 120 });
        // Carbon: estimate based on device type (manufacturing + usage amortized)
        let carbon = 0;
        if (type === 'Desktop') carbon = 350;
        else if (type === 'Laptop') carbon = 250;
        else if (type === 'Server') carbon = 800;
        else carbon = 80;

        return {
            id: faker.string.uuid(),
            name: `EUC-${faker.airline.flightNumber()}-${faker.string.alphanumeric(4).toUpperCase()}`,
            type,
            os,
            location: faker.location.city(),
            status: faker.helpers.arrayElement(['Active', 'Active', 'Active', 'Maintenance', 'Inactive']) as Asset['status'],
            complianceScore: faker.number.int({ min: 40, max: 100 }),
            lastCheckin: faker.date.recent({ days: 30 }),
            owner: faker.person.fullName(),
            serialNumber: faker.vehicle.vin(),
            ipAddress: faker.internet.ipv4(),
            diskEncryption: faker.datatype.boolean(),
            firewallEnabled: faker.datatype.boolean(0.9),
            installedApps: installed,
            dexScore,
            bootTime,
            carbonFootprint: carbon,
            userSentiment: faker.helpers.arrayElement(['Positive', 'Positive', 'Neutral', 'Negative']) as Asset['userSentiment'],
        };
    });
};

export const generateChangeRequests = (count: number): ChangeRequest[] => {
    return Array.from({ length: count }, () => ({
        id: faker.string.uuid(),
        ticketNumber: `CHG-${faker.number.int({ min: 10000, max: 99999 })}`,
        title: faker.helpers.arrayElement(['Upgrade Windows 11 Fleet', 'Deploy Chrome Patch 122', 'Retire Legacy VPN', 'Install CrowdStrike Sensor', 'Update Zoom Globally']),
        description: faker.lorem.sentence(),
        requester: faker.person.fullName(),
        status: faker.helpers.arrayElement(['New', 'Assessing', 'CAB Review', 'Approved', 'Rejected', 'Scheduled', 'Completed']) as ChangeRequest['status'],
        priority: faker.helpers.arrayElement(['Low', 'Medium', 'High', 'Critical']) as ChangeRequest['priority'],
        riskScore: faker.number.int({ min: 10, max: 90 }),
        impact: faker.helpers.arrayElement(['Individual', 'Department', 'Global']) as ChangeRequest['impact'],
        createdDate: faker.date.past(),
        scheduledDate: faker.date.future(),
    }));
};

export const generateAuditLogs = (count: number): AuditLog[] => {
    return Array.from({ length: count }, () => ({
        id: faker.string.uuid(),
        timestamp: faker.date.recent({ days: 7 }),
        actor: faker.person.fullName(),
        action: faker.helpers.arrayElement(['User Login', 'Deployment Created', 'Policy Modified', 'Asset Retired', 'API Key Generated']),
        resource: faker.string.alphanumeric(8).toUpperCase(),
        details: 'Operation completed successfully.',
        status: faker.helpers.arrayElement(['Success', 'Success', 'Success', 'Failure']) as AuditLog['status'],
        ipAddress: faker.internet.ipv4(),
    }));
}

// Singleton Mock Database
class MockDatabase {
    assets: Asset[] = [];
    applications: Application[] = [];
    changes: ChangeRequest[] = [];
    auditLogs: AuditLog[] = [];

    constructor() {
        console.log('Seeding Mock Database...');
        this.applications = appsPool;
        this.assets = generateAssets(50000);
        this.changes = generateChangeRequests(50);
        this.auditLogs = generateAuditLogs(500);
        console.log(`Seeded ${this.assets.length} assets, ${this.applications.length} apps, ${this.changes.length} changes.`);
    }

    getAssets(page: number, pageSize: number) {
        const start = (page - 1) * pageSize;
        return {
            data: this.assets.slice(start, start + pageSize),
            total: this.assets.length
        };
    }
}

export const mockDb = new MockDatabase();
