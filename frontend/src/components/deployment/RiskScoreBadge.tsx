import { Badge } from '@/components/ui/badge';

interface RiskScoreBadgeProps {
    score: number | null;
}

export function RiskScoreBadge({ score }: RiskScoreBadgeProps) {
    if (score === null) return <Badge variant="outline">Not Scored</Badge>;

    const getVariant = () => {
        if (score <= 30) return 'outline'; // Low risk, standard outline or custom success style.
        if (score <= 50) return 'outline'; // Use Outline but color it via className
        return 'destructive';
    };

    const getColorClass = () => {
        if (score <= 30) return 'text-eucora-green border-eucora-green bg-eucora-green/10';
        if (score <= 50) return 'text-eucora-gold border-eucora-gold bg-eucora-gold/10';
        return 'bg-eucora-red text-white border-eucora-red';
    }

    const getLabel = () => {
        if (score <= 30) return 'Low Risk';
        if (score <= 50) return 'Medium Risk';
        return 'High Risk (CAB Required)';
    };

    return (
        <Badge variant={getVariant()} className={`font-semibold ${getColorClass()}`}>
            {score} - {getLabel()}
        </Badge>
    );
}
