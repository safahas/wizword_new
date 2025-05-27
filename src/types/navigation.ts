export type RootStackParamList = {
  Home: undefined;
  Game: {
    wordLength: number;
    category: string;
    mode: 'fun' | 'challenge';
    nickname?: string;
  };
  Result: {
    word: string;
    score: number;
    questionsCount: number;
    timeTaken: number;
  };
};

export type GameMode = 'fun' | 'challenge';
export type Category = 'general' | 'animals' | 'food' | 'places' | 'science' | 'tech' | 'music';

export interface Hint {
  question: string;
  answer: string;
}

export interface ApiResponse {
  hint?: string;
  isCorrect: boolean;
  error?: string;
} 