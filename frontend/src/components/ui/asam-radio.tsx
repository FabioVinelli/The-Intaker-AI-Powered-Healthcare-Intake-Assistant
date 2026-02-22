import React from 'react';
import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';

import { Button } from '@/components/ui/button';

interface Option {
    value: string;
    label: string;
}

interface ASAMRadioProps {
    label: string;
    options: (string | Option)[];
    value?: string;
    onChange?: (value: string) => void;
    onConfirm?: () => void;
    className?: string;
}

export const ASAMRadio: React.FC<ASAMRadioProps> = ({
    label,
    options,
    value,
    onChange,
    onConfirm,
    className,
}) => {
    // Normalize options to objects
    const normalizedOptions: Option[] = options.map((opt) =>
        typeof opt === 'string' ? { value: opt, label: opt } : opt
    );

    return (
        <div className={cn("w-full space-y-3 p-4 border rounded-lg bg-card/50", className)}>
            <Label className="text-base font-medium block mb-2">{label}</Label>
            <div className="space-y-2">
                {normalizedOptions.map((option) => (
                    <label
                        key={option.value}
                        className={cn(
                            "flex items-center space-x-3 p-3 rounded-md border cursor-pointer transition-all hover:bg-muted/50",
                            value === option.value ? "border-primary bg-primary/5" : "border-transparent bg-secondary/50"
                        )}
                    >
                        <input
                            type="radio"
                            name={label} // Ensure grouping works
                            value={option.value}
                            checked={value === option.value}
                            onChange={() => onChange?.(option.value)}
                            className="h-4 w-4 text-primary border-gray-300 focus:ring-primary accent-primary"
                        />
                        <span className="text-sm font-medium">{option.label}</span>
                    </label>
                ))}
            </div>
            {onConfirm && (
                <div className="flex justify-end pt-2">
                    <Button
                        size="sm"
                        onClick={onConfirm}
                        disabled={!value}
                        className="bg-primary/90 hover:bg-primary transition-colors"
                    >
                        Confirm Selection
                    </Button>
                </div>
            )}
        </div>
    );
};
