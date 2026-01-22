import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Message, Sender } from '../types';
import { Bot, User, Download, Sparkles, X, ZoomIn, Edit3, Check, ArrowLeft, Sun, SlidersHorizontal, Crop as CropIcon, Layers } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isModel = message.sender === Sender.MODEL;
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  
  // Editor State
  const [isEditing, setIsEditing] = useState(false);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [aspectRatio, setAspectRatio] = useState<number | null>(null);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const handleImageClick = (imgSrc: string) => {
    setPreviewImage(imgSrc);
    resetEditor();
  };

  const resetEditor = () => {
    setIsEditing(false);
    setBrightness(100);
    setContrast(100);
    setAspectRatio(null);
  };

  const closePreview = () => {
    setPreviewImage(null);
    resetEditor();
  };

  const handleSaveEdit = () => {
    if (canvasRef.current) {
      const dataUrl = canvasRef.current.toDataURL('image/png');
      setPreviewImage(dataUrl);
      setIsEditing(false);
    }
  };

  // Real-time canvas rendering
  useEffect(() => {
    if (!isEditing || !previewImage || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = previewImage;
    
    img.onload = () => {
      // 1. Calculate Crop
      let srcW = img.naturalWidth;
      let srcH = img.naturalHeight;
      let srcX = 0;
      let srcY = 0;

      if (aspectRatio) {
        const imgRatio = srcW / srcH;
        if (imgRatio > aspectRatio) {
          // Image is wider, crop width
          const newW = srcH * aspectRatio;
          srcX = (srcW - newW) / 2;
          srcW = newW;
        } else {
          // Image is taller, crop height
          const newH = srcW / aspectRatio;
          srcY = (srcH - newH) / 2;
          srcH = newH;
        }
      }

      // 2. Set Canvas Size (to the crop size)
      canvas.width = srcW;
      canvas.height = srcH;

      // 3. Draw with Filters
      ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
      ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
    };
  }, [isEditing, previewImage, brightness, contrast, aspectRatio]);

  const hasMultipleImages = message.images && message.images.length > 1;

  return (
    <>
      {/* Lightbox Modal - Technical Style */}
      {previewImage && (
        <div 
          className="fixed inset-0 z-[100] bg-eng-dark/95 backdrop-blur-md flex flex-col animate-in fade-in duration-200"
          onClick={(e) => {
             if (!isEditing && e.target === e.currentTarget) closePreview();
          }}
        >
          {/* Toolbar */}
          <div className="flex items-center justify-between p-4 bg-eng-dark border-b border-white/10 text-white z-50">
             <div className="flex items-center gap-4">
               {isEditing ? (
                 <button onClick={resetEditor} className="hover:text-alert flex items-center gap-2 font-mono text-sm uppercase tracking-wide">
                   <ArrowLeft size={16} /> Cancel
                 </button>
               ) : (
                 <button onClick={closePreview} className="hover:text-alert transition-colors">
                   <X size={24} />
                 </button>
               )}
             </div>

             <div className="flex items-center gap-4">
               {!isEditing ? (
                 <>
                   <button 
                     onClick={() => setIsEditing(true)}
                     className="flex items-center gap-2 px-4 py-2 border border-white/20 hover:border-alert hover:text-alert bg-transparent rounded-sm transition-all font-mono text-xs uppercase"
                   >
                     <Edit3 size={14} />
                     Edit
                   </button>
                   <a 
                      href={previewImage} 
                      download={`creative-studio-${Date.now()}.png`}
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-2 px-4 py-2 bg-alert hover:bg-orange-600 text-white rounded-sm transition-colors font-mono text-xs uppercase font-medium"
                   >
                     <Download size={14} />
                     Download
                   </a>
                 </>
               ) : (
                 <button 
                   onClick={handleSaveEdit}
                   className="flex items-center gap-2 px-4 py-2 bg-alert hover:bg-orange-600 text-white rounded-sm transition-colors font-mono text-xs uppercase font-medium"
                 >
                   <Check size={14} />
                   Save
                 </button>
               )}
             </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex items-center justify-center p-8 overflow-hidden relative bg-[url('https://www.transparenttextures.com/patterns/graphy.png')]">
             {isEditing ? (
               <canvas ref={canvasRef} className="max-w-full max-h-full object-contain shadow-2xl border border-white/10" />
             ) : (
               <img src={previewImage} alt="Preview" className="max-w-full max-h-full object-contain shadow-2xl border border-white/10" onClick={(e) => e.stopPropagation()} />
             )}
          </div>

          {/* Editor Controls */}
          {isEditing && (
            <div className="bg-eng-dark border-t border-white/10 p-6 animate-in slide-in-from-bottom duration-200">
               <div className="max-w-3xl mx-auto space-y-6">
                  {/* Sliders */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                       <div className="flex justify-between text-[10px] text-concrete font-mono uppercase tracking-wider">
                          <span className="flex items-center gap-1"><Sun size={12} /> Brightness</span>
                          <span className="text-alert">{brightness}%</span>
                       </div>
                       <input type="range" min="0" max="200" value={brightness} onChange={(e) => setBrightness(Number(e.target.value))}
                         className="w-full h-1 bg-white/10 rounded-none appearance-none cursor-pointer accent-alert" />
                    </div>
                    <div className="space-y-2">
                       <div className="flex justify-between text-[10px] text-concrete font-mono uppercase tracking-wider">
                          <span className="flex items-center gap-1"><SlidersHorizontal size={12} /> Contrast</span>
                          <span className="text-alert">{contrast}%</span>
                       </div>
                       <input type="range" min="0" max="200" value={contrast} onChange={(e) => setContrast(Number(e.target.value))}
                         className="w-full h-1 bg-white/10 rounded-none appearance-none cursor-pointer accent-alert" />
                    </div>
                  </div>

                  {/* Crop Presets */}
                  <div className="space-y-2">
                    <div className="text-[10px] text-concrete font-mono uppercase tracking-wider flex items-center gap-1">
                      <CropIcon size={12} /> Crop Ratio
                    </div>
                    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                       {[
                         { label: 'Original', val: null },
                         { label: 'Square 1:1', val: 1 },
                         { label: 'Feed 4:5', val: 4/5 },
                         { label: 'Story 9:16', val: 9/16 },
                         { label: 'Land 16:9', val: 16/9 }
                       ].map((opt, i) => (
                         <button 
                           key={i}
                           onClick={() => setAspectRatio(opt.val)}
                           className={`px-3 py-1.5 rounded-sm text-xs font-mono border transition-colors whitespace-nowrap
                             ${aspectRatio === opt.val 
                               ? 'bg-alert border-alert text-white' 
                               : 'bg-transparent border-white/20 text-concrete hover:border-white/50'}`}
                         >
                           {opt.label}
                         </button>
                       ))}
                    </div>
                  </div>
               </div>
            </div>
          )}
        </div>
      )}

      {/* CHAT BUBBLE LAYOUT */}
      <div className={`flex w-full ${isModel ? 'justify-start' : 'justify-end'} mb-6 group`}>
        <div className={`flex max-w-[90%] md:max-w-[75%] gap-4 ${isModel ? 'flex-row' : 'flex-row-reverse'}`}>
          
          {/* Avatar (Technical) */}
          <div className={`w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0 border 
            ${isModel ? 'bg-white border-eng-blue/10 text-eng-blue' : 'bg-eng-blue border-eng-blue text-white'}`}>
            {isModel ? <Bot size={18} strokeWidth={1.5} /> : <User size={18} strokeWidth={1.5} />}
          </div>

          {/* Content Box */}
          <div className={`flex flex-col ${isModel ? 'items-start' : 'items-end'}`}>
            
            {/* Metadata Label */}
            <span className={`text-[10px] font-mono mb-1 uppercase tracking-wider ${isModel ? 'text-concrete ml-1' : 'text-concrete mr-1'}`}>
              {isModel ? 'Creative Director' : 'Client'} • {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>

            <div className={`p-5 shadow-sm relative rounded-sm min-w-[200px]
              ${isModel 
                ? 'bg-white border border-eng-blue/10 text-eng-blue' 
                : 'bg-eng-blue text-white shadow-md'
              }`}>
              
              {/* Technical Corner Accent */}
              <div className={`absolute top-0 w-2 h-2 border-t border-l 
                 ${isModel ? 'border-alert left-0' : 'border-white/30 right-0 rotate-90'}`}></div>

              {message.isThinking && (
                 <div className="flex items-center gap-3 text-xs font-mono text-concrete mb-4 border-b border-dashed border-concrete/20 pb-2">
                   <Sparkles className="w-3 h-3 animate-pulse text-alert" />
                   <span className="uppercase tracking-widest">Processing...</span>
                 </div>
              )}

              {message.content && (
                <div className={`markdown-body text-sm leading-relaxed ${!isModel ? 'text-white' : ''}`}>
                   <ReactMarkdown 
                     components={{
                       code: ({node, ...props}) => (
                         <span className={`font-mono px-1 rounded-sm text-xs ${isModel ? 'bg-black/5 text-eng-blue' : 'bg-white/20 text-white'}`} {...props} />
                       ),
                       strong: ({node, ...props}) => <span className={`font-bold ${isModel ? 'text-eng-blue' : 'text-alert'}`} {...props} />
                     }}
                   >
                     {message.content}
                   </ReactMarkdown>
                </div>
              )}
            </div>

            {/* Generated or Attached Images */}
            {message.images && message.images.length > 0 && (
              <div className="mt-3 w-full">
                {/* Visual Header for Carousel */}
                {hasMultipleImages && (
                    <div className="flex items-center gap-2 mb-2 px-1">
                        <Layers size={12} className="text-concrete" />
                        <span className="text-[10px] font-mono text-concrete uppercase tracking-wider">
                            Visual Continuity View
                        </span>
                    </div>
                )}
                
                {/* Images Container */}
                <div className={`
                    ${hasMultipleImages 
                        ? 'flex flex-row overflow-x-auto snap-x gap-[1px] pb-2 scrollbar-hide mask-fade' 
                        : 'grid grid-cols-1'}
                    `}
                >
                    {message.images.map((img, idx) => (
                      <div 
                        key={idx} 
                        className={`relative group cursor-zoom-in overflow-hidden border border-eng-blue/10 bg-white flex-shrink-0
                            ${hasMultipleImages ? 'w-[250px] aspect-square snap-center rounded-none first:rounded-l-sm last:rounded-r-sm' : 'rounded-sm p-1'}`}
                        onClick={() => handleImageClick(img)}
                      >
                        <div className="absolute inset-0 bg-eng-blue/0 group-hover:bg-eng-blue/20 transition-all z-10 flex items-center justify-center">
                            <ZoomIn className="text-white opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all" size={24} />
                        </div>
                        <img 
                          src={img} 
                          alt={`Asset ${idx + 1}`} 
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ))}
                </div>
              </div>
            )}
            
          </div>
        </div>
      </div>
    </>
  );
};