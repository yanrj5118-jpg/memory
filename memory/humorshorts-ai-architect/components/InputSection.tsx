
import React, { useState } from 'react';
import { useTranslation } from '../i18n';

interface Props {
  onProcess: (type: 'text' | 'url' | 'image' | 'video', value: string, file?: { data: string; mimeType: string }) => void;
}

const InputSection: React.FC<Props> = ({ onProcess }) => {
  const { t } = useTranslation();
  const [inputType, setInputType] = useState<'text' | 'url' | 'file'>('text');
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64Data = (reader.result as string).split(',')[1];
      const type: any = file.type.startsWith('image/') ? 'image' : 'video';
      onProcess(type, file.name, { data: base64Data, mimeType: file.type });
      setIsUploading(false);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    
    const type = inputType === 'url' ? 'url' : 'text';
    onProcess(type, inputValue);
  };

  return (
    <div className="glass rounded-[2.5rem] p-6 md:p-10 border border-white/10 shadow-2xl relative overflow-hidden group">
      <div className="absolute -top-24 -right-24 w-48 h-48 bg-purple-600/10 rounded-full blur-3xl group-hover:bg-purple-600/20 transition-all duration-700"></div>
      
      <div className="flex space-x-2 mb-8 bg-slate-900/40 p-1.5 rounded-2xl border border-white/5 backdrop-blur-sm relative z-10">
        {[
          { key: 'text', label: t('input.tabs.text'), icon: 'fa-align-left' },
          { key: 'url', label: t('input.tabs.url'), icon: 'fa-link' },
          { key: 'file', label: t('input.tabs.file'), icon: 'fa-cloud-upload-alt' }
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setInputType(t.key as any)}
            className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-300 ${
              inputType === t.key 
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-600/30' 
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <i className={`fas ${t.icon} text-xs`}></i>
            {t.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
        {inputType === 'file' ? (
          <div className="relative group/upload">
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFileChange}
              disabled={isUploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
            />
            <div className="border-2 border-dashed border-slate-800 group-hover/upload:border-purple-500/50 rounded-3xl py-16 flex flex-col items-center justify-center transition-all bg-slate-900/50 backdrop-blur-sm group-hover/upload:scale-[0.99] duration-500">
              <div className="w-20 h-20 rounded-full bg-purple-500/10 flex items-center justify-center mb-6 group-hover/upload:scale-110 group-hover/upload:bg-purple-500/20 transition-all duration-500">
                <i className="fas fa-magic text-4xl text-purple-400"></i>
              </div>
              <p className="text-white font-bold text-xl mb-2">{t('input.placeholders.file')}</p>
              <p className="text-slate-500 text-sm">{t('input.placeholders.fileHint')}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6 animate-in fade-in duration-500">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={inputType === 'url' ? t('input.placeholders.url') : t('input.placeholders.text')}
              className="w-full h-48 bg-slate-900/60 border border-slate-800 rounded-3xl p-6 focus:ring-4 focus:ring-purple-500/20 outline-none resize-none text-slate-100 placeholder:text-slate-600 transition-all duration-300 backdrop-blur-sm font-medium leading-relaxed"
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="w-full py-5 btn-primary rounded-2xl group/btn"
            >
              <span className="flex items-center justify-center gap-3">
                {t('input.button')}
                <i className="fas fa-sparkles text-yellow-300 group-hover/btn:rotate-12 transition-transform"></i>
              </span>
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

export default InputSection;
