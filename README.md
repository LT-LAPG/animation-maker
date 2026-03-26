# animation-maker

A simple tool to generate animated frames via AI (or local fallback visuals) and save them as images + animation files.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Add your OpenAI key to run true AI generation:
   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

## Usage

```bash
python animation_maker.py --prompt "sunset city skyline" --frames 16 --outdir output --format gif
```

Use `--use-ai` to request OpenAI image generation; if unavailable, fallback frames are produced automatically.

## Output

- Frame files: `output/frame_000.png`, `output/frame_001.png`, ...
- Animation file: `output/animation.gif` (or `animation.mp4` when `--format mp4`)

