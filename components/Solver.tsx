'use client';

import React, { useState, useEffect, useRef } from 'react';
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
  difficulty?: string;  // yellow, green, blue, purple
}

interface SolverProps {
  words: string[];  // The 16 words from PuzzleFetcher
  puzzleId: number;
  puzzleDate: string;
  onPredictionsChange?: (predictions: Prediction[]) => void;  // Optional callback to notify parent
}

export default function Solver({ words, puzzleId, puzzleDate, onPredictionsChange }: SolverProps) {
  const [topSolution, setTopSolution] = useState<Prediction[]>([]);  // Guaranteed 4 groups
  const [allPredictions, setAllPredictions] = useState<Prediction[]>([]);  // All predictions
  const [excludedPredictions, setExcludedPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [useLLM, setUseLLM] = useState<boolean>(false);
  const [solveTime, setSolveTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showExcluded, setShowExcluded] = useState<boolean>(false);
  const [allWordsCovered, setAllWordsCovered] = useState<boolean>(false);
  
  // Track previous puzzle ID to detect when puzzle changes
  const prevPuzzleIdRef = useRef<number | null>(null);
  
  // Reset solver state when puzzle changes
  useEffect(() => {
    if (prevPuzzleIdRef.current !== null && prevPuzzleIdRef.current !== puzzleId) {
      // Puzzle changed - reset all state
      console.log(`Puzzle changed from ${prevPuzzleIdRef.current} to ${puzzleId}, resetting solver state`);
      setTopSolution([]);
      setAllPredictions([]);
      setExcludedPredictions([]);
      setSolveTime(null);
      setError(null);
      setShowExcluded(false);
      setAllWordsCovered(false);
      
      // Notify parent that predictions are cleared
      if (onPredictionsChange) {
        onPredictionsChange([]);
      }
    }
    prevPuzzleIdRef.current = puzzleId;
  }, [puzzleId, onPredictionsChange]);

  const solvePuzzle = async () => {
    if (!words || words.length !== 16) {
      const errorMsg = `Invalid words: Expected 16 words, got ${words?.length || 0}. Words: ${words?.join(', ') || 'none'}`;
      console.error('Solver error:', errorMsg);
      setError(errorMsg);
      toast.error('Invalid input', {
        description: errorMsg,
      });
      return;
    }
    
    // Debug: Log the words being sent
    console.log('Solving puzzle with words:', words);
    console.log('Puzzle ID:', puzzleId);

    setLoading(true);
    setError(null);
    
    // Show loading toast
    const loadingToastId = toast.loading('Solving puzzle...', {
      description: useLLM ? 'Using embeddings + GPT-4' : 'Using embeddings',
    });

    try {
      // Collect exclude_words from excludedPredictions (flatten all words)
      const excludeWords = excludedPredictions.flatMap(pred => pred.words);

      // Debug: Log what we're sending
      console.log('Sending solve request:', {
        wordsCount: words.length,
        use_llm: useLLM,
        excludeWordsCount: excludeWords.length,
      });

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
      
      // Handle new response format with top_solution and all_predictions
      const topSolution = data.top_solution || data.predictions?.slice(0, 4) || [];
      const allPredictions = data.all_predictions || data.predictions || [];
      const allWordsCovered = data.all_words_covered !== undefined ? data.all_words_covered : false;
      
      setTopSolution(topSolution);
      setAllPredictions(allPredictions);
      setAllWordsCovered(allWordsCovered);
      setSolveTime(data.solve_time_ms || null);
      
      // Notify parent component of predictions change (use top solution)
      if (onPredictionsChange) {
        onPredictionsChange(topSolution);
      }
      
      // Show success toast
      if (allWordsCovered) {
        toast.success('Complete solution found!', {
          description: `Found 4 groups covering all 16 words in ${(data.solve_time_ms / 1000).toFixed(1)}s`,
        });
      } else {
        toast.success('Solution found!', {
          description: `Found ${topSolution.length} groups in ${(data.solve_time_ms / 1000).toFixed(1)}s`,
        });
      }
    } catch (err) {
      // Dismiss loading toast
      toast.dismiss(loadingToastId);
      
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      setTopSolution([]);
      setAllPredictions([]);
      setAllWordsCovered(false);
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
    
    // Remove from top solution
    const updatedTopSolution = topSolution.filter(pred => {
      const predWords = pred.words.map(w => w.toUpperCase()).sort().join(',');
      const excludedWords = prediction.words.map(w => w.toUpperCase()).sort().join(',');
      return predWords !== excludedWords;
    });
    
    // Remove from all predictions
    const updatedAllPredictions = allPredictions.filter(pred => {
      const predWords = pred.words.map(w => w.toUpperCase()).sort().join(',');
      const excludedWords = prediction.words.map(w => w.toUpperCase()).sort().join(',');
      return predWords !== excludedWords;
    });
    
    setTopSolution(updatedTopSolution);
    setAllPredictions(updatedAllPredictions);
    
    // Notify parent of updated predictions
    if (onPredictionsChange) {
      onPredictionsChange(updatedTopSolution);
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

      {/* Top Solution Section */}
      {topSolution.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-gray-800">
                Recommended Solution
              </h2>
              {allWordsCovered && (
                <span className="bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded-full">
                  ✓ Uses all 16 words
                </span>
              )}
            </div>
            <span className="bg-green-100 text-green-800 text-sm font-medium px-3 py-1 rounded-full">
              {topSolution.length} groups
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topSolution.map((prediction, index) => {
              const { percentage, bgColor, label } = getConfidenceBadge(prediction.confidence);
              
              return (
                <div
                  key={index}
                  className={clsx(
                    'bg-white rounded-lg shadow-sm p-4',
                    'relative transition-all duration-200',
                    'hover:scale-[1.02] hover:shadow-md',
                    // Green border for top solution
                    'border-2 border-green-500'
                  )}
                >
                  {/* Recommended Badge */}
                  <div className="absolute top-2 left-2 bg-green-600 text-white text-[10px] font-semibold px-2 py-0.5 rounded">
                    Recommended
                  </div>
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
                      <div className="flex items-center gap-2">
                        <h4 className="text-lg font-bold text-gray-900">
                          {prediction.category}
                        </h4>
                        {prediction.difficulty && (
                          <span className={clsx(
                            'text-xs font-semibold px-2 py-0.5 rounded',
                            prediction.difficulty === 'yellow' && 'bg-yellow-100 text-yellow-800',
                            prediction.difficulty === 'green' && 'bg-green-100 text-green-800',
                            prediction.difficulty === 'blue' && 'bg-blue-100 text-blue-800',
                            prediction.difficulty === 'purple' && 'bg-purple-100 text-purple-800'
                          )}>
                            {prediction.difficulty.toUpperCase()}
                          </span>
                        )}
                      </div>
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
      {!loading && topSolution.length === 0 && !error && (
        <div className="text-center py-12 text-gray-500">
          <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Click "Solve Puzzle" to get AI-powered predictions</p>
        </div>
      )}
    </div>
  );
}

