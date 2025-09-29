import React, { useState, createContext, useContext } from "react";
import { getLocalStorage, setLocalStorage } from "../components/utils/utils";

// Korean translations
const translations = {
  ko: {
    // Header/Navigation
    "Build": "구축",
    "Playground": "놀이터",
    "Gallery": "갤러리", 
    "Data Explorer": "데이터 탐색기",
    
    // General UI
    "Settings": "설정",
    "Profile": "프로필",
    "Sign out": "로그아웃",
    "Dark mode": "다크 모드",
    "Light mode": "라이트 모드",
    
    // Teams and Agents
    "Teams": "팀",
    "Agents": "에이전트",
    "Models": "모델",
    "Tools": "도구",
    "Create": "생성",
    "Edit": "편집",
    "Delete": "삭제",
    "Save": "저장",
    "Cancel": "취소",
    
    // Messages
    "Loading...": "로딩 중...",
    "Error": "오류",
    "Success": "성공",
    "Warning": "경고",
    "Information": "정보",
    
    // Chat
    "Send message": "메시지 보내기",
    "Type your message...": "메시지를 입력하세요...",
    "Clear chat": "채팅 지우기",
    "New conversation": "새 대화",
    
    // AutoGen Studio specific
    "AutoGen Studio": "AutoGen 스튜디오",
    "Build multi-agent teams": "멀티 에이전트 팀 구축",
    "Chat with your team": "팀과 채팅하기",
    "Configure agents": "에이전트 설정",
    
    // Gallery items  
    "Calculator Tool": "계산기 도구",
    "RoundRobin Team": "라운드로빈 팀",
    "Selector Team": "선택자 팀", 
    "Swarm Team": "스웜 팀",
    "Korean Discussion Team": "한국어 토론 팀",
    "Web Surfer Team": "웹 서퍼 팀",
    "Deep Research Team": "심층 연구 팀",
    
    // Termination conditions
    "TERMINATE": "종료",
    "Text Mention Termination": "텍스트 언급 종료",
    "Max Message Termination": "최대 메시지 종료",
    "OR Termination": "OR 종료 조건",
  },
  en: {
    // English translations (fallback)
    "Build": "Build",
    "Playground": "Playground", 
    "Gallery": "Gallery",
    "Data Explorer": "Data Explorer",
    "Settings": "Settings",
    "Profile": "Profile",
    "Sign out": "Sign out",
    "Dark mode": "Dark mode",
    "Light mode": "Light mode",
    "Teams": "Teams",
    "Agents": "Agents",
    "Models": "Models", 
    "Tools": "Tools",
    "Create": "Create",
    "Edit": "Edit",
    "Delete": "Delete",
    "Save": "Save",
    "Cancel": "Cancel",
    "Loading...": "Loading...",
    "Error": "Error",
    "Success": "Success", 
    "Warning": "Warning",
    "Information": "Information",
    "Send message": "Send message",
    "Type your message...": "Type your message...",
    "Clear chat": "Clear chat",
    "New conversation": "New conversation",
    "AutoGen Studio": "AutoGen Studio",
    "Build multi-agent teams": "Build multi-agent teams",
    "Chat with your team": "Chat with your team", 
    "Configure agents": "Configure agents",
    "Calculator Tool": "Calculator Tool",
    "RoundRobin Team": "RoundRobin Team",
    "Selector Team": "Selector Team",
    "Swarm Team": "Swarm Team", 
    "Korean Discussion Team": "Korean Discussion Team",
    "Web Surfer Team": "Web Surfer Team",
    "Deep Research Team": "Deep Research Team",
    "TERMINATE": "TERMINATE",
    "Text Mention Termination": "Text Mention Termination",
    "Max Message Termination": "Max Message Termination", 
    "OR Termination": "OR Termination",
  }
};

export type Language = 'ko' | 'en';
export type TranslationKey = keyof typeof translations.ko;

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: TranslationKey, fallback?: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  language: 'ko',
  setLanguage: () => {},
  t: (key) => key,
});

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Default to Korean as specified in requirements
  const storedLanguage = getLocalStorage("language", "ko") as Language;
  const [language, setLanguage] = useState<Language>(storedLanguage || 'ko');

  const updateLanguage = (lang: Language) => {
    setLanguage(lang);
    setLocalStorage("language", lang, false);
  };

  const t = (key: TranslationKey, fallback?: string): string => {
    const translation = translations[language]?.[key] || translations.en[key] || fallback || key;
    return translation;
  };

  return (
    <I18nContext.Provider value={{
      language,
      setLanguage: updateLanguage,
      t
    }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

// Higher-order component for class components  
export const withI18n = <P extends object>(Component: React.ComponentType<P & I18nContextType>) => {
  return (props: P) => {
    const i18nProps = useI18n();
    return <Component {...props} {...i18nProps} />;
  };
};