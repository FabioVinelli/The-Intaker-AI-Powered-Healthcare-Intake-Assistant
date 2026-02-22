import React from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, AlertTriangle, CheckCircle, Activity, Sparkles, Shield } from 'lucide-react';
import { ASAMScoreChart } from './ASAMScoreChart';
import { clsx } from 'clsx';

export interface IntakeResultData {
    asam_scores: Record<string, number>;
    level_of_care: string;
    suggested_plan: string;
}

interface IntakeResultPanelProps {
    result: IntakeResultData;
    onClose: () => void;
}

/**
 * Level of Care color mapping:
 * - L0.5/Outpatient: Emerald (Green) - Lowest intensity
 * - L1/Intensive: Sky Blue
 * - L2/Partial: Amber
 * - L3/Residential: Rose/Red - High intensity
 * - L4/Inpatient: Red - Highest intensity
 */
const getLOCConfig = (loc: string): {
    bgColor: string;
    textColor: string;
    borderColor: string;
    glowColor: string;
    gradient: string;
} => {
    const level = loc.toLowerCase();
    if (level.includes('0.5') || level.includes('outpatient')) {
        return {
            bgColor: 'bg-emerald-500',
            textColor: 'text-emerald-300',
            borderColor: 'border-emerald-400/30',
            glowColor: 'shadow-emerald-500/30',
            gradient: 'from-emerald-500/20 to-emerald-500/5'
        };
    }
    if (level.includes('1') || level.includes('intensive')) {
        return {
            bgColor: 'bg-sky-500',
            textColor: 'text-sky-300',
            borderColor: 'border-sky-400/30',
            glowColor: 'shadow-sky-500/30',
            gradient: 'from-sky-500/20 to-sky-500/5'
        };
    }
    if (level.includes('2') || level.includes('partial')) {
        return {
            bgColor: 'bg-amber-500',
            textColor: 'text-amber-300',
            borderColor: 'border-amber-400/30',
            glowColor: 'shadow-amber-500/30',
            gradient: 'from-amber-500/20 to-amber-500/5'
        };
    }
    if (level.includes('3') || level.includes('residential')) {
        return {
            bgColor: 'bg-rose-500',
            textColor: 'text-rose-300',
            borderColor: 'border-rose-400/30',
            glowColor: 'shadow-rose-500/30',
            gradient: 'from-rose-500/20 to-rose-500/5'
        };
    }
    if (level.includes('4') || level.includes('inpatient')) {
        return {
            bgColor: 'bg-red-600',
            textColor: 'text-red-300',
            borderColor: 'border-red-400/30',
            glowColor: 'shadow-red-600/30',
            gradient: 'from-red-600/20 to-red-600/5'
        };
    }
    return {
        bgColor: 'bg-sky-500',
        textColor: 'text-sky-300',
        borderColor: 'border-sky-400/30',
        glowColor: 'shadow-sky-500/30',
        gradient: 'from-sky-500/20 to-sky-500/5'
    };
};

const getLOCIcon = (loc: string) => {
    const level = loc.toLowerCase();
    if (level.includes('0.5') || level.includes('outpatient')) return CheckCircle;
    if (level.includes('3') || level.includes('residential')) return AlertTriangle;
    if (level.includes('4') || level.includes('inpatient')) return AlertTriangle;
    return Activity;
};

// Animation variants
const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 }
};

const modalVariants = {
    hidden: {
        opacity: 0,
        scale: 0.9,
        y: 20
    },
    visible: {
        opacity: 1,
        scale: 1,
        y: 0,
        transition: {
            type: "spring",
            stiffness: 300,
            damping: 30
        }
    },
    exit: {
        opacity: 0,
        scale: 0.95,
        y: 10,
        transition: { duration: 0.2 }
    }
};

const contentVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
            delayChildren: 0.2
        }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: "easeOut" }
    }
};

