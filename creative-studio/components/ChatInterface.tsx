import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Trash2, X, Paperclip, Sparkles, Square, RefreshCcw } from 'lucide-react';
import { Message, Sender } from '../types';
import { startChatSession, generateImage, sendMessageWithRetry } from '../services/geminiService';
import { MessageBubble } from './MessageBubble';
import { Chat } from "@google/genai";

const STORAGE_KEY = 'creative_studio_chat_history';

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  sender: Sender.MODEL,
  content: "### Estúdio Criativo Online\n\nOlá. Sou seu **Diretor de Criação**. Estou aqui para elevar o padrão visual da sua marca médica.\n\n**Como podemos começar?**\n1. Envie o texto do post (Copy).\n2. Compartilhe referências visuais que você gosta.\n3. Defina se faremos Feed, Stories ou Carrossel.",
  timestamp: new Date()
};

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [previewImages, setPreviewImages] = useState<string[]>([]);
  
  const chatSessionRef = useRef<Chat | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isInitializedRef = useRef(false);
  
  // Control for stopping generation
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load from Storage
  useEffect(() => {
    if (isInitializedRef.current) return;
    const saved = localStorage.getItem(STORAGE_KEY);
    let initialMessages: Message[] = [];
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        initialMessages = parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp),
          images: m.images ? m.images : (m.image ? [m.image] : [])
        }));
      } catch (e) {
        initialMessages = [WELCOME_MESSAGE];
      }
    } else {
      initialMessages = [WELCOME_MESSAGE];
    }
    setMessages(initialMessages);
    try {
      chatSessionRef.current = startChatSession(initialMessages);
    } catch (e) {
      chatSessionRef.current = startChatSession();
    }
    isInitializedRef.current = true;
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    }
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea with max-height limit
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 200; 
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
      textareaRef.current.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  }, [inputText]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleClearChat = () => {
    if (window.confirm("Deseja limpar o histórico e iniciar um novo projeto criativo?")) {
      localStorage.removeItem(STORAGE_KEY);
      setMessages([WELCOME_MESSAGE]);
      chatSessionRef.current = startChatSession();
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setMessages(prev => [...prev, {
         id: Date.now().toString(),
         sender: Sender.SYSTEM, // Using System/Model visually
         content: "**Operação cancelada pelo usuário.**",
         timestamp: new Date()
      }]);
    }
  };

  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewImages(prev => [...prev, reader.result as string]);
    };
    reader.readAsDataURL(file);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) Array.from(e.target.files).forEach(processFile);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const blob = items[i].getAsFile();
        if (blob) processFile(blob);
      }
    }
  };

  const removePreviewImage = (index: number) => {
    setPreviewImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleSendMessage = async () => {
    if ((!inputText.trim() && previewImages.length === 0) || isLoading || !chatSessionRef.current) return;

    // Reset abort controller
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    const userMsgId = Date.now().toString();
    const newUserMessage: Message = {
      id: userMsgId,
      sender: Sender.USER,
      content: inputText,
      images: previewImages.length > 0 ? [...previewImages] : undefined,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setInputText('');
    setPreviewImages([]);
    setIsLoading(true);

    let currentLoopInputText = inputText;
    let currentLoopImages = newUserMessage.images;
    let loopCount = 0;
    const MAX_LOOPS = 3;

    try {
      while (loopCount < MAX_LOOPS) {
        if (signal.aborted) break;

        // --- 1. PREPARE MESSAGE PARTS ---
        let messageParts: any[] = [];
        if (currentLoopInputText.trim()) messageParts.push({ text: currentLoopInputText });
        
        if (currentLoopImages && currentLoopImages.length > 0) {
          currentLoopImages.forEach(img => {
            if (img.includes('base64,')) {
                const base64Data = img.split(',')[1];
                const mimeType = img.split(';')[0].split(':')[1];
                messageParts.push({ inlineData: { mimeType, data: base64Data } });
            }
          });
        }
        if (messageParts.length === 0) messageParts.push({ text: " " });

        // --- 2. SEND MESSAGE TO GEMINI ---
        const result = await sendMessageWithRetry(chatSessionRef.current, messageParts, signal);
        
        if (signal.aborted) break;

        const calls = result.functionCalls;
        let finalResponseText = result.text;
        let generatedImages: string[] = [];

        // --- 3. PROCESS TOOLS (IMAGE GENERATION) ---
        if (calls && calls.length > 0) {
          setMessages(prev => [...prev, {
              id: Date.now().toString(),
              sender: Sender.MODEL,
              content: loopCount > 0 ? `Refazendo slides (Tentativa ${loopCount + 1}/${MAX_LOOPS})...` : `Gerando ${calls.length > 1 ? 'sequência de slides' : 'arte'}...`,
              isThinking: true,
              timestamp: new Date()
          }]);

          // Process parallel calls
          const toolPromises = calls.map(async (call) => {
              if (signal.aborted) return null;
              if (call.name === 'generate_creative') {
                  const args = call.args as any;
                  try {
                      // Pass signal if generateImage supported it, currently we check before/after
                      const imgUrl = await generateImage(args.style_prompt, args.content_prompt, args.aspectRatio);
                      return { 
                          success: true, 
                          img: imgUrl, 
                          call,
                          prompt: args.content_prompt
                      };
                  } catch (err) {
                      console.error("Image generation failed", err);
                      return { success: false, call, error: err };
                  }
              }
              return null;
          });

          const toolResults = await Promise.all(toolPromises);
          if (signal.aborted) break;

          const functionResponseParts: any[] = [];
          
          toolResults.forEach(res => {
              if (!res) return;
              if (res.success && res.img) {
                  generatedImages.push(res.img);
                  functionResponseParts.push({
                      functionResponse: {
                          name: res.call.name,
                          response: { result: "Image generated successfully." }
                      }
                  });
              } else {
                  functionResponseParts.push({
                      functionResponse: {
                          name: res.call.name,
                          response: { error: "Image generation failed." }
                      }
                  });
              }
          });

          // Send tool outputs back
          if (functionResponseParts.length > 0 && !signal.aborted) {
              await sendMessageWithRetry(chatSessionRef.current, functionResponseParts, signal);
          }

          if (!finalResponseText) {
              if (generatedImages.length > 0) {
                  if (generatedImages.length > 1) {
                      finalResponseText = `**Carrossel Gerado (${generatedImages.length} Slides).**\n\nConfira a continuidade visual abaixo.`;
                  } else {
                      const validResult = toolResults.find(r => r && r.success && r.prompt);
                      const promptText = validResult ? (validResult as any).prompt : "Conceito Visual";
                      finalResponseText = `Arte Gerada.\n\n**Conceito:**\n\`${promptText.substring(0, 80)}...\``;
                  }
              } else {
                  finalResponseText = "Não foi possível gerar as imagens. Tente novamente.";
              }
          }
        }

        // --- 4. SHOW INTERMEDIATE RESULTS ---
        setMessages(prev => {
          const filtered = prev.filter(m => !m.isThinking);
          return [...filtered, {
              id: (Date.now() + 1).toString(),
              sender: Sender.MODEL,
              content: finalResponseText || " ",
              images: generatedImages.length > 0 ? generatedImages : undefined,
              timestamp: new Date()
          }];
        });

        // Notify parent shell about generated creatives
        if (generatedImages.length > 0 && window.parent !== window) {
          window.parent.postMessage({
            type: 'creative:generated',
            images: generatedImages,
            prompt: finalResponseText || '',
            count: generatedImages.length,
          }, '*');
        }

        // --- 5. CAROUSEL VERIFICATION LOGIC ---
        // If we generated multiple images, we force the model to verify them.
        if (generatedImages.length > 1 && loopCount < MAX_LOOPS - 1) {
           loopCount++;
           
           // Inject a hidden "user" message that forces verification
           // We do NOT add this to the UI 'messages' state to keep chat clean, 
           // BUT we add a system indicator bubble in the UI so user knows what's happening.
           
           setMessages(prev => [...prev, {
             id: `verify-${Date.now()}`,
             sender: Sender.MODEL, // Visual trick: Model talking to itself/User
             content: `_Verificando continuidade visual dos slides (${loopCount})..._`,
             timestamp: new Date()
           }]);

           currentLoopInputText = `[SISTEMA DE VERIFICAÇÃO AUTOMÁTICA]
           
           Analise as imagens geradas acima (anexadas neste contexto). 
           Verifique se a continuidade visual entre os slides está PERFEITA (Seamless Carousel).
           
           - Se houver falhas de conexão, cortes abruptos ou cores não batendo nas bordas: Responda chamando a tool 'generate_creative' novamente para corrigir TODAS as imagens.
           - Se estiver PERFEITO: Responda apenas "STATUS: APROVADO".
           
           Tentativa ${loopCount} de ${MAX_LOOPS}.`;
           
           currentLoopImages = generatedImages; // Feed images back to Gemini Vision
           continue; // Loop back to start to send this verification request
        } 
        
        // If not a carousel or max loops reached or single image
        break; 
      }

    } catch (error: any) {
       if (signal.aborted) return; // Ignore errors if aborted
       console.error(error);
       setMessages(prev => [...prev, {
          id: Date.now().toString(),
          sender: Sender.MODEL,
          content: "Ocorreu um erro técnico ou interrupção. Tente novamente.",
          timestamp: new Date()
       }]);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-blueprint relative font-sans">
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scrollbar-hide">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isLoading && !messages.some(m => m.isThinking) && (
           <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
             <div className="bg-white border border-eng-blue/5 px-4 py-3 rounded-2xl shadow-sm flex items-center gap-3">
                <Sparkles className="w-4 h-4 animate-pulse text-alert" />
                <span className="text-xs font-medium text-concrete">Processando...</span>
             </div>
           </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-eng-blue/10 p-4 md:p-6 shadow-[0_-4px_20px_rgba(0,0,0,0.02)] z-10">
        
        {/* Attachments Preview */}
        {previewImages.length > 0 && (
            <div className="mb-4 flex gap-3 overflow-x-auto pb-2 scrollbar-hide px-1">
                {previewImages.map((img, idx) => (
                    <div key={idx} className="relative group border border-eng-blue/10 p-1 bg-tech-white rounded-lg overflow-hidden shadow-sm">
                        <img src={img} alt="Preview" className="h-20 w-auto object-cover rounded-md" />
                        <button 
                            onClick={() => removePreviewImage(idx)}
                            className="absolute top-1 right-1 bg-black/50 hover:bg-alert text-white rounded-full p-1 backdrop-blur-sm transition-all opacity-0 group-hover:opacity-100"
                        >
                            <X size={12} />
                        </button>
                    </div>
                ))}
            </div>
        )}

        <div className="max-w-4xl mx-auto flex items-end gap-3">
          
          {/* Action Buttons */}
          <div className="flex gap-1 pb-0.5">
             <button 
                onClick={handleClearChat}
                className="p-3 text-concrete hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
                title="Novo Projeto"
              >
                <Trash2 size={20} strokeWidth={1.5} />
              </button>
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="p-3 text-concrete hover:text-eng-blue hover:bg-eng-blue/5 rounded-xl transition-all"
                title="Adicionar Referência"
              >
                <Paperclip size={20} strokeWidth={1.5} />
              </button>
          </div>
          
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            accept="image/*" 
            multiple
            className="hidden" 
          />

          {/* Main Input */}
          <div className="flex-1 relative bg-tech-white rounded-2xl border border-eng-blue/5 focus-within:border-eng-blue/20 focus-within:bg-white focus-within:shadow-sm transition-all duration-200">
             <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                onPaste={handlePaste}
                disabled={isLoading}
                placeholder={isLoading ? "Aguarde a finalização..." : "Descreva seu post ou ideia criativa..."}
                className="w-full bg-transparent border-none focus:ring-0 text-eng-blue placeholder-concrete/50 resize-none py-3.5 px-4 font-sans text-sm leading-relaxed max-h-[200px] overflow-hidden disabled:opacity-50"
                rows={1}
                style={{ minHeight: '48px' }}
              />
          </div>
          
          {/* Send / Stop Button */}
          {isLoading ? (
            <button
              onClick={handleStop}
              className="p-3.5 rounded-xl transition-all mb-0.5 shadow-sm flex-shrink-0 bg-red-500 hover:bg-red-600 text-white animate-in zoom-in duration-200"
              title="Parar Geração"
            >
              <Square size={20} strokeWidth={0} fill="currentColor" />
            </button>
          ) : (
            <button
              onClick={handleSendMessage}
              disabled={(!inputText.trim() && previewImages.length === 0)}
              className={`p-3.5 rounded-xl transition-all mb-0.5 shadow-sm flex-shrink-0
                ${(!inputText.trim() && previewImages.length === 0) 
                  ? 'bg-tech-white text-concrete/30 cursor-not-allowed' 
                  : 'bg-alert text-white hover:bg-orange-600 hover:shadow-md hover:scale-105 active:scale-95'
                }`}
            >
              <Send size={20} strokeWidth={2} className="ml-0.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};