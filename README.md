# NYT Connections Solver

**AI-powered puzzle solver for the New York Times Connections game using semantic embeddings and GPT-4 reasoning.**

## Overview

The NYT Connections Solver is a web application that helps players solve the daily New York Times Connections puzzle by leveraging artificial intelligence. The puzzle consists of 16 words that must be grouped into 4 categories of 4 words each, with categories ranging from straightforward (Yellow) to extremely tricky (Purple).

This project combines two AI approaches:
- **Semantic Embeddings**: Fast, similarity-based grouping using sentence transformers
- **GPT-4 Reasoning**: Advanced language model analysis with chain-of-thought prompting

The solver fetches today's puzzle from the NYT API, displays the words in an interactive grid, and provides AI-powered predictions with confidence scores, category suggestions, and explanations.

**Target Users**: Puzzle enthusiasts, developers interested in AI/NLP applications, and anyone who wants to understand how different AI approaches can solve word grouping challenges.

## Key Features

- **Puzzle Fetching**: Automatically retrieves today's NYT Connections puzzle (or any date) from the official API
- **Dual AI Solving Modes**:
  - **Embeddings-Only**: Fast semantic similarity analysis using sentence-transformers (completes in seconds)
  - **Hybrid Mode**: Combines embeddings with GPT-4 for more accurate, reasoning-based solutions
- **Guaranteed 4-Group Solutions**: The solver always returns exactly 4 groups that use all 16 words, ensuring complete puzzle coverage
- **Confidence Scoring**: Each prediction includes a confidence score (0-100%) indicating how certain the AI is about the grouping
- **Category Predictions**: GPT-4 mode provides category names and explanations for each group
- **Wordplay Detection**: Automatically detects tricky patterns like name combinations, fill-in-blank patterns, and compound words
- **Interactive UI**: 
  - Visual word grid with highlighted top predictions
  - Toggle between embeddings-only and GPT-4 modes
  - Exclude incorrect predictions to refine results
  - View alternative predictions beyond the top solution
- **Real-time Feedback**: Toast notifications for loading states, errors, and success messages

## Architecture & Tech Stack

The application uses a **hybrid architecture** combining a Next.js frontend with Python backend services:

```
User Browser
    ↓
Next.js Frontend (React + TypeScript)
    ↓
Next.js API Routes (/api/fetch-puzzle, /api/solve)
    ↓
Python Scripts (child_process execution)
    ↓
AI Models (sentence-transformers, OpenAI GPT-4)
```

### Frontend Technologies

- **Next.js 14** (App Router): React framework for server-side rendering and API routes
- **TypeScript**: Type-safe JavaScript for better code quality
- **TailwindCSS**: Utility-first CSS framework for responsive, modern UI
- **React Hooks**: State management with `useState`, `useEffect`, and `useRef`
- **Radix UI**: Accessible component primitives (Dialog, Switch)
- **Lucide React**: Icon library for UI elements
- **Sonner**: Toast notification system for user feedback

### Backend Technologies

- **Python 3**: Core solving logic and AI model integration
- **sentence-transformers**: Semantic embeddings using `all-mpnet-base-v2` model
- **OpenAI API**: GPT-4 Turbo for advanced reasoning and category prediction
- **NumPy & scikit-learn**: Vector operations and similarity calculations
- **requests**: HTTP client for fetching puzzle data from NYT API

### Key Python Modules

- `scraper_api.py`: Fetches puzzle data from NYT Connections API
- `solver_embeddings.py`: Semantic similarity-based grouping
- `solver_llm.py`: GPT-4-based reasoning with chain-of-thought prompting
- `solver_hybrid.py`: Combines both approaches with intelligent merging and ranking
- `wordplay_detector.py`: Detects name combinations, fill-in-blank patterns, compounds
- `word_analyzer.py`: Universal word analysis (properties, patterns, definitions)
- `group_validator.py`: Validates group coherence and exclusivity
- `constraint_solver.py`: Ensures valid 4-group solutions covering all 16 words
- `difficulty_predictor.py`: Predicts category difficulty (Yellow/Green/Blue/Purple)

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm (or yarn)
- **Python** 3.8+ with pip
- **OpenAI API Key** (optional, required for GPT-4 mode)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd nytconnectionssolver
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   
   Create a `.env.local` file in the project root:
   ```env
   OPENAI_API_KEY=sk-your-api-key-here
   ```
   
   **Note**: The OpenAI API key is only required if you want to use GPT-4 mode. The embeddings-only mode works without it.

