import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

interface SolveRequest {
  words: string[];
  use_llm?: boolean;
  exclude_words?: string[];
}

interface Prediction {
  words: string[];
  confidence: number;
  category?: string | null;
  explanation?: string | null;
  method: string;
  sources?: string[];
  difficulty?: string | null;  // yellow, green, blue, purple
}

interface SolveResponse {
  success: boolean;
  top_solution?: Prediction[];  // Guaranteed 4 groups
  all_predictions?: Prediction[];  // All predictions for exploration
  solve_time_ms?: number;
  all_words_covered?: boolean;  // Whether solution uses all 16 words
  error?: string;
}

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body: SolveRequest = await request.json();
    
    const { words, use_llm = false, exclude_words = [] } = body;
    
    // Debug logging
    console.log('[API] Solve request received:', {
      wordsCount: words?.length,
      use_llm,
      excludeWordsCount: exclude_words?.length,
      hasApiKey: !!process.env.OPENAI_API_KEY,
    });
    
    // Validate input
    if (!words || !Array.isArray(words) || words.length !== 16) {
      return NextResponse.json(
        {
          success: false,
          error: 'Invalid input: words must be an array of exactly 16 words',
        },
        { status: 400 }
      );
    }
    
    // Get OpenAI API key from environment
    const apiKey = process.env.OPENAI_API_KEY || '';
    
    if (use_llm && !apiKey) {
      console.error('[API] GPT-4 requested but no API key found');
      return NextResponse.json(
        {
          success: false,
          error: 'OPENAI_API_KEY not found in environment variables',
        },
        { status: 400 }
      );
    }
    
    if (use_llm) {
      console.log('[API] GPT-4 mode enabled, API key present');
    } else {
      console.log('[API] Embeddings-only mode');
    }
    
    // Create a temporary Python script file to avoid escaping issues
    const tmpFile = path.join(os.tmpdir(), `solve_${Date.now()}.py`);
    
    // Prepare input data
    const inputData = {
      words,
      use_llm,
      exclude_words: exclude_words || [],
    };
    
    // Create Python script content
    const projectRoot = process.cwd().replace(/\\/g, '/').replace(/"/g, '\\"');
    const pythonScript = `#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

# Add project root to path (must be first)
project_root = Path("${projectRoot}")
project_root_str = str(project_root.resolve())
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# Change to project root directory
os.chdir(project_root_str)

# Now import should work
from python.solver_hybrid import solve_puzzle

# Read input from stdin
input_data = json.load(sys.stdin)
words = input_data['words']
use_llm = input_data.get('use_llm', False)
exclude_words = input_data.get('exclude_words', [])
api_key = os.getenv('OPENAI_API_KEY', '')

# Debug logging (to stderr so it doesn't break JSON output)
import sys
print(f"DEBUG: use_llm={use_llm}, api_key_length={len(api_key) if api_key else 0}", file=sys.stderr)

# Solve the puzzle (print statements will go to stderr, JSON to stdout)
# We'll capture stderr separately to see debug info
result = solve_puzzle(words, use_llm=use_llm, api_key=api_key if use_llm else None)

# Filter out excluded words if provided
if exclude_words:
    exclude_set = set(w.upper() for w in exclude_words)
    filtered_predictions = []
    for pred in result['predictions']:
        pred_words_upper = set(w.upper() for w in pred['words'])
        if not pred_words_upper.intersection(exclude_set):
            filtered_predictions.append(pred)
    result['predictions'] = filtered_predictions

# Output ONLY JSON result (no other prints)
# Write directly to stdout to avoid any buffering issues
import sys
sys.stdout.write(json.dumps(result))
sys.stdout.write('\\n')
sys.stdout.flush()
`;
    
    // Write Python script to temp file
    fs.writeFileSync(tmpFile, pythonScript);
    
    // Execute Python script with timeout
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    const inputJson = JSON.stringify(inputData);
    
    // Set environment variables for Python
    const pythonPathEnv = `${process.cwd()}:${process.cwd()}/python:${process.env.PYTHONPATH || ''}`;
    const env = {
      ...process.env,
      OPENAI_API_KEY: apiKey,
      PYTHONPATH: pythonPathEnv,
    };
    
    try {
      // Execute Python script with stdin input
      const result = await new Promise<{ stdout: string; stderr: string }>((resolve, reject) => {
        const pythonProcess = spawn(pythonPath, [tmpFile], {
          cwd: process.cwd(),
          env: {
            ...env,
            PYTHONPATH: `${process.cwd()}:${process.cwd()}/python:${env.PYTHONPATH || ''}`,
          },
        });
        
        let stdout = '';
        let stderr = '';
        
        pythonProcess.stdout.on('data', (data) => {
          stdout += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
          const stderrData = data.toString();
          stderr += stderrData;
          // Log debug info to console (but don't include in error)
          if (stderrData.includes('DEBUG:') || stderrData.includes('Running LLM') || stderrData.includes('LLM solver') || stderrData.includes('use_llm=')) {
            console.log('[Python Debug]', stderrData.trim());
          }
        });
        
        // Set 60 second timeout (embeddings + LLM can take time)
        const timeoutId = setTimeout(() => {
          pythonProcess.kill();
          reject(new Error('Request timeout after 60 seconds'));
        }, 60000);
        
        pythonProcess.on('close', (code) => {
          clearTimeout(timeoutId);
          if (code !== 0 && !stdout) {
            reject(new Error(stderr || `Process exited with code ${code}`));
          } else {
            resolve({ stdout, stderr });
          }
        });
        
        pythonProcess.on('error', (error) => {
          clearTimeout(timeoutId);
          reject(error);
        });
        
        // Write input JSON to stdin
        pythonProcess.stdin.write(inputJson);
        pythonProcess.stdin.end();
      });
      
      const { stdout, stderr } = result;
      
      // Clean up temp file
      try {
        fs.unlinkSync(tmpFile);
      } catch (e) {
        // Ignore cleanup errors
      }
      
      if (stderr && !stdout) {
        throw new Error(stderr);
      }
      
      // Parse Python output - get the last line which should be JSON
      // (ignore any print statements from the solver)
      const lines = stdout.trim().split('\n');
      let jsonLine = lines[lines.length - 1];
      
      // If last line doesn't look like JSON, try to find JSON in the output
      if (!jsonLine.startsWith('{') && !jsonLine.startsWith('[')) {
        // Look for JSON in the output
        for (let i = lines.length - 1; i >= 0; i--) {
          if (lines[i].trim().startsWith('{') || lines[i].trim().startsWith('[')) {
            jsonLine = lines[i].trim();
            break;
          }
        }
      }
      
      // Parse Python output
      const solverResult = JSON.parse(jsonLine);
      
      // Validate top_solution
      const topSolution = solverResult.top_solution || solverResult.predictions?.slice(0, 4) || [];
      const allPredictions = solverResult.all_predictions || solverResult.predictions || [];
      const allWordsCovered = solverResult.all_words_covered !== undefined 
        ? solverResult.all_words_covered 
        : (topSolution.length === 4);
      
      // Validate that top solution has 4 groups
      if (topSolution.length !== 4) {
        console.warn(`Warning: Top solution has ${topSolution.length} groups, expected 4`);
      }
      
      // Format response
      const response: SolveResponse = {
        success: true,
        top_solution: topSolution.map((pred: any) => ({
          words: pred.words,
          confidence: pred.confidence,
          category: pred.category || null,
          explanation: pred.explanation || null,
          method: pred.method,
          sources: pred.sources || [pred.method],
          difficulty: pred.difficulty || null,
        })),
        all_predictions: allPredictions.map((pred: any) => ({
          words: pred.words,
          confidence: pred.confidence,
          category: pred.category || null,
          explanation: pred.explanation || null,
          method: pred.method,
          sources: pred.sources || [pred.method],
          difficulty: pred.difficulty || null,
        })),
        solve_time_ms: solverResult.solve_time_ms,
        all_words_covered: allWordsCovered,
      };
      
      return NextResponse.json(response);
      
    } catch (error: any) {
      // Handle timeout
      if (error.message?.includes('timeout')) {
        return NextResponse.json(
          {
            success: false,
            error: 'Solver timeout: Request took longer than 30 seconds',
          },
          { status: 504 }
        );
      }
      
      // Handle other execution errors
      const errorMessage = error.message || error.stderr || 'Unknown error occurred';
      
      return NextResponse.json(
        {
          success: false,
          error: `Solver error: ${errorMessage}`,
        },
        { status: 500 }
      );
    }
    
  } catch (error: any) {
    // Handle JSON parsing or other errors
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Invalid request format',
      },
      { status: 400 }
    );
  }
}

