export enum Sender {
  USER = 'user',
  MODEL = 'model',
  SYSTEM = 'system'
}

export interface Message {
  id: string;
  sender: Sender;
  content: string;
  timestamp: Date;
  images?: string[]; // Base64 strings for generated images or user uploads (Multi-image support)
  isThinking?: boolean;
  toolCallId?: string;
  functionResponse?: string;
}

export enum AspectRatio {
  SQUARE = '1:1',
  PORTRAIT = '9:16',
  LANDSCAPE = '16:9'
}

export interface ImageGenerationConfig {
  prompt: string;
  aspectRatio: AspectRatio;
}

export interface AppState {
  messages: Message[];
  isLoading: boolean;
  apiKey: string | null;
}