5. **Run the development server**:
   ```bash
   npm run dev
   ```

6. **Open your browser**:
   
   Navigate to `http://localhost:3000`

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | No* | OpenAI API key for GPT-4 mode | `sk-proj-...` |

*Required only if you want to use GPT-4 mode. Embeddings-only mode works without it.

### Building for Production

```bash
# Build the Next.js application
npm run build

# Start the production server
npm start
```

## Usage

### Basic Workflow

1. **Fetch Today's Puzzle**:
   - Click the "Fetch Today's Puzzle" button
   - The app retrieves the puzzle from the NYT API and displays the 16 words in a 4×4 grid

2. **View the Words**:
   - The word grid shows all 16 words with hover effects
   - Words are randomly shuffled (not grouped by answer) to maintain puzzle integrity

3. **Solve the Puzzle**:
   - **Embeddings-Only Mode** (default):
     - Click "Solve Puzzle" to get fast semantic similarity-based predictions
     - Results appear in seconds with confidence scores
   - **GPT-4 Mode** (toggle on):
     - Enable the "Use GPT-4" toggle
     - Click "Solve Puzzle" to get reasoning-based predictions with category names and explanations
     - Takes longer (30-120 seconds) but provides more accurate results

4. **Review Predictions**:
   - **Top Solution**: 4 guaranteed groups that use all 16 words (marked with green border and "Recommended" badge)
   - **Alternative Predictions**: Additional possible groupings for exploration
   - Each prediction shows:
     - Confidence score (percentage)
     - Words in the group
     - Category name (GPT-4 mode only)
     - Explanation (GPT-4 mode only)
     - Methods used (embeddings, llm, hybrid, wordplay)

5. **Refine Results**:
   - Click "× Exclude" on incorrect predictions
   - Click "Solve Again" to get new predictions that avoid excluded words
   - The solver will find different groups on subsequent solves

### API Usage

#### Fetch Puzzle

```bash
# GET request
curl http://localhost:3000/api/fetch-puzzle

# With specific date (optional)
curl http://localhost:3000/api/fetch-puzzle?date=2026-01-14
```

**Response**:
```json
{
  "success": true,
  "data": {
    "words": ["WORD1", "WORD2", ..., "WORD16"],
    "puzzle_id": 1011,
    "date": "2026-01-14"
  }
}
```

#### Solve Puzzle

```bash
# POST request
curl -X POST http://localhost:3000/api/solve \
  -H "Content-Type: application/json" \
  -d '{
    "words": ["WORD1", "WORD2", ..., "WORD16"],
    "use_llm": true,
    "exclude_words": []
  }'
```

**Response**:
```json
{
  "success": true,
  "top_solution": [
    {
      "words": ["WORD1", "WORD2", "WORD3", "WORD4"],
      "confidence": 0.85,
      "category": "Category Name",
      "explanation": "Why these words connect",
      "method": "hybrid",
      "sources": ["embeddings", "llm"],
      "difficulty": "yellow"
    },
    ...
  ],
  "all_predictions": [...],
  "solve_time_ms": 2340,
  "all_words_covered": true
}
```

## Project Structure

```
nytconnectionssolver/
├── app/                          # Next.js App Router
│   ├── api/                      # API routes
│   │   ├── fetch-puzzle/         # Puzzle fetching endpoint
│   │   │   └── route.ts
│   │   └── solve/                # Puzzle solving endpoint
│   │       └── route.ts
│   ├── layout.tsx                # Root layout with Toaster
│   ├── page.tsx                  # Main application page
│   └── globals.css               # Global styles and animations
│
├── components/                   # React components
│   ├── PuzzleFetcher.tsx         # Fetches puzzle from API
│   ├── WordGrid.tsx              # Displays 16 words in 4×4 grid
│   ├── Solver.tsx                # Main solving interface with predictions
│   ├── LoadingSkeletons.tsx      # Loading placeholders
│   └── Toaster.tsx               # Toast notification wrapper
│
├── python/                       # Python solving logic
│   ├── scraper_api.py            # Fetches puzzle from NYT API
│   ├── solver_embeddings.py      # Semantic similarity solver
│   ├── solver_llm.py             # GPT-4 reasoning solver
│   ├── solver_hybrid.py          # Combines both approaches
│   ├── wordplay_detector.py      # Detects wordplay patterns
│   ├── word_analyzer.py          # Universal word analysis
│   ├── group_validator.py        # Validates group coherence
│   ├── constraint_solver.py      # Ensures valid 4-group solutions
│   ├── difficulty_predictor.py  # Predicts category difficulty
│   └── word_conflict_resolver.py # Resolves word assignment conflicts
│
├── lib/                          # Shared utilities (currently empty)
│
├── package.json                  # Node.js dependencies and scripts
├── requirements.txt              # Python dependencies
├── tsconfig.json                 # TypeScript configuration
├── tailwind.config.ts            # TailwindCSS configuration
├── next.config.mjs               # Next.js configuration
└── README.md                     # This file
```

