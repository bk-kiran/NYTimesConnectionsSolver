'use client';

import React from 'react';

// WordGridSkeleton - 4x4 grid of animated placeholder boxes
export function WordGridSkeleton() {
  return (
    <div className="w-full">
      {/* Top Pick Badge Skeleton */}
      <div className="mb-3 text-center">
        <div className="inline-block h-6 w-48 bg-gray-200 rounded-full animate-pulse mx-auto" />
      </div>

      {/* Word Grid Skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        {Array.from({ length: 16 }).map((_, index) => (
          <div
            key={index}
            className="bg-gray-200 border-2 border-gray-300 rounded-lg shadow-sm p-4 md:p-6 min-h-[80px] md:min-h-[100px] flex items-center justify-center animate-pulse"
          >
            <div className="h-4 w-16 bg-gray-300 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

// SolverSkeleton - Skeleton for solver section
export function SolverSkeleton() {
  return (
    <div className="bg-white rounded-lg border shadow-lg p-6 w-full max-w-6xl mx-auto">
      {/* Header Section Skeleton */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="h-8 w-32 bg-gray-200 rounded animate-pulse" />
          <div className="h-5 w-24 bg-gray-200 rounded animate-pulse" />
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          {/* Toggle Skeleton */}
          <div className="flex items-center gap-3">
            <div className="h-5 w-16 bg-gray-200 rounded animate-pulse" />
            <div className="w-11 h-6 bg-gray-200 rounded-full animate-pulse" />
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
          </div>

          {/* Button Skeleton */}
          <div className="h-12 w-40 bg-gray-200 rounded-lg animate-pulse" />
        </div>
      </div>

      {/* Prediction Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="bg-white border rounded-lg shadow-sm p-4 relative animate-pulse"
          >
            {/* Confidence Badge Skeleton */}
            <div className="absolute top-3 right-3 h-6 w-16 bg-gray-200 rounded" />

            {/* Category Skeleton */}
            <div className="h-6 w-32 bg-gray-200 rounded mb-3 pr-20" />

            {/* Words Grid Skeleton */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              {Array.from({ length: 4 }).map((_, wordIndex) => (
                <div
                  key={wordIndex}
                  className="h-10 bg-gray-200 rounded-md animate-pulse"
                />
              ))}
            </div>

            {/* Explanation Skeleton */}
            <div className="h-4 w-full bg-gray-200 rounded mb-2 animate-pulse" />
            <div className="h-4 w-3/4 bg-gray-200 rounded mb-3 animate-pulse" />

            {/* Methods Badge and Button Skeleton */}
            <div className="flex items-center justify-between mt-3 pt-3 border-t">
              <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-7 w-20 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// PuzzleFetcherSkeleton - Skeleton for fetcher card
export function PuzzleFetcherSkeleton() {
  return (
    <div className="bg-white rounded-lg border shadow-md p-6">
      <div className="flex flex-col items-center gap-4">
        {/* Button Skeleton */}
        <div className="h-12 w-48 bg-gray-200 rounded-lg animate-pulse" />

        {/* Success State Skeleton (if needed) */}
        <div className="w-full space-y-2">
          <div className="h-5 w-32 bg-gray-200 rounded animate-pulse mx-auto" />
          <div className="h-4 w-24 bg-gray-200 rounded animate-pulse mx-auto" />
        </div>
      </div>
    </div>
  );
}

