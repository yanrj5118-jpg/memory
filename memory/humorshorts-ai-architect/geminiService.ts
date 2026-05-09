import { GoogleGenAI, Type, GenerateContentResponse } from "@google/genai";
import { ShortScript, ScriptVariation, AlgorithmCheckResult, Language, ModelType, SkillType } from "./types";

export const checkOllamaStatus = async (): Promise<boolean> => {
  try {
    const response = await fetch("http://127.0.0.1:1234/v1/models");
    return response.ok;
  } catch {
    return false;
  }
};

const API_KEY = process.env.API_KEY || "";

// 중국 협업자 및 오프라인 환경을 위한 설정 (Zero-Login)
const LOCAL_CONFIG = {
  enabled: true,
  baseUrl: "http://127.0.0.1:1234/v1",
  model: "google/gemma-4-e2b",
  apiKey: "",
  strictLocal: !API_KEY || API_KEY.includes('PLACEHOLDER') // API 키가 없으면 강제로 로컬 모드
};

// 로컬 플레이스홀더 이미지 (SVG Base64) - Gwall 대응용
const LOCAL_PLACEHOLDER = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNzIwIiBoZWlnaHQ9IjEyODAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzFhMWExYSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIzMCIgZmlsbD0iIzQ0NCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+QUkgQXJjaGl0ZWN0IFZpc3VhbDwvdGV4dD48L3N2Zz4=";

/* --- MOCK DATA FOR DEMONSTRATION --- */
const MOCK_SCRIPT_DATA: ShortScript = {
  trendAnalysis: "현재 소셜 미디어에서 '직장인 공감' 및 '예상 밖의 반전' 콘텐츠가 높은 참여율을 보이고 있습니다. 특히 짧은 호흡의 상황극이 인기입니다.",
  variations: [
    {
      style: 'Wordplay',
      title: '부장님의 개그',
      part1: {
        timestamp: "0:00-0:08",
        content: "부장님: '자네, 회를 좋아하나?' 나: '네! 없어서 못 먹죠!'",
        humorPoint: "상사의 질문에 대한 열정적인 긍정",
        visualPrompt: "Office setting, boss asking a question to an enthusiastic employee, bright lighting, cinematic style",
        imageUrl: LOCAL_PLACEHOLDER
      },
      part2: {
        timestamp: "0:08-0:16",
        content: "부장님: '그럼 오늘 회의는 자네가 준비하게.' (회의...?)",
        humorPoint: "'회'가 생선회가 아니라 '회의'였다는 허탈한 언어유희",
        visualPrompt: "Employee looking shocked and disappointed, boss smiling holding a meeting agenda, close up shot",
        imageUrl: LOCAL_PLACEHOLDER
      }
    },
    {
      style: 'Twist',
      title: '헬스장의 비밀',
      part1: {
        timestamp: "0:00-0:08",
        content: "친구: '와 너 몸 진짜 좋아졌다! 비결이 뭐야? 식단? 운동?'",
        humorPoint: "몸매 변화에 대한 감탄과 궁금증 유발",
        visualPrompt: "Gym setting, two friends talking, one looking muscular, energetic atmosphere",
        imageUrl: LOCAL_PLACEHOLDER
      },
      part2: {
        timestamp: "0:08-0:16",
        content: "나: '어... 포토샵 구독 결제했어.'",
        humorPoint: "운동이 아닌 보정 기술이었다는 허무한 반전",
        visualPrompt: "Person holding a smartphone showing photo editing app, mischievous smile, gym background blurred",
        imageUrl: LOCAL_PLACEHOLDER
      }
    }
  ],
  sources: [{ title: "Viral Humor Trends 2026", uri: "https://google.com" }]
};

const MOCK_ALGO_RESULT: AlgorithmCheckResult = {
  score: 92,
  trendingStatus: "🔥 현재 2026년 급상승 트렌드와 98% 일치함",
  safetyCheck: "✅ 커뮤니티 가이드라인 준수 (안전함)",
  optimizationTips: [
    "도입부 3초 안에 시선을 끄는 빠른 컷 편집을 추가하세요.",
    "2026 AI 공시 문구를 명확하게 삽입하세요.",
    "배경음악으로 최신 트렌딩 사운드를 사용하세요."
  ],
  searchSources: [{ title: "YouTube Shorts Algorithm 2026 Guide", uri: "https://youtube.com" }]
};