## Data & Models

### Puzzle Data Structure

```typescript
interface PuzzleData {
  words: string[];        // 16 shuffled words
  puzzle_id: number;      // Unique puzzle identifier
  date: string;           // YYYY-MM-DD format
}
```

### Prediction Structure

```typescript
interface Prediction {
  words: string[];                    // 4 words in the group
  confidence: number;                 // 0.0 to 1.0
  category?: string | null;           // Category name (GPT-4 only)
  explanation?: string | null;        // Why words connect (GPT-4 only)
  method: string;                     // "embeddings" | "llm" | "hybrid" | "wordplay"
  sources?: string[];                  // ["embeddings", "llm"]
  difficulty?: string | null;          // "yellow" | "green" | "blue" | "purple"
}
```

### Solution Structure

```typescript
interface SolveResponse {
  success: boolean;
  top_solution?: Prediction[];        // Exactly 4 groups
  all_predictions?: Prediction[];     // Additional alternatives
  solve_time_ms?: number;
  all_words_covered?: boolean;        // Whether all 16 words are used
  error?: string;
}
```

## AI / ML Details

### Semantic Embeddings Approach

**Model**: `all-mpnet-base-v2` (sentence-transformers)

**Process**:
1. Generate 768-dimensional embeddings for all 16 words
2. Calculate pairwise cosine similarity for all possible 4-word combinations (C(16,4) = 1,820 combinations)
3. Score each combination by average pairwise similarity
4. Rank by confidence and return top 30 predictions

**Strengths**: Fast (completes in seconds), good at finding semantic relationships
**Limitations**: Struggles with wordplay, homophones, and abstract connections

### GPT-4 Reasoning Approach

**Model**: `gpt-4-turbo-preview` (OpenAI)

**Process**:
1. Construct detailed system prompt explaining Connections rules and category types
2. Include wordplay analysis findings (name combinations, fill-in-blank patterns)
3. Request chain-of-thought reasoning with JSON output
4. Parse response to extract 4 groups with categories and explanations
5. Validate that all 16 words are used exactly once

**Prompt Strategy**:
- **System Prompt**: Explains puzzle rules, category difficulty levels (Yellow/Green/Blue/Purple), and validation requirements
- **User Prompt**: Lists all 16 words, includes wordplay findings, requests step-by-step reasoning
- **Temperature**: 0.4 (balanced between creativity and consistency)
- **Response Format**: JSON with groups, categories, explanations, and validation checklist

**Strengths**: Excellent at wordplay, abstract connections, and providing explanations
**Limitations**: Slower (30-120 seconds), requires API key, can be inconsistent

### Hybrid Merging Strategy

The `solver_hybrid.py` module intelligently combines both approaches:

1. **Wordplay Detection**: Analyzes all words for patterns (name combinations, fill-in-blank, compounds)
2. **Embeddings Solver**: Always runs (fast baseline)
3. **LLM Solver**: Runs if `use_llm=True` (optional, slower but more accurate)
4. **Merging Logic**:
   - Groups found in both methods: Boost confidence to 0.95+
   - LLM-only groups: Weight 0.5-0.6
   - Embeddings-only groups: Weight 0.4
   - Wordplay matches: Additional 0.1-0.15 boost
5. **Constraint Solving**: Uses greedy algorithm to find 4 non-overlapping groups covering all 16 words
6. **Ranking**: Sorts by final confidence, applies overlap penalties

### Wordplay Detection

The solver detects several tricky patterns:

- **Name Combinations**: Words that can be split into two names (e.g., "JACKAL" = "JACK" + "AL")
- **Fill-in-Blank**: Words sharing a pattern like "___ ball" or "fire ___"
- **Compound Words**: Words that combine with the same word (e.g., "FIREWORK", "HOMEWORK", "TEAMWORK")
- **Homophones**: Words that sound alike but have different meanings

