import { Platform } from 'react-native';
import { Category } from '../types/navigation';

// API configuration
const DEV_API_URL = Platform.select({
  ios: 'http://10.0.0.216:8501/api',
  android: 'http://10.0.0.216:8501/api',
  default: 'http://10.0.0.216:8501/api'
});

const PROD_API_URL = 'https://your-production-api.com/api';  // Update with your production API URL

export const API_URL = __DEV__ ? DEV_API_URL : PROD_API_URL;

// Fallback word lists
const fallbackWords: Record<Category, Record<number, string[]>> = {
  general: {
    3: ['cat', 'dog', 'hat'],
    4: ['book', 'lamp', 'desk'],
    5: ['house', 'phone', 'table'],
    // Add more words for other lengths
  },
  animals: {
    3: ['cat', 'dog', 'owl'],
    4: ['bear', 'lion', 'wolf'],
    5: ['tiger', 'zebra', 'koala'],
  },
  food: {
    3: ['pie', 'ham', 'egg'],
    4: ['cake', 'soup', 'fish'],
    5: ['pizza', 'pasta', 'salad'],
  },
  places: {
    3: ['bay', 'sea', 'sky'],
    4: ['city', 'town', 'park'],
    5: ['beach', 'hotel', 'plaza'],
  },
  science: {
    3: ['lab', 'dna', 'ion'],
    4: ['atom', 'cell', 'gene'],
    5: ['laser', 'quark', 'space'],
  },
  tech: {
    3: ['app', 'web', 'cpu'],
    4: ['code', 'data', 'wifi'],
    5: ['cloud', 'phone', 'robot'],
  },
  music: {
    3: ['pop', 'rap', 'mix'],
    4: ['jazz', 'rock', 'song'],
    5: ['blues', 'piano', 'drums'],
  }
};

// Fallback hint generation
export const getFallbackHint = (question: string, word: string): string => {
  const lowerQuestion = question.toLowerCase();
  const lowerWord = word.toLowerCase();

  if (lowerQuestion.includes('start') && lowerQuestion.includes('letter')) {
    return `The word ${lowerWord[0] === lowerWord[0].toLowerCase() ? 'does' : 'does not'} start with '${lowerWord[0]}'`;
  }

  if (lowerQuestion.includes('end') && lowerQuestion.includes('letter')) {
    return `The word ${lowerWord[lowerWord.length - 1] === lowerWord[lowerWord.length - 1].toLowerCase() ? 'does' : 'does not'} end with '${lowerWord[lowerWord.length - 1]}'`;
  }

  if (lowerQuestion.includes('contain') || lowerQuestion.includes('has')) {
    const letters = lowerQuestion.match(/[a-z]/g) || [];
    for (const letter of letters) {
      if (lowerWord.includes(letter)) {
        return `Yes, the word contains the letter '${letter}'`;
      }
    }
    return 'No, the word does not contain that letter';
  }

  if (lowerQuestion.includes('length') || lowerQuestion.includes('long')) {
    return `The word is ${word.length} letters long`;
  }

  return 'I cannot answer that question. Try asking about specific letters or the word length.';
};

// Get a random word from fallback list
export const getFallbackWord = (category: Category, length: number): string => {
  const words = fallbackWords[category][length] || fallbackWords.general[length];
  return words[Math.floor(Math.random() * words.length)];
}; 