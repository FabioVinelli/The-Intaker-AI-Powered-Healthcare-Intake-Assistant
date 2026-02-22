import React, { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { ASAMSlider } from '@/components/ui/asam-slider';
import { ASAMRadio } from '@/components/ui/asam-radio';
import { Card } from '@/components/ui/card';
import { AlertTriangle } from 'lucide-react';

interface A2UIParserProps {
    content: string;
    onValueSubmit?: (label: string, value: any) => void;
}

interface A2UIData {
    type: 'slider' | 'radio' | 'checkbox' | 'info';
    label: string;
    min?: number;
    max?: number;
    step?: number;
    options?: Array<string | { value: string; label: string }>;
    defaultValue?: any;
}

export const A2UIParser: React.FC<A2UIParserProps> = ({ content, onValueSubmit }) => {
    // We use regex to split the content into the main text and the A2UI JSON block
    const { text, uiData } = useMemo(() => {
        const a2uiRegex = /<a2ui>([\s\S]*?)<\/a2ui>/;
        const match = content.match(a2uiRegex);

        if (match) {
            const textPart = content.replace(match[0], '').trim();
            const jsonStr = match[1];
            try {
                const parsed = JSON.parse(jsonStr) as A2UIData;
                return { text: textPart, uiData: parsed };
            } catch (e) {
                console.error("Failed to parse A2UI JSON:", e);
                // If parsing fails, we just return the text and ignore the corrupted tag
                // potentially rendering an error state if we want to be strict
                return { text: textPart, uiData: null };
            }
        }

        return { text: content, uiData: null };
    }, [content]);

    // Handle widget state internally or lift it up?
    // For this tasks's scope, the "widget" pops up. Usually we'd want to send the answer back.
    // The prompt implies we just *render* it. The actual "Answer" logic might be separate.
    // We'll keep local state for validity.
    const [value, setValue] = useState<any>(uiData?.defaultValue);
    const [isSubmitted, setIsSubmitted] = useState(false);

    // If the parsed data changes, reset value?
    // In a real stream, the same message ID would keep appending.
    // The 'content' prop changes as the stream arrives. The JSON block arrives at the END.
    // So 'uiData' will be null until the very end of the stream for that message.

    if (!uiData) {
        return <span className="whitespace-pre-wrap">{text}</span>;
    }

    const handleConfirm = () => {
        setIsSubmitted(true);
        if (onValueSubmit) {
            onValueSubmit(uiData.label, value);
        }
    };

    const renderWidget = () => {
        switch (uiData.type) {
            case 'slider':
                return (
                    <ASAMSlider
                        label={uiData.label}
                        min={uiData.min}
                        max={uiData.max}
                        step={uiData.step}
                        value={value}
                        onChange={setValue}
                        onConfirm={!isSubmitted ? handleConfirm : undefined}
                        className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
                    />
                );
            case 'radio':
                return (
                    <ASAMRadio
                        label={uiData.label}
                        options={uiData.options || []}
                        value={value}
                        onChange={setValue}
                        onConfirm={!isSubmitted ? handleConfirm : undefined}
                        className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
                    />
                );
            case 'checkbox':
                // Reuse radio for now or implement checkbox group if needed. 
                // Instructions only asked for ASAMSlider and ASAMRadio, but schema mentions checkbox.
                // We'll fallback to radio for MVP or just a "Not Implemented" placeholder safely.
                return (
                    <ASAMRadio
                        label={uiData.label + " (Select all that apply - Mock)"}
                        options={uiData.options || []}
                        value={value}
                        onChange={setValue}
                        onConfirm={!isSubmitted ? handleConfirm : undefined}
                        className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300"
                    />
                );
            case 'info':
                return (
                    <Card className="mt-4 p-4 bg-muted/50 border-l-4 border-l-primary">
                        <p className="font-medium text-sm">{uiData.label}</p>
                    </Card>
                )
            default:
                return (
                    <div className="mt-4 p-3 border border-yellow-200 bg-yellow-50 rounded text-yellow-800 text-xs flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        Unknown widget type: {uiData.type}
                    </div>
                );
        }
    };

    return (
        <div className="flex flex-col space-y-3">
            <span className="whitespace-pre-wrap">{text}</span>
            <div className={isSubmitted ? "opacity-50 pointer-events-none grayscale" : ""}>
                {renderWidget()}
            </div>

            {isSubmitted && (
                <div className="text-xs text-muted-foreground text-right italic">
                    Selection submitted
                </div>
            )}
        </div>
    );
};
