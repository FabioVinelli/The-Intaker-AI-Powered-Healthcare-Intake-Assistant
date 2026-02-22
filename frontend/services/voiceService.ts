/**
 * Voice Service for The Intaker
 * Provides fallback voice processing using MediaRecorder + backend transcription
 */

export interface VoiceServiceConfig {
  backendUrl: string;
  sampleRate?: number;
  audioFormat?: string;
  languageCode?: string;
}

export interface TranscriptionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
  success: boolean;
  error?: string;
}

export class VoiceService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioStream: MediaStream | null = null;
  private audioChunks: Blob[] = [];
  private config: VoiceServiceConfig;
  private isRecording: boolean = false;

  constructor(config: VoiceServiceConfig) {
    this.config = {
      sampleRate: 16000,
      audioFormat: 'webm',
      languageCode: 'en-US',
      ...config
    };
  }

  /**
   * Check if MediaRecorder is supported
   */
  static isSupported(): boolean {
    return !!(navigator.mediaDevices && window.MediaRecorder);
  }

  /**
   * Request microphone access
   */
  async requestMicrophoneAccess(): Promise<boolean> {
    try {
      console.log('🔵 Requesting microphone access...');
      
      // Check permissions API
      if (navigator.permissions) {
        const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
        console.log('🔵 Microphone permission status:', permission.state);
        
        if (permission.state === 'denied') {
          throw new Error('Microphone access denied');
        }
      }

      // Request media stream
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.config.sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      console.log('🟢 Microphone access granted');
      return true;
    } catch (error) {
      console.error('🔴 Microphone access failed:', error);
      return false;
    }
  }

  /**
   * Start recording audio
   */
  async startRecording(): Promise<boolean> {
    try {
      if (this.isRecording) {
        console.log('🔴 Already recording');
        return false;
      }

      // Request microphone access if not already done
      if (!this.audioStream) {
        const hasAccess = await this.requestMicrophoneAccess();
        if (!hasAccess) {
          return false;
        }
      }

      // Create MediaRecorder
      const mimeType = this.getSupportedMimeType();
      this.mediaRecorder = new MediaRecorder(this.audioStream!, {
        mimeType,
        audioBitsPerSecond: 128000
      });

      this.audioChunks = [];
      this.isRecording = true;

      // Set up event handlers
      this.mediaRecorder.ondataavailable = (event) => {
        console.log('🔵 Audio data available:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstart = () => {
        console.log('🟢 MediaRecorder started');
      };

      this.mediaRecorder.onstop = () => {
        console.log('🟡 MediaRecorder stopped');
        this.isRecording = false;
      };

      this.mediaRecorder.onerror = (event) => {
        console.error('🔴 MediaRecorder error:', event);
        this.isRecording = false;
      };

      // Start recording
      this.mediaRecorder.start(1000); // Collect data every second
      console.log('🟢 Recording started');
      return true;

    } catch (error) {
      console.error('🔴 Failed to start recording:', error);
      this.isRecording = false;
      return false;
    }
  }

  /**
   * Stop recording and transcribe
   */
  async stopRecording(): Promise<TranscriptionResult> {
    try {
      if (!this.isRecording || !this.mediaRecorder) {
        console.log('🔴 Not currently recording');
        return {
          transcript: '',
          confidence: 0,
          isFinal: true,
          success: false,
          error: 'Not currently recording'
        };
      }

      // Stop recording
      this.mediaRecorder.stop();
      
      // Wait for data to be available
      await new Promise<void>((resolve) => {
        const checkData = () => {
          if (!this.isRecording) {
            resolve();
          } else {
            setTimeout(checkData, 100);
          }
        };
        checkData();
      });

      // Create audio blob
      const audioBlob = new Blob(this.audioChunks, { 
        type: this.getSupportedMimeType() 
      });
      
      console.log('🔵 Audio blob created:', audioBlob.size, 'bytes');

      if (audioBlob.size === 0) {
        return {
          transcript: '',
          confidence: 0,
          isFinal: true,
          success: false,
          error: 'No audio data recorded'
        };
      }

      // Transcribe using backend
      const result = await this.transcribeAudio(audioBlob);
      
      // Reset for next recording
      this.audioChunks = [];
      
      return result;

    } catch (error) {
      console.error('🔴 Failed to stop recording:', error);
      return {
        transcript: '',
        confidence: 0,
        isFinal: true,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Transcribe audio using backend service
   */
  private async transcribeAudio(audioBlob: Blob): Promise<TranscriptionResult> {
    try {
      console.log('🔵 Starting backend transcription...');
      
      // Convert blob to base64
      const base64Audio = await this.blobToBase64(audioBlob);
      
      // Send to backend
      const response = await fetch(`${this.config.backendUrl}/api/v1/voice/transcribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_data: base64Audio,
          audio_format: this.config.audioFormat,
          sample_rate: this.config.sampleRate,
          language_code: this.config.languageCode
        })
      });

      if (!response.ok) {
        throw new Error(`Backend transcription failed: ${response.status}`);
      }

      const result = await response.json();
      console.log('🟢 Backend transcription completed:', result);
      
      return {
        transcript: result.transcript || '',
        confidence: result.confidence || 0,
        isFinal: true,
        success: result.success || false,
        error: result.error
      };

    } catch (error) {
      console.error('🔴 Backend transcription failed:', error);
      return {
        transcript: '',
        confidence: 0,
        isFinal: true,
        success: false,
        error: error instanceof Error ? error.message : 'Transcription failed'
      };
    }
  }

  /**
   * Convert blob to base64
   */
  private async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remove data URL prefix
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Get supported MIME type for MediaRecorder
   */
  private getSupportedMimeType(): string {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/wav'
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log('🔵 Using MIME type:', type);
        return type;
      }
    }

    console.log('🔴 No supported MIME type found, using default');
    return 'audio/webm';
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
    }
    
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }
    
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    
    console.log('🔴 Voice service cleaned up');
  }

  /**
   * Get current recording status
   */
  getRecordingStatus(): boolean {
    return this.isRecording;
  }
}