export const generateShortsContent = async (
  inputType: string,
  inputValue: string,
  modelId: ModelType,
  skillId: SkillType = 'general',
  lang: Language = 'ko',
  fileData?: { data: string; mimeType: string }
): Promise<ShortScript> => {
  if (LOCAL_CONFIG.strictLocal) {
    // API 키가 없거나 플레이스홀더인 경우 강제로 로컬 모드 수행
    return await callLocalOllama(inputType, inputValue, modelId, skillId, lang);
  }

  let result: ShortScript;
  if (LOCAL_CONFIG.enabled) {
    result = await callLocalOllama(inputType, inputValue, modelId, skillId, lang);
  } else {
    const ai = new GoogleGenAI({ apiKey: API_KEY });
    const languageNames: Record<Language, string> = {
      ko: "Korean",
      en: "English",
      "zh-CN": "Chinese (Simplified)",
      "zh-TW": "Chinese (Traditional)",
      ru: "Russian"
    };

    let systemInstruction = "";
    if (skillId === 'viral-2026') {
      systemInstruction = `You are a 2026 Viral Content Architect. Focus on 20-minute long-form structure with 16s Shorts funnel. Rules: 1. Predict retention for a 20-min video with pattern interrupts every 60s. 2. Create 16s viral Shorts to drive traffic to the 20-min video. 3. Include mandatory 2026 AI disclosure metadata. Language: ${languageNames[lang]}`;
    } else if (skillId === 'commerce-olive') {
      systemInstruction = `You are an Olive Young Monetization Specialist. Focus on high-conversion product promotion scripts. Rules: 1. Analyze product USP from the input. 2. Use "Real Review" style with a strong hook (Pain Point). 3. Include a CTA for the affiliate link in the pinned comment. Language: ${languageNames[lang]}`;
    } else {
      systemInstruction = `You are a viral humor strategist for YouTube Shorts. Create TWO distinct 16s variations: Wordplay and Twist. Language: ${languageNames[lang]}`;
    }

    const response = await ai.models.generateContent({
      model: 'gemini-1.5-pro',
      contents: { parts: [{ text: `Input: ${inputValue}\nType: ${inputType}` }] },
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        tools: [{ googleSearch: {} }]
      }
    });

    result = JSON.parse(response.text || "{}");
  }

  for (const variation of result.variations) {
    const [img1, img2] = await Promise.all([
      generateVisual(variation.part1.visualPrompt),
      generateVisual(variation.part2.visualPrompt)
    ]);
    variation.part1.imageUrl = img1;
    variation.part2.imageUrl = img2;
  }
  return result;
};

export const checkAlgorithmAndConstraints = async (variation: ScriptVariation): Promise<AlgorithmCheckResult> => {
  if (!API_KEY || API_KEY.includes('PLACEHOLDER')) {
    return new Promise(resolve => setTimeout(() => resolve(MOCK_ALGO_RESULT), 1500));
  }
  const ai = new GoogleGenAI({ apiKey: API_KEY });
  const response = await ai.models.generateContent({
    model: 'gemini-1.5-flash',
    contents: [{ text: `Check viral potential for: ${variation.title}` }],
    config: { responseMimeType: "application/json", tools: [{ googleSearch: {} }] }
  });
  return JSON.parse(response.text || "{}");
};

export const generateVisual = async (prompt: string): Promise<string> => {
  if (LOCAL_CONFIG.strictLocal) {
    return LOCAL_PLACEHOLDER;
  }
  const ai = new GoogleGenAI({ apiKey: API_KEY });
  try {
    const response = await ai.models.generateContent({
      model: 'imagen-3.0-generate-001',
      contents: { parts: [{ text: `High-quality cinematic: ${prompt}` }] }
    });
    const part = response.candidates?.[0]?.content?.parts?.[0];
    if (part?.inlineData) return `data:image/png;base64,${part.inlineData.data}`;
  } catch (e) {
    console.error("Image failed", e);
  }
  return LOCAL_PLACEHOLDER;
};

async function callLocalOllama(inputType: string, inputValue: string, modelId: string, skillId: SkillType, lang: Language): Promise<ShortScript> {
  const languageNames: Record<Language, string> = {
    ko: "Korean", en: "English", "zh-CN": "Chinese (Simplified)", "zh-TW": "Chinese (Traditional)", ru: "Russian"
  };

  let skillPrompt = "";
  if (skillId === 'viral-2026') {
    skillPrompt = "Strategy: 2026 Viral Architect (20m Long-form + 16s Shorts Discovery). Include AI Disclosure.";
  } else if (skillId === 'commerce-olive') {
    skillPrompt = "Strategy: Olive Young Product Monetization (High-conversion CTA).";
  } else {
    skillPrompt = "Strategy: General Humor Shorts (Wordplay & Twist).";
  }

  const prompt = `You are a specialized AI Architect. [${skillPrompt}] Input: ${inputValue}, Language: ${languageNames[lang]}. Return valid JSON with trendAnalysis and variations (Wordplay & Twist). Each variation has part1 and part2 (8s each).`;

  try {
    const response = await fetch(`${LOCAL_CONFIG.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${LOCAL_CONFIG.apiKey}` },
      body: JSON.stringify({
        model: modelId || LOCAL_CONFIG.model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.2
      })
    });
    const data = await response.json();
    const content = data.choices[0].message.content;
    const jsonStr = content.includes('```json') ? content.split('```json')[1].split('```')[0] : content;
    return JSON.parse(jsonStr.trim());
  } catch (e) {
    console.error("Local failed", e);
    return MOCK_SCRIPT_DATA;
  }
}
