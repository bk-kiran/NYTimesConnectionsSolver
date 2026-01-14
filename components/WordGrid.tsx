'use client';

import React from 'react';
import { clsx } from 'clsx';

interface Prediction {
  words: string[];
  confidence: number;
  category?: string | null;
  explanation?: string | null;
  method?: string;
  sources?: string[];
}

interface WordGridProps {
  words: string[];  // The 16 words
  predictions?: Prediction[];  // Current predictions to highlight
  highlightTop?: boolean;  // Whether to highlight top prediction
}

export default function WordGrid({ words, predictions, highlightTop = false }: WordGridProps) {
  // Helper function to check if word is in top prediction
  const isWordInTopPrediction = (word: string): boolean => {
    if (!highlightTop || !predictions || predictions.length === 0) {
      return false;
    }
    
    const topPrediction = predictions[0];
    if (!topPrediction || !topPrediction.words) {
      return false;
    }
    
    return topPrediction.words.some(
      predWord => predWord.toUpperCase() === word.toUpperCase()
    );
  };

  // Get highlight styling for a word
  const getHighlightClasses = (word: string): string => {
    if (!isWordInTopPrediction(word) || !predictions || predictions.length === 0) {
      return 'bg-white border-gray-300';
    }

    const confidence = predictions[0].confidence;
    
    if (confidence >= 0.7) {
      return 'bg-green-100 border-green-500 border-[3px]';
    } else if (confidence >= 0.4) {
      return 'bg-yellow-100 border-yellow-500 border-[3px]';
    } else {
      return 'bg-red-100 border-red-500 border-[3px]';
    }
  };

  // Get text size based on word length
  const getTextSizeClass = (word: string): string => {
    const length = word.length;
    if (length > 10) {
      return 'text-xs md:text-sm';
    } else if (length < 5) {
      return 'text-base md:text-lg';
    }
    return 'text-sm md:text-base';
  };

  // Check if top prediction is highlighted
  const hasTopPrediction = highlightTop && predictions && predictions.length > 0;

  return (
    <div className="w-full">
      {/* Top Pick Badge (if highlighting) */}
      {hasTopPrediction && (
        <div className="mb-3 text-center">
          <span className="inline-block bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
            Top Pick: {predictions[0].category || 'Prediction'} ({Math.round(predictions[0].confidence * 100)}%)
          </span>
        </div>
      )}

      {/* Word Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        {words.map((word, index) => {
          const isHighlighted = isWordInTopPrediction(word);
          const highlightClasses = getHighlightClasses(word);
          const textSizeClass = getTextSizeClass(word);
          
          return (
            <div
              key={`${word}-${index}`}
              className={clsx(
                'bg-white border-2 rounded-lg shadow-sm',
                'p-4 md:p-6',
                'text-center font-bold uppercase',
                'min-h-[80px] md:min-h-[100px]',
                'flex items-center justify-center',
                'transition-all duration-200',
                'hover:scale-105 hover:shadow-md',
                'relative',
                'text-gray-900', // Dark text for better visibility
                highlightClasses,
                textSizeClass,
                // Animation: fade in with stagger
                'animate-fade-in'
              )}
              style={{
                animationDelay: `${index * 50}ms`,
                animationFillMode: 'both',
              }}
              role="gridcell"
              aria-label={`Word: ${word}${isHighlighted ? ' (Top prediction)' : ''}`}
            >
              {word}
              
              {/* Top Pick Badge Overlay */}
              {isHighlighted && (
                <div className="absolute top-1 right-1">
                  <span className="bg-blue-600 text-white text-[10px] font-semibold px-1.5 py-0.5 rounded">
                    Top Pick
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

