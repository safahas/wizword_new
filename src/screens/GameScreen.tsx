import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Button, Text, TextInput, Card, ActivityIndicator, Portal, Dialog, Snackbar } from 'react-native-paper';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import axios from 'axios';
import { RootStackParamList, Hint, ApiResponse, Category } from '../types/navigation';
import { API_URL, getFallbackHint, getFallbackWord } from '../config/api';

type Props = NativeStackScreenProps<RootStackParamList, 'Game'>;

export default function GameScreen({ route, navigation }: Props) {
  const { wordLength, category, mode, nickname } = route.params;
  const [question, setQuestion] = useState('');
  const [hints, setHints] = useState<Hint[]>([]);
  const [finalGuess, setFinalGuess] = useState('');
  const [score, setScore] = useState(0);
  const [startTime] = useState(Date.now());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fallbackMode, setFallbackMode] = useState(true);
  const [targetWord, setTargetWord] = useState('');

  useEffect(() => {
    // Initialize the game with a fallback word
    const word = getFallbackWord(category as Category, wordLength);
    setTargetWord(word);
    console.log('Selected word:', word);  // For debugging
  }, []);

  const askQuestion = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Always use fallback mode for now
      const hint = getFallbackHint(question, targetWord);
      console.log('Question:', question, 'Hint:', hint);  // For debugging
      setHints(prev => [...prev, { question, answer: hint }]);
      
      if (mode === 'challenge') {
        setScore(prev => prev + 10);
      }
      
      setQuestion('');
    } catch (error) {
      console.error('Error processing question:', error);
      setError('Failed to process question. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const submitGuess = async () => {
    setLoading(true);
    setError(null);

    try {
      if (fallbackMode) {
        const isCorrect = finalGuess.toLowerCase() === targetWord.toLowerCase();
        if (isCorrect) {
          navigation.navigate('Result', {
            word: targetWord,
            score,
            questionsCount: hints.length,
            timeTaken: (Date.now() - startTime) / 1000
          });
        } else {
          setError('Incorrect guess. Try again!');
          if (mode === 'challenge') {
            setScore(prev => prev + 10);
          }
        }
      } else {
        const response = await axios.post<ApiResponse>(`${API_URL}/guess`, {
          guess: finalGuess,
          wordLength,
          category,
          mode,
          nickname
        });
        
        if (response.data.isCorrect) {
          navigation.navigate('Result', {
            word: finalGuess,
            score,
            questionsCount: hints.length,
            timeTaken: (Date.now() - startTime) / 1000
          });
        } else {
          setError('Incorrect guess. Try again!');
          if (mode === 'challenge') {
            setScore(prev => prev + 10);
          }
        }
      }
    } catch (error) {
      console.error('Error submitting guess:', error);
      setError('Failed to submit guess. Switching to offline mode...');
      setFallbackMode(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {fallbackMode && (
        <Card style={styles.offlineCard}>
          <Card.Content>
            <Text variant="titleMedium">Offline Mode</Text>
            <Text variant="bodyMedium">Playing with local word list</Text>
          </Card.Content>
        </Card>
      )}

      <ScrollView style={styles.hintsContainer}>
        <Card style={styles.hintCountCard}>
          <Card.Content>
            <Text variant="titleMedium" style={styles.hintCount}>
              Hints Available: {5 - hints.length}
            </Text>
            <Text variant="bodySmall" style={styles.hintInfo}>
              {hints.length >= 5 ? 'Maximum hints reached' : 'Ask questions to get hints'}
            </Text>
          </Card.Content>
        </Card>

        <View style={styles.hintsSection}>
          <Text variant="titleLarge" style={styles.sectionTitle}>Hints History</Text>
          {hints.map((hint, index) => (
            <Card key={index} style={styles.hintCard}>
              <Card.Content>
                <Text variant="titleMedium" style={styles.question}>Question #{index + 1}:</Text>
                <Text variant="bodyMedium" style={styles.questionText}>{hint.question}</Text>
                <View style={styles.hintDivider} />
                <Text variant="titleMedium" style={styles.hintLabel}>Hint:</Text>
                <Text variant="bodyMedium" style={styles.answer}>{hint.answer}</Text>
              </Card.Content>
            </Card>
          ))}
        </View>
      </ScrollView>

      <Card style={styles.inputCard}>
        <Card.Content>
          <Text variant="titleLarge" style={styles.sectionTitle}>Ask a Question</Text>
          <TextInput
            label={`Yes/No Question (${5 - hints.length} hints remaining)`}
            value={question}
            onChangeText={setQuestion}
            style={styles.input}
            disabled={loading || hints.length >= 5}
          />
          <Button
            mode="contained"
            onPress={askQuestion}
            disabled={!question || loading || hints.length >= 5}
            style={styles.button}
            loading={loading}
            icon="lightbulb-on"
          >
            Get Hint
          </Button>

          <View style={styles.guessSection}>
            <Text variant="titleLarge" style={styles.sectionTitle}>Make a Guess</Text>
            <TextInput
              label="Your final guess"
              value={finalGuess}
              onChangeText={setFinalGuess}
              style={styles.input}
              disabled={loading}
            />
            <Button
              mode="contained"
              onPress={submitGuess}
              disabled={!finalGuess || loading}
              style={styles.button}
              loading={loading}
            >
              Submit Guess
            </Button>
          </View>
        </Card.Content>
      </Card>

      {mode === 'challenge' && (
        <Card style={styles.scoreCard}>
          <Card.Content>
            <Text variant="headlineSmall" style={styles.score}>
              Score: {score}
            </Text>
          </Card.Content>
        </Card>
      )}

      <Snackbar
        visible={!!error}
        onDismiss={() => setError(null)}
        action={{
          label: 'Dismiss',
          onPress: () => setError(null),
        }}
      >
        {error}
      </Snackbar>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#B5E3FF',  // Light blue background
  },
  offlineCard: {
    marginBottom: 16,
    backgroundColor: '#fff3e0',
  },
  hintsContainer: {
    flex: 1,
    marginBottom: 16,
  },
  hintsSection: {
    marginTop: 16,
  },
  sectionTitle: {
    color: '#1976d2',
    fontWeight: 'bold',
    marginBottom: 12,
    textAlign: 'center',
  },
  hintCard: {
    marginBottom: 12,
    backgroundColor: '#fff',
    borderRadius: 8,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#1976d2',
  },
  question: {
    color: '#1976d2',
    marginBottom: 4,
    fontWeight: 'bold',
  },
  questionText: {
    color: '#424242',
    marginBottom: 8,
    paddingLeft: 8,
  },
  hintLabel: {
    color: '#2e7d32',
    marginBottom: 4,
    fontWeight: 'bold',
  },
  answer: {
    color: '#2e7d32',
    fontStyle: 'italic',
    paddingLeft: 8,
    borderLeftWidth: 2,
    borderLeftColor: '#2e7d32',
  },
  hintDivider: {
    height: 1,
    backgroundColor: '#e0e0e0',
    marginVertical: 8,
  },
  inputCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    elevation: 3,
    marginBottom: 16,
  },
  inputSection: {
    gap: 8,
  },
  guessSection: {
    marginTop: 24,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  input: {
    marginBottom: 8,
    backgroundColor: '#fff',
  },
  button: {
    marginBottom: 16,
  },
  scoreCard: {
    marginTop: 16,
    backgroundColor: '#e3f2fd',
  },
  score: {
    textAlign: 'center',
    color: '#1976d2',
  },
  hintCountCard: {
    marginBottom: 16,
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
    elevation: 4,
  },
  hintCount: {
    textAlign: 'center',
    color: '#1976d2',
    fontWeight: 'bold',
  },
  hintInfo: {
    textAlign: 'center',
    color: '#757575',
    marginTop: 4,
  },
}); 