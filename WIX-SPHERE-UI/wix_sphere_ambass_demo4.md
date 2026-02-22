Agent, update src/hooks/useVoiceBridge.ts to "Ambassador 7.0". Expand the Listener Logic to include specific responses for H3's core offerings: JCAHO/CARF Accreditation, Telehealth Implementation, and Network Expansion. Keep the existing Intake Script logic intact.

TypeScript
import { useState, useCallback, useRef, useEffect } from 'react';

// ==========================================
// AMBASSADOR MODE 7.0 (H3 SPECIALIST)
// 1. Expanded Knowledge Base (JCAHO, CARF, Telehealth, Network Expansion)
// 2. Specific Pitches for each service category
// 3. Retains strict "Speaker 2" script for the Intake Demo
// ==========================================

export interface IntakeResultData {
    asam_scores: Record<string, number>;
    level_of_care: string;
    suggested_plan: string;
}

export interface ScenarioData {
    scenario: string;
    language: string;
    asam_scores: Record<string, number>;
    level_of_care: string;
    level_of_care_label: string;
    keywords: string[];
    sphere_state: 'idle' | 'active' | 'escalating';
}

export interface UseVoiceBridgeReturn {
    connect: () => void;
    disconnect: () => void;
    sendFinalize: () => void;
    sendTrigger: (trigger: string) => void;
    status: 'disconnected' | 'connecting' | 'connected' | 'error';
    isSpeaking: boolean;
    voiceState: 'idle' | 'listening' | 'thinking' | 'speaking' | 'escalating';
    intakeResult: IntakeResultData | null;
    scenarioData: ScenarioData | null;
    escalationData: any;
}

// STRICT INTAKE SCRIPT (Speaker 2 Lines)
const INTAKE_SCRIPT = [
    "Hello, I'm here to help with your intake process. I'll ask some questions about your health, substances, and life circumstances. Please answer honestly; there are no right or wrong answers. Everything you share helps us create the best care plan for you. Would you like to begin?",
    "Great, let's start with dimension one, focusing on your recent substances and any potential withdrawal. Have you used any substances in the last 48 to 72 hours?",
    "Thank you for sharing that. Can you tell me a bit more about the amounts you use?",
    "I understand. On a scale from 0 to 10, where 10 is severe and 0 is none, are you currently seeing any intoxication symptoms?",
    "Thank you. And have you experienced any withdrawal symptoms like nausea, shaking, or anxiety when you haven't used?",
    "That sounds difficult. Have you ever had any severe withdrawal symptoms like seizures or hallucinations, or been hospitalized for detox?",
    "Thank you for letting me know; that's helpful context. Now I'd like to move to dimension two, which covers your physical health. Do you have any current medical conditions like diabetes, heart disease, or liver problems?",
    "I see. Is that being treated and managed?",
    "Okay, thank you. Are you currently taking any medications?",
    "That makes sense. Now I'd like to move on to dimension 3, which covers your emotional health. This can be a sensitive topic, so please feel free to take your time. Have you ever been diagnosed with any mental health conditions like depression, anxiety, or PTSD?",
    "Thank you. I have gathered the necessary information to proceed."
];

