import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { LoadingButton } from '@/components/ui/loading-button';
import { ArrowLeft, ArrowRight, Check, UploadCloud, AlertCircle } from 'lucide-react';
import { useCreateDeployment } from '@/lib/api/hooks/useDeployments';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';

// Form validation schema
const deploymentSchema = z.object({
    appName: z.string().min(1, 'Application name is required').max(100, 'Application name must be less than 100 characters'),
    version: z.string().regex(/^\d+\.\d+\.\d+/, 'Version must be in semver format (e.g., 1.0.0)'),
    targetRing: z.enum(['LAB', 'CANARY', 'PILOT'], {
        message: 'Target ring is required',
    }),
    evidenceFile: z.instanceof(File).optional(),
});

type DeploymentFormData = z.infer<typeof deploymentSchema>;

export default function DeploymentWizard() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const createDeployment = useCreateDeployment();

    const form = useForm<DeploymentFormData>({
        resolver: zodResolver(deploymentSchema),
        defaultValues: {
            appName: '',
            version: '',
            targetRing: 'CANARY',
        },
        mode: 'onChange',
    });

    // React Hook Form exposes watch as a mutable API; lint rule needs explicit opt-out here.
    // eslint-disable-next-line react-hooks/incompatible-library
    const watchedValues = form.watch();
    const appName = watchedValues.appName || '';

    // Mock Risk Analysis (in production, this would call the backend)
    const riskScore = appName.toLowerCase().includes('critical') ? 75 : 15;

    const handleNext = async () => {
        // Validate current step before proceeding
        let fieldsToValidate: (keyof DeploymentFormData)[] = [];
        
        if (step === 1) {
            fieldsToValidate = ['appName', 'version'];
        } else if (step === 2) {
            fieldsToValidate = ['targetRing'];
        }

        const isValid = await form.trigger(fieldsToValidate);
        if (isValid) {
            setStep((p) => Math.min(p + 1, 4));
        }
    };

    const handleBack = () => setStep((p) => Math.max(p - 1, 1));

    const handleSubmit = async (data: DeploymentFormData) => {
        try {
            const result = await createDeployment.mutateAsync({
                app_name: data.appName,
                version: data.version,
                target_ring: data.targetRing,
                evidence_pack: {
                    // Evidence pack would be uploaded separately or included here
                    // For now, we'll create deployment and evidence pack can be added later
                },
            });

            toast.success('Deployment created successfully', {
                description: `Correlation ID: ${result.correlation_id}`,
            });

            navigate('/dashboard');
        } catch (error) {
            // Error is already handled by the mutation
            console.error('Failed to create deployment:', error);
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">New Deployment</h2>
                <p className="text-muted-foreground">Create a deployment intent for the packaging factory.</p>
            </div>

            {/* Stepper */}
            <div className="flex items-center space-x-4 mb-4">
                {[1, 2, 3, 4].map((s) => (
                    <div key={s} className="flex items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 transition-colors ${
                            step >= s ? 'bg-primary border-primary text-primary-foreground' : 'border-muted text-muted-foreground'
                        }`}>
                            {s}
                        </div>
                        {s < 4 && <div className={`w-12 h-1 mx-2 rounded ${step > s ? 'bg-primary' : 'bg-muted'}`} />}
                    </div>
                ))}
            </div>

            <Form {...form}>
                <form onSubmit={form.handleSubmit(handleSubmit)}>
                    <Card className="glass">
                        <CardHeader>
                            <CardTitle>
                                {step === 1 && 'Select Application'}
                                {step === 2 && 'Configuration'}
                                {step === 3 && 'Risk Analysis'}
                                {step === 4 && 'Review & Submit'}
                            </CardTitle>
                            <CardDescription>
                                {step === 1 && 'Choose the application package to deploy.'}
                                {step === 2 && 'Configure target ring and deployment strategy.'}
                                {step === 3 && 'Automated risk assessment based on change impact.'}
                                {step === 4 && 'Verify all details before initiating deployment.'}
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4 min-h-[300px]">
                            {step === 1 && (
                                <div className="space-y-4">
                                    <FormField
                                        control={form.control}
                                        name="appName"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Application Name</FormLabel>
                                                <FormControl>
                                                    <Input
                                                        placeholder="e.g. Adobe Acrobat Reader"
                                                        {...field}
                                                        aria-label="Application name"
                                                    />
                                                </FormControl>
                                                <FormDescription>
                                                    Enter the name of the application to deploy
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="version"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Version</FormLabel>
                                                <FormControl>
                                                    <Input
                                                        placeholder="e.g. 24.001.20604"
                                                        {...field}
                                                        aria-label="Version"
                                                    />
                                                </FormControl>
                                                <FormDescription>
                                                    Version must be in semver format (e.g., 1.0.0)
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="evidenceFile"
                                        render={({ field: { onChange, ...field } }) => (
                                            <FormItem>
                                                <FormLabel>Artifact File (Optional)</FormLabel>
                                                <FormControl>
                                                    <div className="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-muted-foreground hover:bg-muted/50 transition-colors cursor-pointer">
                                                        <UploadCloud className="h-10 w-10 mb-2" />
                                                        <span className="text-sm">Drag and drop package binaries (MSI, EXE, INTUNEWIN)</span>
                                                        <input
                                                            {...(field as React.InputHTMLAttributes<HTMLInputElement>)}
                                                            type="file"
                                                            accept=".msi,.exe,.intunewin"
                                                            onChange={(e) => {
                                                                const file = e.target.files?.[0];
                                                                onChange(file);
                                                            }}
                                                            className="mt-2"
                                                            aria-label="Upload artifact file"
                                                        />
                                                    </div>
                                                </FormControl>
                                                <FormDescription>
                                                    Upload the application package file (optional, can be added later)
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                            )}

                            {step === 2 && (
                                <div className="space-y-4">
                                    <FormField
                                        control={form.control}
                                        name="targetRing"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Target Ring</FormLabel>
                                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                    <FormControl>
                                                        <SelectTrigger aria-label="Target ring">
                                                            <SelectValue />
                                                        </SelectTrigger>
                                                    </FormControl>
                                                    <SelectContent>
                                                        <SelectItem value="LAB">Lab (Internal)</SelectItem>
                                                        <SelectItem value="CANARY">Ring 1: Canary</SelectItem>
                                                        <SelectItem value="PILOT">Ring 2: Pilot</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                                <FormDescription>
                                                    Only Lab and Canary are available for initial deployment. Pilot requires promotion.
                                                </FormDescription>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                            )}

                            {step === 3 && (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-4 p-4 border rounded-lg bg-background/50">
                                        <div className="flex-1">
                                            <h4 className="font-semibold">Calculated Risk Score</h4>
                                            <p className="text-sm text-muted-foreground">Based on app criticality and historical stability.</p>
                                        </div>
                                        <div className="text-right">
                                            <span className={`text-4xl font-bold ${riskScore > 50 ? 'text-destructive' : 'text-eucora-green'}`}>
                                                {riskScore}
                                            </span>
                                            <span className="text-muted-foreground text-sm">/100</span>
                                        </div>
                                    </div>

                                    {riskScore > 50 && (
                                        <div className="flex items-center gap-2 p-3 text-sm text-eucora-gold-dark bg-eucora-gold/10 border border-eucora-gold/20 rounded-md">
                                            <AlertCircle className="h-4 w-4" />
                                            <span>High Risk: CAB Approval will be required before promotion to Ring 2.</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {step === 4 && (
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div className="flex flex-col">
                                            <span className="text-muted-foreground">Application</span>
                                            <span className="font-medium">{watchedValues.appName}</span>
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-muted-foreground">Version</span>
                                            <span className="font-medium">{watchedValues.version}</span>
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-muted-foreground">Target Ring</span>
                                            <Badge variant="secondary">{watchedValues.targetRing}</Badge>
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-muted-foreground">Risk Score</span>
                                            <span className={riskScore > 50 ? 'text-destructive font-bold' : 'text-eucora-green font-bold'}>
                                                {riskScore}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="pt-4 border-t">
                                        <p className="text-sm text-muted-foreground">
                                            Clicking submit will initiate the CI/CD pipeline, signing process, and initial rollout to the selected ring.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                        <CardFooter className="flex justify-between">
                            <Button type="button" variant="outline" onClick={handleBack} disabled={step === 1}>
                                <ArrowLeft className="mr-2 h-4 w-4" /> Back
                            </Button>
                            {step < 4 ? (
                                <Button type="button" onClick={handleNext}>
                                    Next <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            ) : (
                                <LoadingButton
                                    type="submit"
                                    loading={createDeployment.isPending}
                                    className="bg-eucora-green hover:bg-eucora-green-dark"
                                >
                                    <Check className="mr-2 h-4 w-4" /> Submit Deployment
                                </LoadingButton>
                            )}
                        </CardFooter>
                    </Card>
                </form>
            </Form>
        </div>
    );
}
