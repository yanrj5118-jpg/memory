import React, { useState, useEffect } from 'react';
import { ShortScript, ScriptVariation, ScriptPart, AlgorithmCheckResult } from '../types';
import { checkAlgorithmAndConstraints, generateVisual } from '../geminiService';
import { useTranslation } from '../i18n';

interface Props {
  result: ShortScript;
  onReset: () => void;
}

const ScriptResult: React.FC<Props> = ({ result, onReset }) => {
  const { t, lang } = useTranslation();
  const [activeVariationIdx, setActiveVariationIdx] = useState(0);
  const [localVariations, setLocalVariations] = useState<ScriptVariation[]>(result.variations);
  const [algoCheck, setAlgoCheck] = useState<{ loading: boolean, data: AlgorithmCheckResult | null }>({
    loading: false,
    data: null
  });
  const [isRegeneratingImg, setIsRegeneratingImg] = useState<{ [key: string]: boolean }>({});
  const [copyStatus, setCopyStatus] = useState(false);

  useEffect(() => {
    setLocalVariations(result.variations);
    setAlgoCheck({ loading: false, data: null });
    setActiveVariationIdx(0);
  }, [result]);

  const updateField = (partKey: 'part1' | 'part2', field: keyof ScriptPart, value: string) => {
    const updated = [...localVariations];
    updated[activeVariationIdx][partKey] = {
      ...updated[activeVariationIdx][partKey],
      [field]: value
    };
    setLocalVariations(updated);
  };

  const runAlgoCheck = async () => {
    setAlgoCheck({ loading: true, data: null });
    try {
      const data = await checkAlgorithmAndConstraints(localVariations[activeVariationIdx]);
      setAlgoCheck({ loading: false, data });
    } catch (e) {
      console.error(e);
      setAlgoCheck({ loading: false, data: null });
    }
  };

  const handleRegenerateImage = async (partKey: 'part1' | 'part2') => {
    const prompt = localVariations[activeVariationIdx][partKey].visualPrompt;
    setIsRegeneratingImg(prev => ({ ...prev, [partKey]: true }));
    try {
      const newImageUrl = await generateVisual(prompt);
      const updated = [...localVariations];
      updated[activeVariationIdx][partKey].imageUrl = newImageUrl;
      setLocalVariations(updated);
    } catch (error) {
      console.error("Failed to regenerate image:", error);
    } finally {
      setIsRegeneratingImg(prev => ({ ...prev, [partKey]: false }));
    }
  };

  const currentVar = localVariations[activeVariationIdx];

  const handleDownloadJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentVar, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `${currentVar.title}_script.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    
    setCopyStatus(true);
    setTimeout(() => setCopyStatus(false), 2000);
  };

  const InfoWindow = ({ title, content, icon, colorClass }: { title: string, content: string, icon: string, colorClass: string }) => (
    <div className={`glass border border-white/10 rounded-3xl overflow-hidden shadow-lg mb-4 bg-slate-950/40 animate-in fade-in duration-500`}>
      <div className="bg-slate-950/80 px-5 py-3 border-b border-white/5 flex items-center space-x-3">
        <i className={`fas ${icon} ${colorClass} text-sm`}></i>
        <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">{title}</span>
      </div>
      <div className="p-5">
        <p className="text-sm text-slate-200 leading-relaxed font-medium">
          {content}
        </p>
      </div>
    </div>
  );

  const JsonEditorWindow = ({ 
    title, 
    data, 
    fields, 
    onFieldChange, 
    icon,
    onRegenerate
  }: { 
    title: string, 
    data: any, 
    fields: {label: string, key: keyof ScriptPart}[], 
    onFieldChange: (field: keyof ScriptPart, val: string) => void,
    icon: string,
    onRegenerate?: () => void
  }) => (
    <div className="flex flex-col h-full glass border border-white/10 rounded-[2rem] overflow-hidden shadow-2xl bg-slate-950/30 group/editor">
      <div className="bg-slate-950/80 px-5 py-4 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center">
            <i className={`fas ${icon} text-purple-400 text-sm`}></i>
          </div>
          <span className="text-xs font-black text-slate-300 uppercase tracking-widest">{title}</span>
        </div>
        <div className="flex space-x-1.5 opacity-30 group-hover/editor:opacity-100 transition-opacity">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500/50"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
        </div>
      </div>
      
      <div className="p-5 bg-slate-950/30 space-y-4 border-b border-white/5">
        {fields.map(f => (
          <div key={f.key} className="flex flex-col space-y-2">
            <div className="flex items-center justify-between px-1">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">{f.label}</label>
              {f.key === 'visualPrompt' && onRegenerate && (
                <button 
                  onClick={onRegenerate}
                  disabled={isRegeneratingImg[title.includes('1') ? 'part1' : 'part2']}
                  className="w-7 h-7 rounded-lg bg-purple-500/10 text-purple-400 hover:text-purple-300 transition-all flex items-center justify-center hover:scale-110 active:scale-90"
                  title="이미지 다시 생성"
                >
                  <i className={`fas fa-sync-alt text-xs ${isRegeneratingImg[title.includes('1') ? 'part1' : 'part2'] ? 'fa-spin' : ''}`}></i>
                </button>
              )}
            </div>
            <textarea 
              value={data[f.key] || ''} 
              onChange={(e) => onFieldChange(f.key, e.target.value)}
              className="bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 text-xs text-purple-100 focus:border-purple-500/50 focus:ring-4 focus:ring-purple-500/10 outline-none transition-all resize-none leading-relaxed"
              rows={2}
            />
          </div>
        ))}
      </div>

      <div className="flex-1 p-5 bg-slate-950/90 font-mono text-[11px] overflow-auto custom-scrollbar">
        <div className="flex justify-between items-center mb-2 px-1">
          <span className="text-[9px] text-slate-500 uppercase">Live JSON Output</span>
          <div className="flex space-x-2">
            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse"></div>
          </div>
        </div>
        <pre className="text-emerald-400/90">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
      {/* Header / Tabs */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-6 bg-slate-900/40 p-2 rounded-[2rem] border border-white/5 backdrop-blur-sm">
        <div className="flex space-x-2 p-1">
          {localVariations.map((v, idx) => (
            <button
              key={idx}
              onClick={() => setActiveVariationIdx(idx)}
              className={`px-8 py-3 rounded-2xl font-black text-sm transition-all duration-300 flex items-center gap-3 ${
                activeVariationIdx === idx 
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-xl shadow-purple-600/20' 
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
              }`}
            >
              <i className={`fas ${v.style.includes('말장난') || v.style.toLowerCase().includes('wordplay') ? 'fa-quote-left' : 'fa-bolt-lightning'} text-xs`}></i>
              {lang === 'en' ? v.style.split('(')[1]?.replace(')', '') || v.style : v.style}
            </button>
          ))}
        </div>
        <button
          onClick={onReset}
          className="px-8 py-3 bg-slate-800/50 hover:bg-slate-800 text-slate-300 rounded-2xl transition-all flex items-center text-sm font-black border border-white/5 group"
        >
          <i className="fas fa-plus mr-3 group-hover:rotate-90 transition-transform"></i> {t('result.reset')}
        </button>
      </div>

      {/* Algo Check Results */}
      {algoCheck.data && (
        <div className="glass border border-emerald-500/30 p-8 rounded-[2.5rem] animate-in slide-in-from-top-4 duration-500 shadow-2xl bg-emerald-500/5 overflow-hidden relative">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-[80px] rounded-full"></div>
          
          <div className="flex items-center justify-between mb-8 relative z-10">
            <div className="flex items-center space-x-5">
              <div className="w-16 h-16 rounded-[1.25rem] bg-emerald-500 flex items-center justify-center shadow-xl shadow-emerald-500/30">
                <span className="text-white font-black text-2xl">{algoCheck.data.score}</span>
              </div>
              <div>
                <h4 className="text-white text-xl font-black tracking-tight">AI Algorithm Audit</h4>
                <p className="text-emerald-400 text-sm font-bold mt-1">{algoCheck.data.trendingStatus}</p>
              </div>
            </div>
            <button 
              onClick={() => setAlgoCheck({ loading: false, data: null })} 
              className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-500 hover:text-white transition-all hover:bg-white/10"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 relative z-10">
            <div className="space-y-6">
              <div className="bg-slate-950/60 p-6 rounded-3xl border border-white/5 backdrop-blur-sm">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">Safety & Policy</p>
                <p className="text-sm text-slate-200 leading-relaxed font-medium">{algoCheck.data.safetyCheck}</p>
              </div>
              <div className="flex flex-wrap gap-3">
                {algoCheck.data.searchSources?.map((s, i) => (
                  <a key={i} href={s.uri} target="_blank" className="text-[10px] bg-emerald-500/10 text-emerald-300 px-4 py-2 rounded-xl border border-emerald-500/20 hover:bg-emerald-500/20 transition-all flex items-center font-bold">
                    <i className="fas fa-globe mr-2"></i> {s.title}
                  </a>
                ))}
              </div>
            </div>
            <div className="bg-slate-950/60 p-6 rounded-3xl border border-white/5 backdrop-blur-sm">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Viral Optimization Tips</p>
              <ul className="space-y-3">
                {algoCheck.data.optimizationTips.map((tip, i) => (
                  <li key={i} className="text-sm text-slate-200 flex items-start space-x-3 group">
                    <div className="mt-1 w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                      <i className="fas fa-check text-[8px] text-emerald-500"></i>
                    </div>
                    <span className="font-medium">{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Areas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Part 1 */}
        <div className="flex flex-col space-y-5 animate-in slide-in-from-left-4 duration-700">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center space-x-3">
              <span className="bg-purple-600 text-white text-[10px] font-black px-3 py-1 rounded-lg shadow-lg shadow-purple-600/30 tracking-widest uppercase">PART 1</span>
              <span className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">{lang === 'ko' ? '도입부 (0-8초)' : 'HOOK (0-8s)'}</span>
            </div>
          </div>

          <InfoWindow 
            title={lang === 'ko' ? '파트 1 장면 요약' : 'Part 1 Scene Summary'}
            content={currentVar.part1.humorPoint}
            icon="fa-lightbulb"
            colorClass="text-yellow-400"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 h-[550px]">
            <JsonEditorWindow 
              title={lang === 'ko' ? '파트 1 스크립트' : 'Part 1 Script'}
              icon="fa-film"
              data={{ 
                timestamp: currentVar.part1.timestamp, 
                content: currentVar.part1.content, 
                humorPoint: currentVar.part1.humorPoint 
              }}
              fields={[
                { label: t('result.humorPoint'), key: 'humorPoint' },
                { label: 'Script', key: 'content' }
              ]}
              onFieldChange={(f, v) => updateField('part1', f, v)}
            />
            <JsonEditorWindow 
              title={lang === 'ko' ? '파트 1 프롬프트' : 'Part 1 Prompt'}
              icon="fa-paint-brush"
              data={{ visualPrompt: currentVar.part1.visualPrompt }}
              fields={[
                { label: t('result.visualPrompt'), key: 'visualPrompt' }
              ]}
              onFieldChange={(f, v) => updateField('part1', f, v)}
              onRegenerate={() => handleRegenerateImage('part1')}
            />
          </div>

          <div className="h-80 rounded-[2.5rem] overflow-hidden border border-white/10 relative group bg-slate-900 flex items-center justify-center shadow-2xl transition-all duration-500 hover:border-purple-500/50">
            {isRegeneratingImg['part1'] ? (
              <div className="flex flex-col items-center space-y-4">
                <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">AI Regenerating...</span>
              </div>
            ) : (
              <>
                <img src={currentVar.part1.imageUrl} className="w-full h-full object-cover opacity-70 group-hover:scale-105 transition-transform duration-[2000ms]" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent flex flex-col justify-end p-8">
                   <div className="bg-black/40 backdrop-blur-md p-4 rounded-2xl border border-white/10">
                     <p className="text-white text-sm font-bold italic line-clamp-2 leading-relaxed tracking-tight group-hover:text-purple-300 transition-colors">"{currentVar.part1.content}"</p>
                   </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Part 2 */}
        <div className="flex flex-col space-y-5 animate-in slide-in-from-right-4 duration-700">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center space-x-3">
              <span className="bg-pink-600 text-white text-[10px] font-black px-3 py-1 rounded-lg shadow-lg shadow-pink-600/30 tracking-widest uppercase">PART 2</span>
              <span className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">{lang === 'ko' ? '펀치라인 (8-16초)' : 'TWIST (8-16s)'}</span>
            </div>
          </div>

          <InfoWindow 
            title={lang === 'ko' ? '파트 2 장면 요약' : 'Part 2 Scene Summary'}
            content={currentVar.part2.humorPoint}
            icon="fa-bolt"
            colorClass="text-pink-400"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 h-[550px]">
            <JsonEditorWindow 
              title={lang === 'ko' ? '파트 2 스크립트' : 'Part 2 Script'}
              icon="fa-fire"
              data={{ 
                timestamp: currentVar.part2.timestamp, 
                content: currentVar.part2.content, 
                humorPoint: currentVar.part2.humorPoint 
              }}
              fields={[
                { label: t('result.humorPoint'), key: 'humorPoint' },
                { label: 'Script', key: 'content' }
              ]}
              onFieldChange={(f, v) => updateField('part2', f, v)}
            />
            <JsonEditorWindow 
              title={lang === 'ko' ? '파트 2 프롬프트' : 'Part 2 Prompt'}
              icon="fa-wand-magic-sparkles"
              data={{ visualPrompt: currentVar.part2.visualPrompt }}
              fields={[
                { label: t('result.visualPrompt'), key: 'visualPrompt' }
              ]}
              onFieldChange={(f, v) => updateField('part2', f, v)}
              onRegenerate={() => handleRegenerateImage('part2')}
            />
          </div>

          <div className="h-80 rounded-[2.5rem] overflow-hidden border border-white/10 relative group bg-slate-900 flex items-center justify-center shadow-2xl transition-all duration-500 hover:border-pink-500/50">
            {isRegeneratingImg['part2'] ? (
              <div className="flex flex-col items-center space-y-4">
                <div className="w-12 h-12 border-4 border-pink-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">AI Regenerating...</span>
              </div>
            ) : (
              <>
                <img src={currentVar.part2.imageUrl} className="w-full h-full object-cover opacity-70 group-hover:scale-105 transition-transform duration-[2000ms]" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent flex flex-col justify-end p-8">
                   <div className="bg-black/40 backdrop-blur-md p-4 rounded-2xl border border-white/10">
                     <p className="text-white text-sm font-bold italic line-clamp-2 leading-relaxed tracking-tight group-hover:text-pink-300 transition-colors">"{currentVar.part2.content}"</p>
                   </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Production Controls */}
      <div className="glass border border-purple-500/20 p-10 rounded-[3rem] shadow-2xl relative overflow-hidden bg-slate-900/40 backdrop-blur-xl group/controls">
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-purple-600/10 blur-[100px] rounded-full group-hover/controls:bg-purple-600/20 transition-all duration-700"></div>
        
        <div className="flex flex-col lg:flex-row items-center justify-between gap-10 relative z-10">
          <div className="flex items-center space-x-8">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center shadow-2xl shadow-purple-600/40 relative group-hover/controls:rotate-6 transition-transform duration-500">
              <i className="fas fa-microchip text-white text-3xl"></i>
              <div className="absolute inset-0 bg-white/20 rounded-3xl opacity-0 group-hover/controls:opacity-100 transition-opacity"></div>
            </div>
            <div>
              <h4 className="text-white text-3xl font-black tracking-tight mb-2">Architect Workstation</h4>
              <div className="flex items-center gap-3">
                <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <p className="text-slate-400 text-[10px] uppercase font-black tracking-[0.3em]">State: Ready for Deployment</p>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
            <button 
              onClick={runAlgoCheck}
              disabled={algoCheck.loading}
              className="px-10 py-5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-black rounded-2xl shadow-2xl shadow-emerald-600/30 transition-all flex items-center justify-center gap-3 group/btn relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/10 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-1000"></div>
              {algoCheck.loading ? (
                <i className="fas fa-circle-notch fa-spin"></i>
              ) : (
                <i className="fas fa-shield-check text-xl"></i>
              )}
              {lang === 'ko' ? '알고리즘 정밀 점검' : 'Algorithm Audit'}
            </button>
            <button 
              onClick={handleDownloadJson}
              className="px-10 py-5 glass hover:bg-white/10 text-white font-black rounded-2xl transition-all active:scale-95 shadow-xl flex items-center justify-center gap-3 border border-white/10"
            >
              <i className={`fas ${copyStatus ? 'fa-check text-emerald-400' : 'fa-download text-purple-400'} text-xl`}></i>
              {copyStatus ? t('result.copied') : t('result.copy') + ' JSON'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScriptResult;
