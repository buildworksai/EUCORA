import { CheckCircle, Circle, XCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Ring {
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    successRate?: number;
}

interface RingProgressIndicatorProps {
    rings: Ring[];
    className?: string; // Add className prop
}

export function RingProgressIndicator({ rings, className }: RingProgressIndicatorProps) {
    return (
        <div className={cn("flex flex-wrap items-center gap-4", className)}>
            {rings.map((ring, index) => (
                <div key={ring.name} className="flex items-center gap-2">
                    {/* Ring status icon */}
                    <div className={cn(
                        'flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300',
                        ring.status === 'completed' && 'bg-eucora-green/20 border-eucora-green',
                        ring.status === 'in_progress' && 'bg-eucora-teal/20 border-eucora-teal animate-pulse',
                        ring.status === 'failed' && 'bg-eucora-red/20 border-eucora-red',
                        ring.status === 'pending' && 'bg-muted border-muted-foreground/30'
                    )}>
                        {ring.status === 'completed' && <CheckCircle className="w-6 h-6 text-eucora-green" />}
                        {ring.status === 'in_progress' && <Clock className="w-6 h-6 text-eucora-teal" />}
                        {ring.status === 'failed' && <XCircle className="w-6 h-6 text-eucora-red" />}
                        {ring.status === 'pending' && <Circle className="w-6 h-6 text-muted-foreground/50" />}
                    </div>

                    {/* Ring name and success rate */}
                    <div className="flex flex-col">
                        <span className="text-sm font-semibold">{ring.name}</span>
                        {ring.successRate !== undefined && (
                            <span className="text-xs text-muted-foreground">
                                {ring.successRate.toFixed(1)}% success
                            </span>
                        )}
                    </div>

                    {/* Connector line to next ring */}
                    {index < rings.length - 1 && (
                        <div className={cn(
                            'hidden md:block w-8 h-0.5 mx-2 rounded-full',
                            ring.status === 'completed' ? 'bg-eucora-green' : 'bg-muted-foreground/20'
                        )} />
                    )}
                </div>
            ))}
        </div>
    );
}
