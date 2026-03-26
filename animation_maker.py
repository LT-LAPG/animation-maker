#!/usr/bin/env python3
"""AI Animation Maker

Usage examples:
  python animation_maker.py --prompt "sunrise over mountains" --frames 12 --outdir output
"""

import argparse
import logging
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Pillow is required. Install with 'pip install pillow'.")

try:
    import imageio
except ImportError:
    raise SystemExit("imageio is required. Install with 'pip install imageio'.")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def create_fallback_frame(prompt: str, frame_idx: int, total_frames: int, size=(512, 512)) -> Image.Image:
    """Generate a synthetic frame when AI API is unavailable."""
    width, height = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)

    # animated gradient + shapes
    for y in range(height):
        r = int((y / height) * 255)
        g = int(((width - y) / width) * 255)
        b = int((frame_idx / max(1, total_frames - 1)) * 255)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    text = f"{prompt[:24]}...\nFrame {frame_idx + 1}/{total_frames}"
    font = ImageFont.load_default()

    # Calculate multiline text size manually for compatibility
    lines = text.splitlines()
    text_w = 0
    text_h = 0
    line_spacing = 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        text_w = max(text_w, line_width)
        text_h += line_height + line_spacing
    text_h -= line_spacing

    draw.rectangle([10, 10, 10 + text_w + 6, 10 + text_h + 6], fill=(0, 0, 0, 160))
    y = 13
    for line in lines:
        draw.text((13, y), line, fill=(255, 255, 255), font=font)
        y += draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + line_spacing

    return img


def generate_ai_frame(prompt: str, frame_idx: int, total_frames: int, size=(512, 512)) -> Image.Image:
    """Generate one frame using OpenAI Image API and return PIL Image."""
    if not OPENAI_AVAILABLE:
        raise RuntimeError("openai package not installed")

    if os.getenv("OPENAI_API_KEY") is None:
        raise RuntimeError("OPENAI_API_KEY not set")

    dynamic_prompt = f"{prompt}, animation frame {frame_idx + 1} of {total_frames}"
    result = openai.Image.create(
        prompt=dynamic_prompt,
        n=1,
        size=f"{size[0]}x{size[1]}",
        response_format="b64_json",
    )

    import base64
    from io import BytesIO

    image_b64 = result["data"][0]["b64_json"]
    image_bytes = base64.b64decode(image_b64)
    return Image.open(BytesIO(image_bytes)).convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Generator + Animation saver")
    parser.add_argument("--prompt", required=True, help="Text prompt for the animation")
    parser.add_argument("--frames", type=int, default=12, help="Number of frames")
    parser.add_argument("--width", type=int, default=512, help="Frame width")
    parser.add_argument("--height", type=int, default=512, help="Frame height")
    parser.add_argument("--outdir", default="output", help="Output directory")
    parser.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Animation format")
    parser.add_argument("--use-ai", action="store_true", help="Use OpenAI image generation (requires OPENAI_API_KEY + openai package)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip frame generation if file exists")

    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    frame_paths = []
    use_ai = args.use_ai and OPENAI_AVAILABLE

    if args.use_ai and not OPENAI_AVAILABLE:
        logging.warning("openai package is missing; falling back to built-in placeholder frames.")
        use_ai = False

    if args.use_ai and os.getenv("OPENAI_API_KEY") is None:
        logging.warning("OPENAI_API_KEY missing; falling back to built-in placeholder frames.")
        use_ai = False

    for i in range(args.frames):
        frame_file = outdir / f"frame_{i:03d}.png"
        frame_paths.append(frame_file)

        if args.skip_existing and frame_file.exists():
            continue

        if use_ai:
            try:
                frame = generate_ai_frame(args.prompt, i, args.frames, size=(args.width, args.height))
            except Exception as e:
                logging.warning("AI frame generation failed (%s); using fallback frame.", e)
                frame = create_fallback_frame(args.prompt, i, args.frames, size=(args.width, args.height))
        else:
            frame = create_fallback_frame(args.prompt, i, args.frames, size=(args.width, args.height))

        frame.save(frame_file)

    # create animation
    images = [imageio.imread(str(path)) for path in frame_paths]
    output_file = outdir / f"animation.{args.format}"
    if args.format == "gif":
        imageio.mimsave(str(output_file), images, fps=12)
    else:
        writer = imageio.get_writer(str(output_file), fps=12)
        for img in images:
            writer.append_data(img)
        writer.close()

    print(f"Saved {len(frame_paths)} frames in '{outdir}/' and animation '{output_file}'")


if __name__ == "__main__":
    main()
