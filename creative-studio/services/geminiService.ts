import { GoogleGenAI, FunctionDeclaration, Type, Tool, Content, Part, Chat, GenerateContentResponse } from "@google/genai";
import { SYSTEM_INSTRUCTION, MODEL_TEXT, MODEL_IMAGE } from "../constants";
import { Message, Sender } from "../types";

const getClient = () => {
  // Always create a new instance to ensure we use the latest API Key
  const apiKey = process.env.API_KEY;
  if (!apiKey) throw new Error("API Key not found");
  return new GoogleGenAI({ apiKey });
};

// Retry helper with AbortSignal support
async function retryOperation<T>(operation: () => Promise<T>, maxRetries: number = 3, initialDelay: number = 2000, signal?: AbortSignal): Promise<T> {
  let lastError: any;
  
  for (let i = 0; i < maxRetries; i++) {
    if (signal?.aborted) {
        throw new Error("Operation aborted by user");
    }

    try {
      return await operation();
    } catch (error: any) {
      if (signal?.aborted) {
          throw new Error("Operation aborted by user");
      }

      lastError = error;
      const errorCode = error.status || error.code;
      const errorMessage = error.message || "";
      
      // Retry on 503 (Unavailable), 504 (Gateway Timeout), or specific deadline errors
      if (errorCode === 503 || errorCode === 504 || errorMessage.includes("Deadline expired")) {
        const delay = initialDelay * Math.pow(2, i);
        console.warn(`API call failed with ${errorCode || errorMessage}. Retrying in ${delay}ms...`);
        
        // Wait with signal check
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(resolve, delay);
            if (signal) {
                signal.addEventListener('abort', () => {
                    clearTimeout(timeout);
                    reject(new Error("Operation aborted by user"));
                });
            }
        });
        continue;
      }
      
      // If not retryable, throw immediately
      throw error;
    }
  }
  throw lastError;
}

// Tool Definition for Image Generation
const generateCreativeTool: FunctionDeclaration = {
  name: "generate_creative",
  description: "Generates a high-quality social media image. Enforces consistency by separating the global style from specific content.",
  parameters: {
    type: Type.OBJECT,
    properties: {
      style_prompt: {
        type: Type.STRING,
        description: "The 'Master Style' prompt. Describes the global look, colors, lighting, medium, and typography style. MUST BE IDENTICAL for every slide in a carousel sequence.",
      },
      content_prompt: {
        type: Type.STRING,
        description: "The specific content, subject, layout, and text for THIS specific image/slide.",
      },
      aspectRatio: {
        type: Type.STRING,
        enum: ["1:1", "9:16", "3:4"],
        description: "STRICT ASPECT RATIO RULES: 1. IF content is 'Story' or 'Stories' -> MUST use '9:16'. 2. IF content is 'Feed', 'Post', or 'Carousel' -> MUST use '1:1' (Square) or '3:4' (Portrait). NEVER use '9:16' for Feed/Carousels.",
      },
    },
    required: ["style_prompt", "content_prompt", "aspectRatio"],
  },
};

const tools: Tool[] = [{ functionDeclarations: [generateCreativeTool] }];

// Helper to convert App Message format to Gemini SDK Content format
const convertToGeminiHistory = (messages: Message[]): Content[] => {
  const history: Content[] = [];

  for (const msg of messages) {
    // Skip system messages or temporary states if any
    if (msg.isThinking) continue;

    const role = msg.sender === Sender.USER ? 'user' : 'model';
    const parts: Part[] = [];

    // Add text content
    if (msg.content) {
      parts.push({ text: msg.content });
    }

    // Add image content if present (for user uploads)
    // Supports multiple images per message
    if (msg.images && msg.images.length > 0) {
      msg.images.forEach(img => {
        // Ensure valid base64 string
        if (img.includes('base64,')) {
          const base64Data = img.split(',')[1];
          const mimeType = img.split(';')[0].split(':')[1];
          parts.push({ 
            inlineData: { 
              mimeType, 
              data: base64Data 
            } 
          });
        }
      });
    }

    if (parts.length > 0) {
      history.push({ role, parts });
    }
  }

  return history;
};

export const startChatSession = (previousMessages?: Message[]) => {
  const ai = getClient();
  
  let history: Content[] = [];
  if (previousMessages && previousMessages.length > 0) {
    history = convertToGeminiHistory(previousMessages);
  }

  return ai.chats.create({
    model: MODEL_TEXT,
    config: {
      systemInstruction: SYSTEM_INSTRUCTION,
      thinkingConfig: { thinkingBudget: 1024 },
      tools: tools,
    },
    history: history
  });
};

export const sendMessageWithRetry = async (chat: Chat, message: any, signal?: AbortSignal): Promise<GenerateContentResponse> => {
  return retryOperation(() => chat.sendMessage({ message }), 3, 2000, signal);
};

export const generateImage = async (style_prompt: string, content_prompt: string, aspectRatio: string): Promise<string> => {
  const ai = getClient();
  
  // Combine style and content for the image model
  // We prioritize style first to set the scene, then content
  const fullPrompt = `Style: ${style_prompt}. Content: ${content_prompt}`;

  return retryOperation(async () => {
    const response = await ai.models.generateContent({
      model: MODEL_IMAGE,
      contents: {
          parts: [{ text: fullPrompt }]
      },
      config: {
        imageConfig: {
          aspectRatio: aspectRatio as any, 
          imageSize: "1K" 
        }
      }
    });

    for (const part of response.candidates?.[0]?.content?.parts || []) {
      if (part.inlineData && part.inlineData.data) {
          return `data:${part.inlineData.mimeType || 'image/png'};base64,${part.inlineData.data}`;
      }
    }

    throw new Error("No image generated");
  }, 3, 4000); // Higher initial delay for image generation
};