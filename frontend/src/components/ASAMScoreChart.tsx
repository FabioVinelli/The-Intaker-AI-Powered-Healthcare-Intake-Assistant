import React from 'react';
import { motion } from 'framer-motion';
import { ASAM_DIMENSIONS } from '../constants';
import { clsx } from 'clsx';

interface ASAMScoreChartProps {
    scores: Record<string, number>;
}

/**
 * Color logic per Mission 10:
 * - 0-1: Emerald (low severity)
 * - 2-3: Amber (moderate severity)
 * - 4: Rose/Red (high severity)
 */
const getSeverityColor = (score: number): string => {
    if (score <= 1) return 'bg-emerald-400';
    if (score <= 3) return 'bg-amber-400';
    return 'bg-rose-500'; // Changed from orange to rose/red for score 4
};

const getSeverityGradient = (score: number): string => {
    if (score <= 1) return 'from-emerald-500 to-emerald-400';
    if (score <= 3) return 'from-amber-500 to-amber-400';
    return 'from-rose-600 to-rose-500';
};

const getSeverityGlow = (score: number): string => {
    if (score <= 1) return 'shadow-emerald-400/50';
    if (score <= 3) return 'shadow-amber-400/50';
    return 'shadow-rose-500/50';
};

const getSeverityLabel = (score: number): string => {
    const labels = ['None', 'Mild', 'Moderate', 'High', 'Severe'];
    return labels[Math.min(score, 4)] || 'Unknown';
};

const getBadgeClasses = (score: number): string => {
    if (score <= 1) return 'bg-emerald-400/20 text-emerald-300 border-emerald-400/30';
    if (score <= 3) return 'bg-amber-400/20 text-amber-300 border-amber-400/30';
    return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
};

export const ASAMScoreChart: React.FC<ASAMScoreChartProps> = ({ scores }) => {
    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white/90 mb-4 flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                ASAM Dimension Scores
            </h3>
            {ASAM_DIMENSIONS.map((dim, index) => {
                const dimensionKey = `Dimension.D${dim.id}`;
                const score = scores[dimensionKey] ?? scores[`D${dim.id}`] ?? 0;
                const widthPercent = ((score / 4) * 100);

                return (
                    <motion.div
                        key={dim.id}
                        className="space-y-2"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{
                            delay: index * 0.1,
                            duration: 0.4,
                            ease: "easeOut"
                        }}
                    >
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-white/80 font-medium tracking-wide">
                                D{dim.id}: {dim.short}
                            </span>
                            <motion.span
                                className={clsx(
                                    'text-xs px-2.5 py-1 rounded-full border backdrop-blur-sm font-medium',
                                    getBadgeClasses(score)
                                )}
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{
                                    delay: index * 0.1 + 0.3,
                                    type: "spring",
                                    stiffness: 400,
                                    damping: 20
                                }}
                            >
                                {getSeverityLabel(score)} ({score})
                            </motion.span>
                        </div>
                        <div className="h-3.5 bg-white/5 rounded-full overflow-hidden backdrop-blur-sm border border-white/10">
                            <motion.div
                                className={clsx(
                                    'h-full rounded-full shadow-lg bg-gradient-to-r',
                                    getSeverityGradient(score),
                                    getSeverityGlow(score)
                                )}
                                initial={{ width: '0%' }}
                                animate={{ width: `${Math.max(widthPercent, 5)}%` }}
                                transition={{
                                    delay: index * 0.1 + 0.2,
                                    duration: 0.8,
                                    ease: [0.34, 1.56, 0.64, 1] // Custom spring-like easing
                                }}
                            />
                        </div>
                    </motion.div>
                );
            })}
            <motion.p
                className="text-xs text-white/40 mt-5 pt-4 border-t border-white/5"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
            >
                Scale: 0 = None, 1 = Mild, 2 = Moderate, 3 = High, 4 = Severe
            </motion.p>
        </div>
    );
};