export const useVoiceBridge = (): UseVoiceBridgeReturn => {
    const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'thinking' | 'speaking' | 'escalating'>('idle');
    const [intakeResult, setIntakeResult] = useState<IntakeResultData | null>(null);
    const [scenarioData, setScenarioData] = useState<ScenarioData | null>(null);
    const [escalationData, setEscalationData] = useState<any>(null);

    const [mode, setMode] = useState<'ambassador' | 'intake'>('ambassador');
    const [scriptIndex, setScriptIndex] = useState(0);

    const recognitionRef = useRef<any>(null);
    const shouldListenRef = useRef<boolean>(false); 

    // 1. VOICE SYNTHESIS
    const speak = useCallback((text: string) => {
        if ('speechSynthesis' in window) {
            if (recognitionRef.current) recognitionRef.current.abort();
            shouldListenRef.current = false; 
            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9; 
            utterance.pitch = 1.0; 

            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v => 
                v.name.includes('Google US English') || 
                v.name.includes('Samantha')
            );
            if (preferredVoice) utterance.voice = preferredVoice;

            utterance.onstart = () => {
                setIsSpeaking(true);
                setVoiceState('speaking');
            };

            utterance.onend = () => {
                setIsSpeaking(false);
                setVoiceState('listening');
                setTimeout(() => startListening(), 250);
            };

            window.speechSynthesis.speak(utterance);
        }
    }, []);

    // 2. H3 SPECIALIST BRAIN
    const startListening = useCallback(() => {
        if (!('webkitSpeechRecognition' in window)) return;
        if (recognitionRef.current) recognitionRef.current.abort();

        const recognition = new (window as any).webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        shouldListenRef.current = true;

        recognition.onstart = () => {
            console.log(`👂 Listening (Mode: ${mode})...`);
            setVoiceState('listening');
        };

        recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript.toLowerCase();
            console.log(`🗣️ Heard: "${transcript}"`);

            // === AMBASSADOR LOGIC ===
            if (mode === 'ambassador') {
                // OFFERING 1: ACCREDITATION (JCAHO/CARF)
                if (transcript.includes('accreditation') || transcript.includes('joint commission') || transcript.includes('carf') || transcript.includes('licensing')) {
                    speak("H3 provides complete readiness preparation for JCAHO and CARF accreditation. We also handle DHCS licensing and compliance checks to ensure your facility is audit-ready.");
                }
                // OFFERING 2: AI & AUTOMATION
                else if (transcript.includes('automation') || transcript.includes('ai') || transcript.includes('intake') || transcript.includes('documentation')) {
                    speak("Our AI solutions automate patient intake, documentation compliance, and risk assessment. This reduces administrative burden and ensures your online presence is fully optimized.");
                }
                // OFFERING 3: TELEHEALTH & NETWORK EXPANSION
                else if (transcript.includes('telehealth') || transcript.includes('expansion') || transcript.includes('network') || transcript.includes('growth')) {
                    speak("We assist with Telehealth service implementation and Network Expansion, helping you reach more patients while maintaining strict compliance standards.");
                }
                // TRIGGER: INTAKE DEMO
                else if (transcript.includes('demo') || transcript.includes('test') || transcript.includes('simulate') || transcript.includes('yes')) {
                    setMode('intake');
                    setScriptIndex(0);
                    speak("Understood. I will now switch to the intake simulation. " + INTAKE_SCRIPT[0]);
                }
                // FALLBACK
                else {
                    speak("I can explain our Accreditation, AI Automation, or Network Expansion services. Or, we can run a Test Intake. Which would you prefer?");
                }
            }
            
            // === INTAKE SCRIPT LOGIC (Strict Follow) ===
            else if (mode === 'intake') {
                setScriptIndex(prev => {
                    const nextIndex = prev + 1;
                    if (nextIndex < INTAKE_SCRIPT.length) {
                        setTimeout(() => speak(INTAKE_SCRIPT[nextIndex]), 1000); 
                    } else {
                        sendFinalize();
                    }
                    return nextIndex;
                });
            }
        };

        recognition.onend = () => {
            if (status === 'connected' && shouldListenRef.current && !isSpeaking) {
                try { recognition.start(); } catch(e) {}
            }
        };

        recognitionRef.current = recognition;
        try { recognition.start(); } catch(e) {}

    }, [speak, status, isSpeaking, mode]);

    // 3. CONNECT & GREET
    const connect = useCallback(() => {
        if (status === 'connected') return;
        setStatus('connecting');
        setMode('ambassador'); 

        setTimeout(() => {
            setStatus('connected');
            setVoiceState('speaking');
            speak("Welcome to H3 Highland Health Hub Consulting. I specialize in AI Automation, Accreditation Readiness, and Telehealth Implementation. Would you like to discuss our services, or run a test intake?");
        }, 1500);
    }, [status, speak]);

    const disconnect = useCallback(() => {
        shouldListenRef.current = false;
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        if (recognitionRef.current) recognitionRef.current.abort();
        setStatus('disconnected');
        setVoiceState('idle');
        setScriptIndex(0);
        setMode('ambassador');
    }, []);

    const sendFinalize = useCallback(() => {
        setVoiceState('thinking');
        setTimeout(() => {
             setIntakeResult({
                asam_scores: { "Acute": 2, "Biomedical": 1, "Psych": 2 },
                level_of_care: "Suggestion: Level 2.1 (IOP)",
                suggested_plan: "Flagged for Clinical Director Review."
            });
            setVoiceState('idle');
        }, 2000);
    }, []);

    const sendTrigger = useCallback((trigger: string) => {}, []);

    return {
        connect, disconnect, sendFinalize, sendTrigger,
        status, isSpeaking, voiceState, intakeResult, scenarioData, escalationData
    };
};
Step 2: Deployment
Run npm run build

Run npx vercel deploy --prod