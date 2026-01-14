'use client';

import React, { useState } from 'react';
import { Sparkles, Loader2, X, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import * as Switch from '@radix-ui/react-switch';
import { clsx } from 'clsx';
import { toast } from 'sonner';

interface Prediction {
  words: string[];
  confidence: number;
  category?: string | null;
  explanation?: string | null;
  method?: string;
  sources?: string[];
}

interface SolverProps {
  words: string[];  // The 16 words from PuzzleFetcher
  puzzleId: number;
  puzzleDate: string;
  onPredictionsChange?: (predictions: Prediction[]) => void;  // Optional callback to notify parent
}

export default function Solver({ words, puzzleId, puzzleDate, onPredictionsChange }: SolverProps) {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [excludedPredictions, setExcludedPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [useLLM, setUseLLM] = useState<boolean>(false);
  const [solveTime, setSolveTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showExcluded, setShowExcluded] = useState<boolean>(false);

  const solvePuzzle = async () => {
    if (!words || words.length !== 16) {
      const errorMsg = 'Invalid words: Must have exactly 16 words';
      setError(errorMsg);
      toast.error('Invalid input', {
        description: errorMsg,
      });
      return;
    }

    setLoading(true);
    setError(null);
    
    // Show loading toast
    const loadingToastId = toast.loading('Solving puzzle...', {
      description: useLLM ? 'Using embeddings + GPT-4' : 'Using embeddings',
    });

    try {
      // Collect exclude_words from excludedPredictions (flatten all words)
      const excludeWords = excludedPredictions.flatMap(pred => pred.words);

      const response = await fetch('/api/solve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          words: words,
          use_llm: useLLM,
          exclude_words: excludeWords,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to solve puzzle');
      }

      // Dismiss loading toast
      toast.dismiss(loadingToastId);
      
      // Merge new predictions with existing ones (don't overwrite)
      // Only add predictions that don't overlap with existing predictions
      const newPredictions = data.predictions || [];
      const existingWords = new Set(
        predictions.flatMap(pred => pred.words.map(w => w.toUpperCase()))
      );
      
      // Filter out new predictions that overlap with existing ones
      const uniqueNewPredictions = newPredictions.filter(newPred => {
        const newWords = new Set(newPred.words.map(w => w.toUpperCase()));
        // Check if any word from new prediction is already in existing predictions
        return !Array.from(newWords).some(word => existingWords.has(word));
      });
      
      // Combine existing predictions with new unique ones
      const mergedPredictions = [...predictions, ...uniqueNewPredictions];
      
      setPredictions(mergedPredictions);
      setSolveTime(data.solve_time_ms || null);
      
      // Notify parent component of predictions change
      if (onPredictionsChange) {
        onPredictionsChange(mergedPredictions);
      }
      
      // Show success toast
      if (uniqueNewPredictions.length > 0) {
        toast.success('New predictions found!', {
          description: `Added ${uniqueNewPredictions.length} new group${uniqueNewPredictions.length > 1 ? 's' : ''} (${mergedPredictions.length} total) in ${(data.solve_time_ms / 1000).toFixed(1)}s`,
        });
      } else {
        toast.info('No new groups found', {
          description: `All predictions overlap with existing groups. Try excluding more words.`,
        });
      }
    } catch (err) {
      // Dismiss loading toast
      toast.dismiss(loadingToastId);
      
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      setPredictions([]);
      setSolveTime(null);
      
      // Notify parent that predictions are cleared
      if (onPredictionsChange) {
        onPredictionsChange([]);
      }
      
      // Show error toast
      toast.error('Failed to solve puzzle', {
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const excludePrediction = (prediction: Prediction) => {
    // Add to excluded
    setExcludedPredictions(prev => [...prev, prediction]);
    
    // Remove from predictions
    const updatedPredictions = predictions.filter(pred => {
      // Compare word arrays (order-independent)
      const predWords = pred.words.map(w => w.toUpperCase()).sort().join(',');
      const excludedWords = prediction.words.map(w => w.toUpperCase()).sort().join(',');
      return predWords !== excludedWords;
    });
    
    setPredictions(updatedPredictions);
    
    // Notify parent of updated predictions
    if (onPredictionsChange) {
      onPredictionsChange(updatedPredictions);
    }
  };

  const resolvePuzzle = () => {
    solvePuzzle();
  };

  const resetExclusions = () => {
    setExcludedPredictions([]);
  };

  const formatSolveTime = (ms: number): string => {
    if (ms < 1000) {
      return `${Math.round(ms)}ms`;
    }
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getConfidenceBadge = (confidence: number) => {
    const percentage = Math.round(confidence * 100);
    let bgColor = 'bg-red-100 text-red-800 border-red-200';
    let label = 'Low confidence';

    if (confidence >= 0.7) {
      bgColor = 'bg-green-100 text-green-800 border-green-200';
      label = 'High confidence';
    } else if (confidence >= 0.4) {
      bgColor = 'bg-yellow-100 text-yellow-800 border-yellow-200';
      label = 'Medium confidence';
    }

    return { percentage, bgColor, label };
  };

  const getMethodsLabel = (prediction: Prediction): string => {
    const methods = prediction.sources || [prediction.method || 'embeddings'];
    if (methods.includes('llm') && methods.includes('embeddings')) {
      return 'Embeddings + GPT-4';
    } else if (methods.includes('llm')) {
      return 'GPT-4';
    }
    return 'Embeddings only';
  };

  return (
    <div className="bg-white rounded-lg border shadow-lg p-6 w-full max-w-6xl mx-auto">
      {/* Header Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800">AI Solver</h2>
          {solveTime !== null && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>Solved in {formatSolveTime(solveTime)}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          {/* GPT-4 Toggle */}
          <div className="flex items-center gap-3">
            <label
              htmlFor="llm-toggle"
              className="text-sm font-medium text-gray-700 cursor-pointer"
            >
              Use GPT-4
            </label>
            <Switch.Root
              id="llm-toggle"
              checked={useLLM}
              onCheckedChange={setUseLLM}
              className={clsx(
                'w-11 h-6 rounded-full relative',
                'bg-gray-200 data-[state=checked]:bg-blue-600',
                'transition-colors duration-200',
                'outline-none cursor-pointer'
              )}
            >
              <Switch.Thumb
                className={clsx(
                  'block w-5 h-5 bg-white rounded-full',
                  'transition-transform duration-200',
                  'translate-x-0.5 data-[state=checked]:translate-x-[22px]',
                  'shadow-sm'
                )}
              />
            </Switch.Root>
            <span className="text-xs text-gray-500">
              {useLLM && '(requires API key)'}
            </span>
          </div>

          {/* Solve Button */}
          <button
            onClick={solvePuzzle}
            disabled={!words || words.length !== 16 || loading}
            className={clsx(
              'flex items-center gap-2',
              'bg-blue-600 hover:bg-blue-700',
              'text-white px-6 py-3 rounded-lg',
              'font-medium transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'disabled:hover:bg-blue-600'
            )}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Solving...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Solve Puzzle</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="font-medium mb-1">Error</p>
              <p className="text-sm">{error}</p>
            </div>
            <button
              onClick={solvePuzzle}
              disabled={loading}
              className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Results Section */}
      {predictions.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold text-gray-800">
              Top Predictions
            </h3>
            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
              {predictions.length}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {predictions.map((prediction, index) => {
              const { percentage, bgColor, label } = getConfidenceBadge(prediction.confidence);
              
              return (
                <div
                  key={index}
                  className={clsx(
                    'bg-white border rounded-lg shadow-sm p-4',
                    'relative transition-all duration-200',
                    'hover:scale-[1.02] hover:shadow-md'
                  )}
                >
                  {/* Confidence Badge */}
                  <div className={clsx(
                    'absolute top-3 right-3',
                    'px-2 py-1 rounded text-xs font-semibold border',
                    bgColor
                  )}>
                    {percentage}%
                  </div>

                  {/* Category - Only available when using GPT-4 */}
                  {prediction.category && (
                    <div className="mb-3 pr-20">
                      <h4 className="text-lg font-bold text-gray-900">
                        {prediction.category}
                      </h4>
                      {useLLM && (
                        <p className="text-xs text-blue-600 font-medium mt-1">
                          GPT-4 Category Prediction
                        </p>
                      )}
                    </div>
                  )}

                  {/* Words Grid */}
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {prediction.words.map((word, wordIndex) => (
                      <div
                        key={wordIndex}
                        className={clsx(
                          'bg-gray-100 text-gray-900',
                          'px-3 py-2 rounded-md',
                          'text-sm font-bold uppercase',
                          'text-center'
                        )}
                      >
                        {word}
                      </div>
                    ))}
                  </div>

                  {/* Explanation */}
                  {prediction.explanation && (
                    <p className="text-xs text-gray-600 mb-3">
                      {prediction.explanation}
                    </p>
                  )}

                  {/* Methods Badge */}
                  <div className="flex items-center justify-between mt-3 pt-3 border-t">
                    <span className="text-xs text-gray-500">
                      {getMethodsLabel(prediction)}
                    </span>
                    <button
                      onClick={() => excludePrediction(prediction)}
                      className={clsx(
                        'flex items-center gap-1',
                        'px-2 py-1 rounded text-xs',
                        'border border-gray-300 hover:bg-gray-50',
                        'text-gray-700 transition-colors'
                      )}
                    >
                      <X className="w-3 h-3" />
                      <span>Exclude</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Excluded Section */}
      {excludedPredictions.length > 0 && (
        <div className="border-t pt-6">
          <button
            onClick={() => setShowExcluded(!showExcluded)}
            className="flex items-center justify-between w-full mb-4 text-left"
          >
            <h3 className="text-lg font-semibold text-gray-800">
              Excluded Predictions ({excludedPredictions.length})
            </h3>
            {showExcluded ? (
              <ChevronUp className="w-5 h-5 text-gray-600" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-600" />
            )}
          </button>

          {showExcluded && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {excludedPredictions.map((prediction, index) => {
                  const { percentage, bgColor } = getConfidenceBadge(prediction.confidence);
                  
                  return (
                    <div
                      key={index}
                      className={clsx(
                        'bg-gray-50 border border-gray-200 rounded-lg shadow-sm p-4',
                        'opacity-60 relative'
                      )}
                    >
                      <div className={clsx(
                        'absolute top-3 right-3',
                        'px-2 py-1 rounded text-xs font-semibold border',
                        bgColor
                      )}>
                        {percentage}%
                      </div>

                      {prediction.category && (
                        <h4 className="text-lg font-bold text-gray-700 mb-3 pr-20">
                          {prediction.category}
                        </h4>
                      )}

                      <div className="grid grid-cols-2 gap-2">
                        {prediction.words.map((word, wordIndex) => (
                          <div
                            key={wordIndex}
                            className="bg-gray-200 text-gray-700 px-3 py-2 rounded-md text-sm font-bold uppercase text-center"
                          >
                            {word}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={resolvePuzzle}
                  disabled={loading}
                  className={clsx(
                    'px-4 py-2 bg-blue-600 hover:bg-blue-700',
                    'text-white rounded-lg text-sm font-medium',
                    'transition-colors disabled:opacity-50'
                  )}
                >
                  Re-solve Without Excluded
                </button>
                <button
                  onClick={resetExclusions}
                  className={clsx(
                    'px-4 py-2 bg-gray-200 hover:bg-gray-300',
                    'text-gray-800 rounded-lg text-sm font-medium',
                    'transition-colors'
                  )}
                >
                  Clear Exclusions
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && predictions.length === 0 && !error && (
        <div className="text-center py-12 text-gray-500">
          <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Click "Solve Puzzle" to get AI-powered predictions</p>
        </div>
      )}
    </div>
  );
}

