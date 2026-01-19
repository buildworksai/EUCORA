import { useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SkeletonCard } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useEvidencePack } from '@/lib/api/hooks/useEvidence';
import { 
    FileText, 
    Shield, 
    Package, 
    AlertTriangle, 
    CheckCircle2, 
    XCircle,
    Download,
    Copy,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function EvidenceViewer() {
    const { id } = useParams<{ id: string }>();
    const { data: evidencePack, isLoading, error } = useEvidencePack(id || '');

    const copyToClipboard = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        toast.success(`${label} copied to clipboard`);
    };

    if (!id) {
        return (
            <EmptyState
                icon={FileText}
                title="Evidence Pack ID Required"
                description="Please provide a valid evidence pack correlation ID"
            />
        );
    }

    if (isLoading) {
        return (
            <div className="space-y-6">
                <SkeletonCard />
                <SkeletonCard />
            </div>
        );
    }

    if (error || !evidencePack) {
        return (
            <EmptyState
                icon={FileText}
                title="Evidence Pack Not Found"
                description={error instanceof Error ? error.message : 'The requested evidence pack could not be found'}
            />
        );
    }

    // Parse vulnerability scan results
    const vulnResults = evidencePack.vulnerability_scan_results || {};
    const getVulnCount = (key: string): number => {
        if (typeof vulnResults === 'object' && vulnResults !== null && key in vulnResults) {
            const value = vulnResults[key];
            return typeof value === 'number' ? value : 0;
        }
        return 0;
    };
    const criticalVulns = getVulnCount('critical');
    const highVulns = getVulnCount('high');
    const mediumVulns = getVulnCount('medium');
    const lowVulns = getVulnCount('low');

    // Parse SBOM data
    const sbomData = evidencePack.sbom_data || {};
    const packages = (sbomData.packages || []) as Array<{
        name: string;
        version: string;
        type?: string;
        purl?: string;
    }>;

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Evidence Pack</h2>
                <p className="text-muted-foreground">
                    Complete evidence for {evidencePack.app_name} v{evidencePack.version}
                </p>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card className="glass">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <Package className="h-4 w-4" />
                            Artifact
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Hash:</span>
                                <div className="flex items-center gap-2">
                                    <span className="font-mono text-xs">{evidencePack.artifact_hash.slice(0, 16)}...</span>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => copyToClipboard(evidencePack.artifact_hash, 'Hash')}
                                        className="h-6 w-6 p-0"
                                        aria-label="Copy hash"
                                    >
                                        <Copy className="h-3 w-3" />
                                    </Button>
                                </div>
                            </div>
                            {evidencePack.artifact_signature && (
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Signature:</span>
                                    <Badge variant="outline">Signed</Badge>
                                </div>
                            )}
                            {evidencePack.artifact_path && (
                                <Button variant="outline" size="sm" className="w-full mt-2">
                                    <Download className="mr-2 h-4 w-4" />
                                    Download Artifact
                                </Button>
                            )}
                        </div>
                    </CardContent>
                </Card>

                <Card className="glass">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <Shield className="h-4 w-4" />
                            Validation Status
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            <Badge variant={evidencePack.is_validated ? 'default' : 'destructive'} className="text-sm">
                                {evidencePack.is_validated ? (
                                    <>
                                        <CheckCircle2 className="mr-1 h-3 w-3" />
                                        Validated
                                    </>
                                ) : (
                                    <>
                                        <XCircle className="mr-1 h-3 w-3" />
                                        Invalid
                                    </>
                                )}
                            </Badge>
                            <div className="text-xs text-muted-foreground">
                                {evidencePack.scan_policy_decision && (
                                    <span>Policy: {evidencePack.scan_policy_decision}</span>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="glass">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4" />
                            Vulnerabilities
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-1 text-sm">
                            {criticalVulns > 0 && (
                                <div className="flex justify-between text-destructive">
                                    <span>Critical:</span>
                                    <span className="font-bold">{criticalVulns}</span>
                                </div>
                            )}
                            {highVulns > 0 && (
                                <div className="flex justify-between text-eucora-gold">
                                    <span>High:</span>
                                    <span className="font-bold">{highVulns}</span>
                                </div>
                            )}
                            {mediumVulns > 0 && (
                                <div className="flex justify-between text-muted-foreground">
                                    <span>Medium:</span>
                                    <span>{mediumVulns}</span>
                                </div>
                            )}
                            {lowVulns > 0 && (
                                <div className="flex justify-between text-muted-foreground">
                                    <span>Low:</span>
                                    <span>{lowVulns}</span>
                                </div>
                            )}
                            {criticalVulns === 0 && highVulns === 0 && mediumVulns === 0 && lowVulns === 0 && (
                                <div className="text-muted-foreground">No vulnerabilities found</div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Tabs */}
            <Tabs defaultValue="sbom" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="sbom">SBOM</TabsTrigger>
                    <TabsTrigger value="vulnerabilities">Vulnerabilities</TabsTrigger>
                    <TabsTrigger value="rollback">Rollback Plan</TabsTrigger>
                </TabsList>

                <TabsContent value="sbom" className="space-y-4">
                    <Card className="glass">
                        <CardHeader>
                            <CardTitle>Software Bill of Materials (SBOM)</CardTitle>
                            <CardDescription>
                                Complete list of software components and dependencies
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {packages.length > 0 ? (
                                <ScrollArea className="h-[400px]">
                                    <div className="space-y-2">
                                        {packages.map((pkg, index) => (
                                            <div
                                                key={index}
                                                className="flex items-center justify-between p-3 border rounded-lg"
                                            >
                                                <div>
                                                    <div className="font-medium">{pkg.name}</div>
                                                    <div className="text-sm text-muted-foreground">
                                                        Version: {pkg.version}
                                                        {pkg.type && ` • Type: ${pkg.type}`}
                                                    </div>
                                                    {pkg.purl && (
                                                        <div className="text-xs font-mono text-muted-foreground mt-1">
                                                            {pkg.purl}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </ScrollArea>
                            ) : (
                                <div className="text-center py-8 text-muted-foreground">
                                    No SBOM data available
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="vulnerabilities" className="space-y-4">
                    <Card className="glass">
                        <CardHeader>
                            <CardTitle>Vulnerability Scan Results</CardTitle>
                            <CardDescription>
                                Detailed vulnerability assessment from security scanning
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {Object.keys(vulnResults).length > 0 ? (
                                    <ScrollArea className="h-[400px]">
                                        <pre className="text-xs font-mono bg-muted p-4 rounded-lg overflow-auto">
                                            {JSON.stringify(vulnResults, null, 2)}
                                        </pre>
                                    </ScrollArea>
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground">
                                        No vulnerability scan results available
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="rollback" className="space-y-4">
                    <Card className="glass">
                        <CardHeader>
                            <CardTitle>Rollback Plan</CardTitle>
                            <CardDescription>
                                Documented procedure for rolling back this deployment
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {evidencePack.rollback_plan ? (
                                <ScrollArea className="h-[400px]">
                                    <div className="prose prose-sm dark:prose-invert max-w-none">
                                        <pre className="whitespace-pre-wrap text-sm font-mono bg-muted p-4 rounded-lg">
                                            {typeof evidencePack.rollback_plan === 'string'
                                                ? evidencePack.rollback_plan
                                                : JSON.stringify(evidencePack.rollback_plan, null, 2)}
                                        </pre>
                                    </div>
                                </ScrollArea>
                            ) : (
                                <div className="text-center py-8 text-muted-foreground">
                                    No rollback plan available
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
