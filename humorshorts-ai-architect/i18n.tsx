
import React, { createContext, useContext, useState, useEffect } from 'react';
import { Language } from './types';
import ko from './locales/ko.json';
import en from './locales/en.json';
import zhCN from './locales/zh-CN.json';
import zhTW from './locales/zh-TW.json';
import ru from './locales/ru.json';

type Translations = typeof ko;

const translations: Record<Language, Translations> = { 
  ko, 
  en, 
  'zh-CN': zhCN as unknown as Translations, 
  'zh-TW': zhTW as unknown as Translations, 
  ru: ru as unknown as Translations 
};

interface I18nContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (path: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<Language>(() => {
    const saved = localStorage.getItem('lang') as Language;
    if (translations[saved]) return saved;
    if (navigator.language.startsWith('ko')) return 'ko';
    if (navigator.language.startsWith('zh-CN')) return 'zh-CN';
    if (navigator.language.startsWith('zh-TW')) return 'zh-TW';
    if (navigator.language.startsWith('ru')) return 'ru';
    return 'en';
  });

  useEffect(() => {
    localStorage.setItem('lang', lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const t = (path: string): string => {
    const keys = path.split('.');
    let current: any = translations[lang];
    for (const key of keys) {
      if (current[key] === undefined) return path;
      current = current[key];
    }
    return current;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useTranslation = () => {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useTranslation must be used within I18nProvider');
  return context;
};
