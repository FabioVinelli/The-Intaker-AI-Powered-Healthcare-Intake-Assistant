import React from 'react';
import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';

import { Button } from '@/components/ui/button';

interface ASAMSliderProps {
    label: string;
    min?: number;
    max?: number;
    step?: number;
    value?: number;
    onChange?: (value: number) => void;
    onConfirm?: () => void;
    className?: string;
}

export const ASAMSlider: React.FC<ASAMSliderProps> = ({
    label,
    min = 0,
    max = 4,
    step = 1,
    value,
    onChange,
    onConfirm,
    className,
}) => {
    const [localValue, setLocalValue] = React.useState(value || min);

    React.useEffect(() => {
        if (value !== undefined) {
            setLocalValue(value);
        }
    }, [value]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = Number(e.target.value);
        setLocalValue(newVal);
        if (onChange) {
            onChange(newVal);
        }
    };

    return (
        <div className={cn("w-full space-y-4 p-4 border rounded-lg bg-card/50", className)}>
            <div className="flex justify-between items-center">
                <Label className="text-base font-medium">{label}</Label>
                <span className="text-lg font-bold text-primary">{localValue}</span>
            </div>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={localValue}
                onChange={handleChange}
                className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
                <span>Low ({min})</span>
                <span>High ({max})</span>
            </div>
            {onConfirm && (
                <div className="flex justify-end pt-2">
                    <Button
                        size="sm"
                        onClick={onConfirm}
                        className="bg-primary/90 hover:bg-primary transition-colors"
                    >
                        Confirm Value
                    </Button>
                </div>
            )}
        </div>
    );
};
