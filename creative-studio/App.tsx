import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { Lock, Grid } from 'lucide-react';
import { BrandLogo } from './components/BrandLogo';

const App: React.FC = () => {
  const [hasApiKey, setHasApiKey] = useState<boolean>(false);
  const [checking, setChecking] = useState<boolean>(true);

  useEffect(() => {
    const checkKey = async () => {
      try {
        const aistudio = (window as any).aistudio;
        if (aistudio) {
          const hasKey = await aistudio.hasSelectedApiKey();
          setHasApiKey(hasKey);
        } else {
          setHasApiKey(!!process.env.API_KEY);
        }
      } catch (e) {
        setHasApiKey(!!process.env.API_KEY);
      } finally {
        setChecking(false);
      }
    };
    checkKey();
  }, []);

  const handleSelectKey = async () => {
    const aistudio = (window as any).aistudio;
    if (aistudio) {
      try {
        await aistudio.openSelectKey();
      } catch (e) {
        console.error("Error selecting key:", e);
      }
      setHasApiKey(true);
    }
  };

  if (checking) {
      return (
        <div className="h-screen w-screen bg-tech-white flex flex-col items-center justify-center gap-4">
            <div className="w-12 h-12 border-4 border-eng-blue/20 border-t-alert rounded-full animate-spin"></div>
            <div className="font-mono text-xs text-concrete uppercase tracking-widest">Iniciando Sistemas...</div>
        </div>
      );
  }

  if (!hasApiKey) {
      return (
          <div className="h-screen w-screen flex items-center justify-center bg-blueprint font-sans">
              <div className="p-10 bg-white border border-eng-blue/10 shadow-tech max-w-md mx-4 relative overflow-hidden rounded-sm">
                  {/* Decorative Bar */}
                  <div className="absolute top-0 left-0 w-full h-1 bg-alert"></div>
                  
                  <div className="flex flex-col items-center text-center">
                    <div className="w-20 h-20 bg-eng-blue/5 rounded-sm flex items-center justify-center mb-6 border border-eng-blue/10">
                      <BrandLogo className="w-12 h-12 text-eng-blue" />
                    </div>
                    
                    <h2 className="text-2xl font-bold text-eng-blue mb-2 tracking-tight">Acesso Restrito</h2>
                    <p className="text-concrete mb-8 text-sm leading-relaxed">
                      Este terminal de engenharia requer uma chave de API válida (Google Cloud Project) para operar o motor <strong>Gemini 3 Pro</strong>.
                    </p>
                    
                    <button 
                      onClick={handleSelectKey}
                      className="w-full py-3 px-6 bg-alert hover:bg-orange-600 text-white font-bold uppercase tracking-wider text-sm rounded-sm transition-all shadow-sm flex items-center justify-center gap-2 mb-6"
                    >
                      <Lock size={16} /> Autenticar Acesso
                    </button>

                    <div className="text-[10px] text-concrete font-mono border-t border-eng-blue/10 pt-4 w-full">
                      <a 
                          href="https://ai.google.dev/gemini-api/docs/billing" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="hover:text-alert transition-colors flex items-center justify-center gap-1"
                      >
                          DOCUMENTAÇÃO DE FATURAMENTO <Grid size={10} />
                      </a>
                    </div>
                  </div>
              </div>
          </div>
      )
  }

  return (
    <div className="flex h-screen w-full bg-white overflow-hidden">
      <Sidebar />
      <main className="flex-1 h-full relative">
        <ChatInterface />
      </main>
    </div>
  );
};

export default App;