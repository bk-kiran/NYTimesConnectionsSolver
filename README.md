# NYT Connections Solver

AI-powered solver for NYT Connections puzzles using semantic embeddings and GPT-4.

## Features

- 🧩 Fetch today's NYT Connections puzzle
- 🤖 AI-powered solving using:
  - Semantic similarity (embeddings) - Fast and free
  - GPT-4 - More accurate with reasoning
- 🎯 Visual word grid with prediction highlighting
- 📊 Confidence scores and explanations
- 🚫 Exclude incorrect predictions
- 🔄 Re-solve with exclusions

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- OpenAI API key (optional, for GPT-4 solver)

## Setup Instructions

### 1. Install Node.js Dependencies

```bash
npm install
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** The first time you run the embeddings solver, it will download the `all-mpnet-base-v2` model (~420MB). This is a one-time download.

### 3. Configure Environment Variables

Create a `.env.local` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

**Note:** The OpenAI API key is only required if you want to use the GPT-4 solver. The embeddings solver works without it.

### 4. Start the Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Usage

1. **Fetch Puzzle**: Click "Fetch Today's Puzzle" to load today's NYT Connections puzzle
2. **View Words**: The 16 words will be displayed in a 4x4 grid
3. **Solve**: Click "Solve Puzzle" to get AI predictions
   - Toggle "Use GPT-4" for more accurate results (requires API key)
4. **Review Predictions**: 
   - Top prediction is highlighted in the word grid
   - View all predictions with confidence scores
   - Exclude incorrect predictions
5. **Re-solve**: Click "Re-solve Without Excluded" to get new predictions

## Project Structure

```
/
├── app/
│   ├── api/
│   │   ├── fetch-puzzle/    # API route to fetch puzzle
│   │   └── solve/            # API route to solve puzzle
│   ├── page.tsx              # Main application page
│   └── layout.tsx            # Root layout with Toaster
├── components/
│   ├── PuzzleFetcher.tsx    # Component to fetch puzzle
│   ├── WordGrid.tsx         # Component to display words
│   ├── Solver.tsx           # Component to solve puzzle
│   ├── LoadingSkeletons.tsx # Loading placeholders
│   └── Toaster.tsx          # Toast notifications
└── python/
    ├── scraper_api.py        # Fetch puzzle from NYT API
    ├── solver_embeddings.py  # Embeddings-based solver
    ├── solver_llm.py         # GPT-4 solver
    └── solver_hybrid.py      # Combined solver
```

## Troubleshooting

### Python Script Not Found
If you get "Python script not found" errors:
- Ensure Python 3 is installed: `python3 --version`
- Ensure all Python dependencies are installed: `pip install -r requirements.txt`

### OpenAI API Errors
If GPT-4 solver fails:
- Check your API key in `.env.local`
- Ensure you have credits in your OpenAI account
- Check rate limits

### Model Download Issues
If the embeddings model fails to download:
- Check your internet connection
- The model is downloaded to `~/.cache/huggingface/` on first use
- You can manually download it if needed

## Development

### Run in Development Mode
```bash
npm run dev
```

### Build for Production
```bash
npm run build
npm start
```

### Lint Code
```bash
npm run lint
```

## License

MIT
