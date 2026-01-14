import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

export async function GET(request: NextRequest) {
  try {
    // Get date parameter from query string (optional)
    const searchParams = request.nextUrl.searchParams;
    const date = searchParams.get('date') || null;

    // Call Python script
    const scriptPath = path.join(process.cwd(), 'python', 'scraper_api.py');
    const dateArg = date ? `"${date}"` : '';
    const command = `python3 -c "from python.scraper_api import fetch_puzzle; import json; print(json.dumps(fetch_puzzle(${dateArg})))"`;

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      maxBuffer: 1024 * 1024, // 1MB buffer
    });

    if (stderr && !stdout) {
      throw new Error(stderr);
    }

    // Parse JSON response from Python
    const puzzleData = JSON.parse(stdout.trim());

    // Return success response
    return NextResponse.json({
      success: true,
      data: {
        words: puzzleData.words,
        puzzle_id: puzzleData.puzzle_id,
        date: puzzleData.date,
      },
    });
  } catch (error) {
    // Return error response
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    
    return NextResponse.json(
      {
        success: false,
        error: errorMessage,
      },
      { status: 500 }
    );
  }
}

// Also support POST method
export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const date = body.date || null;

    // Call Python script
    const scriptPath = path.join(process.cwd(), 'python', 'scraper_api.py');
    const dateArg = date ? `"${date}"` : '';
    const command = `python3 -c "from python.scraper_api import fetch_puzzle; import json; print(json.dumps(fetch_puzzle(${dateArg})))"`;

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      maxBuffer: 1024 * 1024, // 1MB buffer
    });

    if (stderr && !stdout) {
      throw new Error(stderr);
    }

    // Parse JSON response from Python
    const puzzleData = JSON.parse(stdout.trim());

    // Return success response
    return NextResponse.json({
      success: true,
      data: {
        words: puzzleData.words,
        puzzle_id: puzzleData.puzzle_id,
        date: puzzleData.date,
      },
    });
  } catch (error) {
    // Return error response
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    
    return NextResponse.json(
      {
        success: false,
        error: errorMessage,
      },
      { status: 500 }
    );
  }
}

