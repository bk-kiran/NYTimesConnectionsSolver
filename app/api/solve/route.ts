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
}

interface SolveResponse {
  success: boolean;
  predictions?: Prediction[];
  solve_time_ms?: number;
  error?: string;
}

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body: SolveRequest = await request.json();
    
    const { words, use_llm = false, exclude_words = [] } = body;
    
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
      return NextResponse.json(
        {
          success: false,
          error: 'OPENAI_API_KEY not found in environment variables',
        },
        { status: 400 }
      );
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

# Suppress print statements by redirecting stdout temporarily
import io
import contextlib

# Capture and suppress print output
f = io.StringIO()
with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
    # Solve the puzzle
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
          stderr += data.toString();
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
      
      // Format response
      const response: SolveResponse = {
        success: true,
        predictions: solverResult.predictions.map((pred: any) => ({
          words: pred.words,
          confidence: pred.confidence,
          category: pred.category || null,
          explanation: pred.explanation || null,
          method: pred.method,
          sources: pred.sources || [pred.method],
        })),
        solve_time_ms: solverResult.solve_time_ms,
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

