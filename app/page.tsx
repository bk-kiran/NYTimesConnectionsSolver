'use client';

import React, { useState } from 'react';
import { Puzzle, Info } from 'lucide-react';
import PuzzleFetcher from '@/components/PuzzleFetcher';
import WordGrid from '@/components/WordGrid';
import Solver from '@/components/Solver';

interface PuzzleData {
  words: string[];
  puzzle_id: number;
  date: string;
}

interface Prediction {
  words: string[];
  confidence: number;
  category?: string | null;
  explanation?: string | null;
  method?: string;
  sources?: string[];
}

export default function Home() {
  const [puzzleData, setPuzzleData] = useState<PuzzleData | null>(null);
  const [predictions, setPredictions] = useState<Prediction[] | null>(null);

  const handlePuzzleFetched = (data: PuzzleData) => {
    setPuzzleData(data);
    setPredictions(null); // Reset predictions when new puzzle is loaded
  };

  const handlePredictionsChange = (newPredictions: Prediction[]) => {
    setPredictions(newPredictions);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      {/* Header Section */}
      <header className="bg-white shadow-lg rounded-lg mb-8 p-6 max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-2">
          <Puzzle className="w-8 h-8 md:w-10 md:h-10 text-blue-600" />
          <h1 className="text-3xl md:text-4xl font-bold text-blue-600">
            NYT Connections Solver
          </h1>
        </div>
        <p className="text-gray-600 text-lg mt-2">
          AI-powered puzzle solver using embeddings + GPT-4
        </p>
        <p className="text-gray-500 text-sm mt-4">
          Fetch today's NYT Connections puzzle, view the 16 words, and get AI-powered predictions
          to help you solve the puzzle. Use semantic similarity (embeddings) for fast results, or
          enable GPT-4 for more accurate, reasoning-based solutions.
        </p>
      </header>

      {/* Main Content Container */}
      <div className="max-w-6xl mx-auto space-y-8">
        {/* PuzzleFetcher Component */}
        <PuzzleFetcher onPuzzleFetched={handlePuzzleFetched} />

        {/* Conditional Rendering - Only if puzzleData exists */}
        {puzzleData ? (
          <>
            {/* Puzzle Info Card */}
            <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-blue-500">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-800 mb-1">
                    Puzzle #{puzzleData.puzzle_id}
                  </h3>
                  <p className="text-sm text-gray-600 mb-1">
                    Date: {formatDate(puzzleData.date)}
                  </p>
                  <p className="text-sm text-gray-600">
                    16 words ready to solve
                  </p>
                </div>
              </div>
            </div>

            {/* WordGrid Component */}
            <div className="my-8">
              <WordGrid
                words={puzzleData.words}
                predictions={predictions || undefined}
                highlightTop={true}
              />
            </div>

            {/* Solver Component */}
            <Solver
              words={puzzleData.words}
              puzzleId={puzzleData.puzzle_id}
              puzzleDate={puzzleData.date}
              onPredictionsChange={handlePredictionsChange}
            />
          </>
        ) : (
          /* Empty State */
          <div className="text-center py-20">
            <Puzzle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h2 className="text-2xl font-semibold text-gray-600 mb-2">Get Started</h2>
            <p className="text-gray-500">
              Click &apos;Fetch Today&apos;s Puzzle&apos; above to begin
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="mt-16 text-center text-sm text-gray-500">
        <p>
          Built with Next.js, OpenAI, and sentence-transformers
        </p>
      </footer>
    </div>
  );
}
