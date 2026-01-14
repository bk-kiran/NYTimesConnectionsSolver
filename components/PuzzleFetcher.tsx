'use client';

import React, { useState } from 'react';
import { Download, Loader2, RefreshCw, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

interface PuzzleData {
  words: string[];
  puzzle_id: number;
  date: string;
}

interface PuzzleFetcherProps {
  onPuzzleFetched: (data: PuzzleData) => void;
}

export default function PuzzleFetcher({ onPuzzleFetched }: PuzzleFetcherProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [puzzleData, setPuzzleData] = useState<PuzzleData | null>(null);

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch (e) {
      return dateString;
    }
  };

  const fetchPuzzle = async () => {
    console.log('Fetch puzzle button clicked');
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/fetch-puzzle', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to fetch puzzle');
      }

      // Update state with puzzle data
      setPuzzleData(data.data);
      
      // Call the callback with the puzzle data
      onPuzzleFetched(data.data);
      
      // Show success toast
      toast.success('Puzzle fetched!', {
        description: `Puzzle #${data.data.puzzle_id} loaded with 16 words`,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      setPuzzleData(null);
      
      // Show error toast
      toast.error('Failed to fetch puzzle', {
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-md p-6 w-full max-w-2xl mx-auto">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <h2 className="text-xl font-semibold text-gray-800">NYT Connections Puzzle</h2>
          <button
            onClick={fetchPuzzle}
            disabled={loading}
            type="button"
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-75 disabled:cursor-not-allowed cursor-pointer relative z-10"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Loading...</span>
              </>
            ) : (
              <>
                <Download className="w-5 h-5" />
                <span>Fetch Today&apos;s Puzzle</span>
              </>
            )}
          </button>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="font-medium mb-1">Error</p>
                <p className="text-sm">{error}</p>
              </div>
              <button
                onClick={fetchPuzzle}
                disabled={loading}
                className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Success State / Already Fetched Message */}
        {puzzleData && !error && (
          <div className="bg-green-50 border border-green-200 text-green-800 p-4 rounded">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5" />
                  <p className="font-medium">
                    Puzzle #{puzzleData.puzzle_id} - {formatDate(puzzleData.date)}
                  </p>
                </div>
                <p className="text-sm">16 words loaded - Ready to solve!</p>
                <p className="text-xs text-green-700 mt-1 italic">
                  Puzzle already fetched. Click &quot;Fetch Today&apos;s Puzzle&quot; above to refresh.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State (when button is clicked) */}
        {loading && !puzzleData && (
          <div className="text-center py-4">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
            <p className="text-sm text-gray-600 mt-2">Fetching puzzle data...</p>
          </div>
        )}
      </div>
    </div>
  );
}

