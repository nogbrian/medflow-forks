import React from 'react';
import { Palette, Info, Zap, ChevronRight, Activity } from 'lucide-react';
import { BrandLogo } from './BrandLogo';

export const Sidebar: React.FC = () => {
  return (
    <div className="w-72 bg-white border-r border-eng-blue/10 flex-shrink-0 flex flex-col h-full hidden md:flex font-sans">
      {/* Header Técnico */}
      <div className="p-6 border-b border-eng-blue/10 bg-white">
        <div className="flex items-center gap-3 text-eng-blue mb-2">
          <div className="text-eng-blue">
            <BrandLogo className="w-10 h-10" />
          </div>
          <div>
            <h1 className="font-bold text-base tracking-tight leading-tight text-eng-blue">
              TRÁFEGO PARA<br/>CONSULTÓRIOS
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-3 pl-1">
           <span className="w-2 h-2 rounded-full bg-alert animate-pulse"></span>
           <p className="text-[10px] font-mono text-concrete uppercase tracking-widest">System Online</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Section: Modules */}
        <div className="p-6 pb-2">
          <h3 className="text-[10px] font-mono font-bold text-concrete uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-4 h-[1px] bg-alert"></span>
            Módulos Ativos
          </h3>
          
          <div className="space-y-1">
             <div className="group flex items-center justify-between text-sm text-eng-blue p-3 bg-eng-blue/5 border-l-2 border-alert cursor-default">
                <div className="flex items-center gap-3">
                  <Palette className="w-4 h-4 text-eng-blue" />
                  <span className="font-medium">Creative Lab</span>
                </div>
                <ChevronRight className="w-3 h-3 text-alert" />
             </div>
             
             <div className="group flex items-center justify-between text-sm text-concrete p-3 hover:bg-tech-white border-l-2 border-transparent hover:border-concrete transition-all cursor-not-allowed opacity-60">
                <div className="flex items-center gap-3">
                  <Activity className="w-4 h-4" />
                  <span className="font-medium">Analytics (Em breve)</span>
                </div>
             </div>
          </div>
        </div>

        {/* Section: Specs */}
        <div className="p-6 pt-2">
          <h3 className="text-[10px] font-mono font-bold text-concrete uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-4 h-[1px] bg-alert"></span>
            Especificações
          </h3>
          
          <div className="bg-tech-white border border-eng-blue/10 p-4 rounded-sm space-y-4">
             <div>
                <span className="block text-[10px] font-mono text-concrete mb-1">MODELO ATIVO</span>
                <span className="text-xs font-bold text-eng-blue flex items-center gap-1">
                  <Zap className="w-3 h-3 text-alert" /> Gemini 3.0 Pro
                </span>
             </div>
             <div className="h-[1px] bg-eng-blue/10 w-full"></div>
             <div>
                <span className="block text-[10px] font-mono text-concrete mb-1">MODO DE OPERAÇÃO</span>
                <span className="text-xs font-bold text-eng-blue">Engenharia de Prompt</span>
             </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="px-6 py-4">
           <div className="border border-eng-blue/10 rounded-sm p-4 bg-white relative overflow-hidden">
              <div className="absolute top-0 right-0 w-8 h-8 bg-eng-blue/5 rounded-bl-xl"></div>
              <h4 className="text-xs font-bold text-eng-blue mb-3 uppercase border-b border-eng-blue/5 pb-2">Protocolo de Uso</h4>
              <ul className="text-[11px] text-concrete space-y-2 font-mono">
                <li className="flex items-start gap-2">
                  <span className="text-alert">01.</span> Insira o copy técnico.
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-alert">02.</span> Anexe ref. visual.
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-alert">03.</span> Aprove o blueprint.
                </li>
              </ul>
           </div>
        </div>
      </div>

      <div className="p-4 border-t border-eng-blue/10 bg-tech-white/50">
        <div className="flex items-center gap-2 text-[10px] text-concrete font-mono">
          <Info className="w-3 h-3" />
          <span>v2.4.0-stable</span>
        </div>
      </div>
    </div>
  );
};