export const IntakeResultPanel: React.FC<IntakeResultPanelProps> = ({ result, onClose }) => {
    const LOCIcon = getLOCIcon(result.level_of_care);
    const locConfig = getLOCConfig(result.level_of_care);

    return (
        <AnimatePresence>
            {/* Backdrop with blur */}
            <motion.div
                className="fixed inset-0 z-[100] flex items-center justify-center p-4"
                variants={backdropVariants}
                initial="hidden"
                animate="visible"
                exit="hidden"
            >
                {/* Glassmorphism Backdrop */}
                <div className="absolute inset-0 bg-black/70 backdrop-blur-xl" onClick={onClose} />

                {/* Ambient glow effects */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
                    <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
                </div>

                {/* Modal Container - Crystal Glass Effect */}
                <motion.div
                    className={clsx(
                        // Glassmorphism container
                        "relative bg-black/40 backdrop-blur-2xl",
                        "border border-white/10",
                        "rounded-3xl w-full max-w-5xl max-h-[90vh] overflow-hidden",
                        // Premium shadow
                        "shadow-2xl shadow-black/50",
                        // Inner glow
                        "before:absolute before:inset-0 before:rounded-3xl before:bg-gradient-to-br before:from-white/10 before:via-transparent before:to-transparent before:pointer-events-none",
                        "flex flex-col"
                    )}
                    variants={modalVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                >
                    {/* Header */}
                    <motion.div
                        className="relative p-6 border-b border-white/10 flex justify-between items-center bg-gradient-to-r from-white/5 to-transparent"
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-gradient-to-br from-blue-500/30 to-purple-500/20 rounded-2xl border border-white/10 backdrop-blur-sm">
                                <Sparkles className="text-blue-400" size={24} />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-white tracking-tight">
                                    Intake Assessment Complete
                                </h2>
                                <p className="text-sm text-white/50 mt-0.5 flex items-center gap-2">
                                    <Shield size={12} className="text-emerald-400" />
                                    ASAM-based treatment recommendation generated
                                </p>
                            </div>
                        </div>
                        <motion.button
                            onClick={onClose}
                            className="p-2.5 text-white/50 hover:text-white hover:bg-white/10 rounded-xl transition-all border border-transparent hover:border-white/10"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <X size={22} />
                        </motion.button>
                    </motion.div>

                    {/* Content */}
                    <motion.div
                        className="flex-1 overflow-y-auto p-6"
                        variants={contentVariants}
                        initial="hidden"
                        animate="visible"
                    >
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                            {/* Left Column: Scores */}
                            <div className="space-y-6">
                                {/* Level of Care Badge - Prominent & Color-coded */}
                                <motion.div
                                    className={clsx(
                                        'p-5 rounded-2xl border backdrop-blur-sm',
                                        'flex items-center gap-4',
                                        `bg-gradient-to-r ${locConfig.gradient}`,
                                        locConfig.borderColor,
                                        'shadow-lg',
                                        locConfig.glowColor
                                    )}
                                    variants={itemVariants}
                                >
                                    <motion.div
                                        className={clsx(
                                            'p-4 rounded-2xl shadow-lg',
                                            locConfig.bgColor,
                                            locConfig.glowColor
                                        )}
                                        initial={{ rotate: -10, scale: 0 }}
                                        animate={{ rotate: 0, scale: 1 }}
                                        transition={{
                                            type: "spring",
                                            stiffness: 400,
                                            damping: 15,
                                            delay: 0.3
                                        }}
                                    >
                                        <LOCIcon className="text-white" size={28} />
                                    </motion.div>
                                    <div>
                                        <p className="text-xs text-white/50 uppercase tracking-widest font-medium">
                                            Recommended Level of Care
                                        </p>
                                        <p className={clsx(
                                            'text-xl font-bold mt-1 tracking-tight',
                                            locConfig.textColor
                                        )}>
                                            {result.level_of_care}
                                        </p>
                                    </div>
                                </motion.div>

                                {/* ASAM Score Chart */}
                                <motion.div
                                    className="p-6 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm"
                                    variants={itemVariants}
                                >
                                    <ASAMScoreChart scores={result.asam_scores} />
                                </motion.div>
                            </div>

                            {/* Right Column: Treatment Plan */}
                            <motion.div
                                className="p-6 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm flex flex-col"
                                variants={itemVariants}
                            >
                                <h3 className="text-lg font-semibold text-white/90 mb-5 flex items-center gap-2.5 pb-4 border-b border-white/10">
                                    <div className="p-2 bg-blue-500/20 rounded-lg">
                                        <FileText size={16} className="text-blue-400" />
                                    </div>
                                    Treatment Plan
                                </h3>
                                {/* 
                                    prose-invert for dark mode typography
                                    Custom component overrides for clean, readable Markdown
                                */}
                                <div className="flex-1 overflow-y-auto prose prose-invert prose-sm max-w-none">
                                    <ReactMarkdown
                                        components={{
                                            h1: ({ children }) => (
                                                <h1 className="text-xl font-bold text-white mb-4 mt-2 tracking-tight">
                                                    {children}
                                                </h1>
                                            ),
                                            h2: ({ children }) => (
                                                <h2 className="text-lg font-semibold text-white/90 mb-3 mt-6 pb-2 border-b border-white/10">
                                                    {children}
                                                </h2>
                                            ),
                                            h3: ({ children }) => (
                                                <h3 className="text-base font-medium text-white/80 mb-2 mt-4">
                                                    {children}
                                                </h3>
                                            ),
                                            p: ({ children }) => (
                                                <p className="text-white/70 mb-4 leading-relaxed text-sm">
                                                    {children}
                                                </p>
                                            ),
                                            ul: ({ children }) => (
                                                <ul className="list-none text-white/70 mb-4 space-y-2 text-sm">
                                                    {children}
                                                </ul>
                                            ),
                                            li: ({ children }) => (
                                                <li className="text-white/70 flex items-start gap-2">
                                                    <span className="text-blue-400 mt-1.5">•</span>
                                                    <span>{children}</span>
                                                </li>
                                            ),
                                            strong: ({ children }) => (
                                                <strong className="text-white font-semibold">
                                                    {children}
                                                </strong>
                                            ),
                                            em: ({ children }) => (
                                                <em className="text-white/80 italic">
                                                    {children}
                                                </em>
                                            ),
                                            blockquote: ({ children }) => (
                                                <blockquote className="border-l-2 border-blue-400/50 pl-4 my-4 text-white/60 italic">
                                                    {children}
                                                </blockquote>
                                            ),
                                        }}
                                    >
                                        {result.suggested_plan}
                                    </ReactMarkdown>
                                </div>
                            </motion.div>
                        </div>
                    </motion.div>

                    {/* Footer */}
                    <motion.div
                        className="p-6 border-t border-white/10 bg-gradient-to-r from-white/5 to-transparent flex justify-between items-center"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                    >
                        <p className="text-xs text-white/40 flex items-center gap-2">
                            <Shield size={12} className="text-emerald-400/60" />
                            Assessment generated by The Intaker AI • Review with clinical staff before finalizing
                        </p>
                        <div className="flex gap-3">
                            <motion.button
                                onClick={onClose}
                                className="px-6 py-2.5 bg-white/5 hover:bg-white/10 text-white/80 hover:text-white rounded-xl font-medium transition-all border border-white/10 backdrop-blur-sm"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                Close
                            </motion.button>
                            <motion.button
                                onClick={onClose}
                                className={clsx(
                                    "px-6 py-2.5 rounded-xl font-medium transition-all",
                                    "bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400",
                                    "text-white shadow-lg shadow-blue-500/25",
                                    "border border-blue-400/20"
                                )}
                                whileHover={{ scale: 1.02, boxShadow: "0 10px 40px rgba(59, 130, 246, 0.3)" }}
                                whileTap={{ scale: 0.98 }}
                            >
                                Archive & Reset
                            </motion.button>
                        </div>
                    </motion.div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};