These patterns are passed to GPT-4 to improve accuracy on Purple categories.

## Design & Trade-offs

### Architecture Decisions

- **Next.js API Routes + Python Scripts**: 
  - **Why**: Leverages Next.js for full-stack development while using Python's superior ML ecosystem
  - **Trade-off**: Requires `child_process` execution, slower than native Node.js but more flexible

- **Hybrid AI Approach**:
  - **Why**: Embeddings are fast but limited; GPT-4 is accurate but slow. Combining both provides speed and accuracy options
  - **Trade-off**: More complex codebase, but gives users choice between speed and quality

- **Greedy Constraint Solver**:
  - **Why**: Exhaustive search (trying all combinations) is too slow (C(30,4) = 27,405 combinations)
  - **Trade-off**: May not find optimal solution, but guarantees 4 groups in seconds vs. minutes

### Performance Optimizations

- **Model Caching**: Sentence-transformers model loaded once and cached globally
- **Limited Validation**: Skips expensive embedding-based validation for all predictions (only validates top candidates)
- **Early Exit**: Constraint solver stops when high-confidence solution found
- **Reduced Candidate Pool**: Limits constraint solver to top 12 predictions instead of all 30

### Known Limitations

- **GPT-4 Inconsistency**: Sometimes returns fewer than 4 groups (fallback creates missing groups with low confidence)
- **Timeout Risk**: GPT-4 mode can take 60-120 seconds; timeout set to 120 seconds
- **Wordplay Detection**: Limited to common patterns; may miss obscure wordplay
- **No Historical Learning**: Doesn't track which predictions were correct to improve over time

### Future Improvements

- **Caching**: Cache embeddings for common words to speed up repeated solves
- **Ensemble Models**: Try multiple embedding models and merge results
- **Better Wordplay**: Expand wordplay detection with more patterns and phonetic matching
- **User Feedback Loop**: Track which predictions users mark as correct/incorrect to improve ranking
- **Progressive Solving**: Allow users to lock in correct groups and solve remaining words

## Testing & Quality

### Linting

```bash
# Run ESLint
npm run lint
```

### Type Checking

TypeScript provides compile-time type checking. The project uses strict mode for maximum type safety.

### Manual Testing

The application is primarily tested manually through the UI:
1. Fetch a puzzle and verify words are displayed correctly
2. Test embeddings-only mode (should complete in seconds)
3. Test GPT-4 mode (requires API key, should complete in 30-120 seconds)
4. Verify that top solution always has exactly 4 groups
5. Test exclusion feature to ensure new predictions avoid excluded words

## Deployment

### Vercel (Recommended)

1. **Push to GitHub**:
   ```bash
   git push origin main
   ```

2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Add environment variable: `OPENAI_API_KEY`

3. **Deploy**:
   - Vercel automatically detects Next.js and deploys
   - Python scripts run via `child_process` (no separate Python server needed)

### Other Platforms

For other platforms (Netlify, Railway, etc.):

1. **Build the Next.js app**:
   ```bash
   npm run build
   ```

2. **Ensure Python 3.8+ is available** in the deployment environment

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**:
   - `OPENAI_API_KEY` (if using GPT-4 mode)

5. **Start the production server**:
   ```bash
   npm start
   ```

### Docker (Alternative)

A Dockerfile could be added to containerize both Node.js and Python, but this is not currently implemented.

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and test thoroughly
4. **Commit with clear messages**:
   ```bash
   git commit -m "Add feature: description"
   ```
5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request** with a clear description of changes

### Areas for Contribution

- Improve wordplay detection patterns
- Add more embedding models for ensemble approach
- Optimize constraint solver performance
- Add unit tests for Python modules
- Improve UI/UX with better animations or layouts
- Add puzzle history/archival features

## License

This project is provided as-is for educational and personal use. Please respect the New York Times' terms of service when using their puzzle data.

## Author & Contact

Built as a demonstration of combining semantic embeddings and large language models for puzzle solving.

For questions, issues, or contributions, please open an issue on the repository.

---

**Note**: This solver is designed to help understand and enjoy the puzzle, not to replace the challenge of solving it yourself. The best way to play Connections is to try solving it first, then use the solver to learn from your mistakes!
