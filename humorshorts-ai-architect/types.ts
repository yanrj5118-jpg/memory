
export interface ScriptPart {
  timestamp: string;
  content: string;
  humorPoint: string;
  visualPrompt: string;
  imageUrl?: string;
}

export interface ScriptVariation {
  style: string;
  title: string;
  part1: ScriptPart;
  part2: ScriptPart;
}

export interface ShortScript {
  trendAnalysis: string;
  variations: ScriptVariation[];
  sources: Array<{ title: string; uri: string }>;
}

export interface AlgorithmCheckResult {
  score: number;
  trendingStatus: string;
  safetyCheck: string;
  optimizationTips: string[];
  searchSources: Array<{ title: string; uri: string }>;
}

export type InputType = 'text' | 'url' | 'image' | 'video';
export type Language = 'ko' | 'en' | 'zh-CN' | 'zh-TW' | 'ru';
export type ModelType = 'gemma4:e2b' | 'gemma4:e4b';
export type SkillType = 'general' | 'viral-2026' | 'commerce-olive';

export interface AppState {
  isAnalyzing: boolean;
  error: string | null;
  result: ShortScript | null;
  selectedModel: ModelType;
  selectedSkill: SkillType;
}
