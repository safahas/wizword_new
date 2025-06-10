import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Button, Text, TextInput, SegmentedButtons, Card, useTheme } from 'react-native-paper';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList, Category, GameMode } from '../types/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

const categories: Category[] = [
  'general',
  'animals',
  'food',
  'places',
  'science',
  'tech',
  'music'
];

const wordLengths = [3, 4, 5, 6, 7, 8, 9, 10];

export default function HomeScreen({ navigation }: Props) {
  const theme = useTheme();
  const [wordLength, setWordLength] = useState(5);
  const [category, setCategory] = useState<Category>('general');
  const [mode, setMode] = useState<GameMode>('fun');
  const [nickname, setNickname] = useState('');

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.headerCard}>
        <Card.Content>
          <Text variant="headlineLarge" style={styles.title}>
            Word Guess Game
          </Text>
          <Text variant="bodyLarge" style={styles.subtitle}>
            Test your word-guessing skills!
          </Text>
        </Card.Content>
      </Card>

      <Card style={styles.section}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Word Length
          </Text>
          <SegmentedButtons
            value={String(wordLength)}
            onValueChange={value => setWordLength(Number(value))}
            buttons={wordLengths.map(num => ({
              value: String(num),
              label: String(num),
              style: styles.segmentButton
            }))}
          />
        </Card.Content>
      </Card>

      <Card style={styles.section}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Category
          </Text>
          <SegmentedButtons
            value={category}
            onValueChange={value => setCategory(value as Category)}
            buttons={categories.map(cat => ({
              value: cat,
              label: cat.charAt(0).toUpperCase() + cat.slice(1),
              style: styles.segmentButton
            }))}
          />
        </Card.Content>
      </Card>

      <Card style={styles.section}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Game Mode
          </Text>
          <SegmentedButtons
            value={mode}
            onValueChange={value => setMode(value as GameMode)}
            buttons={[
              { 
                value: 'fun',
                label: 'Fun Mode',
                style: [styles.segmentButton, { backgroundColor: mode === 'fun' ? theme.colors.primary : undefined }]
              },
              { 
                value: 'challenge',
                label: 'Challenge Mode',
                style: [styles.segmentButton, { backgroundColor: mode === 'challenge' ? theme.colors.primary : undefined }]
              }
            ]}
          />
          <Text variant="bodyMedium" style={styles.modeDescription}>
            {mode === 'fun' 
              ? 'Fun mode: No scoring, just enjoy guessing!'
              : 'Challenge mode: Score points based on your questions'}
          </Text>
        </Card.Content>
      </Card>

      <Card style={styles.section}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Player Info
          </Text>
          <TextInput
            label="Nickname (optional)"
            value={nickname}
            onChangeText={setNickname}
            style={styles.input}
            mode="outlined"
          />
        </Card.Content>
      </Card>

      <Button
        mode="contained"
        onPress={() => navigation.navigate('Game', {
          wordLength,
          category,
          mode,
          nickname
        })}
        style={styles.button}
        contentStyle={styles.buttonContent}
      >
        Start Game
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#B5E3FF',
  },
  headerCard: {
    marginBottom: 24,
    backgroundColor: '#fff',
  },
  title: {
    textAlign: 'center',
    color: '#1976d2',
    marginBottom: 8,
  },
  subtitle: {
    textAlign: 'center',
    color: '#757575',
  },
  section: {
    marginBottom: 16,
    backgroundColor: '#fff',
  },
  sectionTitle: {
    marginBottom: 16,
    color: '#1976d2',
  },
  segmentButton: {
    flex: 1,
    paddingVertical: 8,
  },
  modeDescription: {
    marginTop: 8,
    color: '#757575',
    fontStyle: 'italic',
  },
  input: {
    marginTop: 8,
  },
  button: {
    marginVertical: 24,
  },
  buttonContent: {
    paddingVertical: 8,
  },
}); 