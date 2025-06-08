import React from 'react';
import { View, StyleSheet, Share } from 'react-native';
import { Button, Text, Card, useTheme } from 'react-native-paper';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Result'>;

export default function ResultScreen({ route, navigation }: Props) {
  const theme = useTheme();
  const { word, score, questionsCount, timeTaken } = route.params;

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const shareResult = async () => {
    try {
      const message = `I just played Word Guess Game!\n\n` +
        `Word: ${word}\n` +
        `Questions Asked: ${questionsCount}\n` +
        `Time: ${formatTime(timeTaken)}\n` +
        (score > 0 ? `Score: ${score}\n` : '') +
        `\nCan you beat my score? Play now!`;

      await Share.share({
        message,
        title: 'Word Guess Game Results',
      });
    } catch (error) {
      console.error('Error sharing result:', error);
    }
  };

  return (
    <View style={styles.container}>
      <Card style={styles.resultCard}>
        <Card.Content>
          <Text variant="headlineLarge" style={[styles.title, { color: theme.colors.primary }]}>
            Congratulations!
          </Text>
          <Text variant="bodyLarge" style={styles.subtitle}>
            You've guessed the word correctly!
          </Text>

          <View style={styles.statsContainer}>
            <Card style={styles.statCard}>
              <Card.Content>
                <Text variant="headlineMedium" style={styles.statValue}>
                  {word}
                </Text>
                <Text variant="bodyMedium" style={styles.statLabel}>
                  Word
                </Text>
              </Card.Content>
            </Card>

            <Card style={styles.statCard}>
              <Card.Content>
                <Text variant="headlineMedium" style={styles.statValue}>
                  {questionsCount}
                </Text>
                <Text variant="bodyMedium" style={styles.statLabel}>
                  Questions
                </Text>
              </Card.Content>
            </Card>

            <Card style={styles.statCard}>
              <Card.Content>
                <Text variant="headlineMedium" style={styles.statValue}>
                  {formatTime(timeTaken)}
                </Text>
                <Text variant="bodyMedium" style={styles.statLabel}>
                  Time
                </Text>
              </Card.Content>
            </Card>

            {score > 0 && (
              <Card style={styles.statCard}>
                <Card.Content>
                  <Text variant="headlineMedium" style={styles.statValue}>
                    {score}
                  </Text>
                  <Text variant="bodyMedium" style={styles.statLabel}>
                    Score
                  </Text>
                </Card.Content>
              </Card>
            )}
          </View>
        </Card.Content>
      </Card>

      <View style={styles.buttonContainer}>
        <Button
          mode="contained"
          onPress={shareResult}
          style={[styles.button, { backgroundColor: theme.colors.primary }]}
          icon="share"
        >
          Share Result
        </Button>

        <Button
          mode="contained"
          onPress={() => navigation.navigate('Home')}
          style={[styles.button, { backgroundColor: theme.colors.secondary }]}
          icon="refresh"
        >
          Play Again
        </Button>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#B5E3FF',
  },
  resultCard: {
    marginBottom: 24,
    backgroundColor: '#fff',
  },
  title: {
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    textAlign: 'center',
    color: '#757575',
    marginBottom: 24,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 16,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#f8f8f8',
  },
  statValue: {
    textAlign: 'center',
    marginBottom: 4,
  },
  statLabel: {
    textAlign: 'center',
    color: '#757575',
    textTransform: 'uppercase',
    fontSize: 12,
  },
  buttonContainer: {
    gap: 16,
  },
  button: {
    paddingVertical: 8,
  },
}); 