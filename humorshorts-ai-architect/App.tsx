
import React, { useState } from 'react';
import Header from './components/Header';
import InputSection from './components/InputSection';
import ScriptResult from './components/ScriptResult';
import { AppState } from './types';
import { generateShortsContent } from './geminiService';
import { useTranslation } from './i18n';

const App: React.FC = () => {
  const { t, lang } = useTranslation();
  const [state, setState] = useState<AppState>({
    isAnalyzing: false,
    error: null,
    result: null,
    selectedModel: (localStorage.getItem('selectedModel') as any) || 'gemma4:e2b',
    selectedSkill: (localStorage.getItem('selectedSkill') as any) || 'general'
  });

  const setSelectedModel = (model: 'gemma4:e2b' | 'gemma4:e4b') => {
    localStorage.setItem('selectedModel', model);
    setState(prev => ({ ...prev, selectedModel: model }));
  };

  const setSelectedSkill = (skill: any) => {
    localStorage.setItem('selectedSkill', skill);
    setState(prev => ({ ...prev, selectedSkill: skill }));
  };

  const handleProcess = async (
    type: 'text' | 'url' | 'image' | 'video',
    value: string,
    file?: { data: string; mimeType: string }
  ) => {
    setState(prev => ({ ...prev, isAnalyzing: true, error: null }));
    try {
      const data = await generateShortsContent(type, value, state.selectedModel, state.selectedSkill, lang, file);
      setState(prev => ({ ...prev, isAnalyzing: false, error: null, result: data }));
    } catch (err: any) {
      console.error(err);
      setState(prev => ({ 
        ...prev, 
        isAnalyzing: false, 
        error: t('status.error')
      }));
    }
  };

  const handleReset = () => {
    setState({ isAnalyzing: false, error: null, result: null });
  };

  return (
    <div className="min-h-screen bg-slate-950 selection:bg-purple-500/30">
      <div className="max-w-4xl mx-auto px-4 py-8 md:py-16 space-y-12">
        <Header 
          selectedModel={state.selectedModel} 
          onModelChange={setSelectedModel} 
          selectedSkill={state.selectedSkill}
          onSkillChange={setSelectedSkill}
        />
        
        <main className="relative">
          {!state.result && !state.isAnalyzing && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
              <InputSection onProcess={handleProcess} />
            </div>
          )}

          {state.isAnalyzing && (
            <div className="flex flex-col items-center justify-center py-32 space-y-8 animate-in zoom-in-95 duration-500">
              <div className="relative">
                <div className="w-24 h-24 border-b-4 border-purple-500 rounded-full animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <i className="fas fa-bolt text-3xl text-yellow-400 animate-pulse"></i>
                </div>
              </div>
              <div className="text-center space-y-3">
                <h2 className="text-2xl font-bold text-white tracking-tight">{t('status.analyzing')}</h2>
                <p className="text-slate-400 animate-pulse">{t('status.scanning')}</p>
              </div>
            </div>
          )}

          {state.error && (
            <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-3xl text-red-200 flex items-center space-x-4 animate-in shake duration-500">
              <div className="w-12 h-12 rounded-2xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
                <i className="fas fa-exclamation-triangle text-xl text-red-400"></i>
              </div>
              <div className="flex-1">
                <p className="font-medium">{state.error}</p>
              </div>
              <button 
                onClick={handleReset} 
                className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-xl text-sm font-bold transition-colors"
              >
                {t('status.retry')}
              </button>
            </div>
          )}

          {state.result && !state.isAnalyzing && (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
              <ScriptResult result={state.result} onReset={handleReset} />
            </div>
          )}
        </main>

        <footer className="pt-20 pb-8 text-center border-t border-white/5">
          <p className="text-slate-500 text-sm tracking-wide">
            {t('app.footer')}
          </p>
        </footer>
      </div>
    </div>
  );
};

export default App;
