import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from '../i18n';
import { Language, ModelType, SkillType } from '../types';
import { checkOllamaStatus } from '../geminiService';

interface HeaderProps {
  selectedModel: ModelType;
  onModelChange: (model: ModelType) => void;
  selectedSkill: SkillType;
  onSkillChange: (skill: SkillType) => void;
}

const Header: React.FC<HeaderProps> = ({ 
  selectedModel, 
  onModelChange,
  selectedSkill,
  onSkillChange 
}) => {
  const { lang, setLang, t } = useTranslation();
  const [isLangOpen, setIsLangOpen] = useState(false);
  const [isSkillOpen, setIsSkillOpen] = useState(false);
  const [isOllamaOnline, setIsOllamaOnline] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const skillDropdownRef = useRef<HTMLDivElement>(null);

  const languages: { code: Language; label: string; flag: string }[] = [
    { code: 'ko', label: '한국어', flag: '🇰🇷' },
    { code: 'en', label: 'English', flag: '🇺🇸' },
    { code: 'zh-CN', label: '简体中文', flag: '🇨🇳' },
    { code: 'zh-TW', label: '繁體中文', flag: '🇹🇼' },
    { code: 'ru', label: 'Русский', flag: '🇷🇺' },
  ];

  const skills: { id: SkillType; label: string; icon: string; color: string }[] = [
    { id: 'general', label: t('skill.general'), icon: 'fa-magic', color: 'text-purple-400' },
    { id: 'viral-2026', label: t('skill.viral2026'), icon: 'fa-rocket', color: 'text-pink-400' },
    { id: 'commerce-olive', label: t('skill.commerce'), icon: 'fa-shopping-bag', color: 'text-emerald-400' },
  ];

  useEffect(() => {
    const checkStatus = async () => {
      const online = await checkOllamaStatus();
      setIsOllamaOnline(online);
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsLangOpen(false);
      }
      if (skillDropdownRef.current && !skillDropdownRef.current.contains(event.target as Node)) {
        setIsSkillOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="relative text-center space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 py-2 border-b border-white/5 mb-8">
        <div className="flex flex-wrap items-center gap-4">
          {/* Status & Model Switcher */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-white/5 text-[10px] font-bold tracking-tighter uppercase">
              <span className={`w-2 h-2 rounded-full animate-pulse ${isOllamaOnline ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'}`}></span>
              <span className={isOllamaOnline ? 'text-green-400' : 'text-red-400'}>LM Studio</span>
              {!process.env.API_KEY || process.env.API_KEY.includes('PLACEHOLDER') ? (
                <span className="ml-2 px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-400 border border-purple-500/30 text-[9px]">GUEST MODE</span>
              ) : null}
            </div>

            <div className="flex items-center space-x-1 glass p-1 rounded-2xl">
              <button
                onClick={() => onModelChange('google/gemma-4-e2b:2')}
                className={`px-3 py-1 rounded-xl text-[10px] font-bold transition-all ${
                  selectedModel === 'google/gemma-4-e2b:2' ? 'bg-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Fast
              </button>
              <button
                onClick={() => onModelChange('google/gemma-4-e2b')}
                className={`px-3 py-1 rounded-xl text-[10px] font-bold transition-all ${
                  selectedModel === 'google/gemma-4-e2b' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Deep
              </button>
            </div>
          </div>

          {/* Skill Selector */}
          <div className="relative" ref={skillDropdownRef}>
            <button
              onClick={() => setIsSkillOpen(!isSkillOpen)}
              className="glass px-4 py-2 rounded-2xl text-xs font-bold flex items-center space-x-3 border border-white/10 hover:border-purple-500/40 transition-all text-slate-200"
            >
              <i className={`fas ${skills.find(s => s.id === selectedSkill)?.icon} ${skills.find(s => s.id === selectedSkill)?.color}`}></i>
              <span>{skills.find(s => s.id === selectedSkill)?.label}</span>
              <i className={`fas fa-chevron-down text-[8px] transition-transform duration-300 ${isSkillOpen ? 'rotate-180' : ''}`}></i>
            </button>

            {isSkillOpen && (
              <div className="absolute left-0 mt-2 w-56 glass rounded-2xl shadow-2xl border border-white/10 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-200">
                <div className="py-2">
                  <div className="px-4 py-1 text-[10px] font-black text-slate-500 uppercase tracking-widest">{t('skill.selection')}</div>
                  {skills.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => {
                        onSkillChange(s.id);
                        setIsSkillOpen(false);
                      }}
                      className={`w-full px-4 py-3 text-left text-xs transition-colors flex items-center space-x-3 ${
                        selectedSkill === s.id 
                          ? 'bg-purple-600/20 text-purple-300 font-bold' 
                          : 'text-slate-400 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      <i className={`fas ${s.icon} ${s.color} w-5 text-center`}></i>
                      <span>{s.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Language Selector */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsLangOpen(!isLangOpen)}
            className="glass px-4 py-2 rounded-2xl text-sm font-medium flex items-center space-x-2 border border-white/10 hover:border-purple-500/40 transition-all text-slate-200"
          >
            <span>{languages.find(l => l.code === lang)?.flag}</span>
            <span className="hidden sm:inline">{languages.find(l => l.code === lang)?.label}</span>
            <i className={`fas fa-chevron-down text-[10px] transition-transform duration-300 ${isLangOpen ? 'rotate-180' : ''}`}></i>
          </button>

          {isLangOpen && (
            <div className="absolute right-0 mt-2 w-48 glass rounded-2xl shadow-2xl border border-white/10 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-200">
              <div className="py-2">
                {languages.map((l) => (
                  <button
                    key={l.code}
                    onClick={() => {
                      setLang(l.code);
                      setIsLangOpen(false);
                    }}
                    className={`w-full px-4 py-2.5 text-left text-sm transition-colors flex items-center space-x-3 ${
                      lang === l.code 
                        ? 'bg-purple-600/20 text-purple-300 font-bold' 
                        : 'text-slate-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <span>{l.flag}</span>
                    <span>{l.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="inline-flex items-center justify-center p-4 rounded-3xl bg-gradient-to-br from-purple-600 to-pink-600 shadow-xl shadow-purple-500/20 animate-float">
        <i className="fas fa-theater-masks text-3xl text-white"></i>
      </div>
      
      <div className="space-y-2">
        <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-white">
          {t('app.title')} <span className="text-gradient font-bold">{t('app.titleAccent')}</span>
        </h1>
        
        <p className="text-slate-400 max-w-xl mx-auto text-lg leading-relaxed font-light">
          {t('app.description')}
        </p>
      </div>
    </header>
  );
};

export default Header;
