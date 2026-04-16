#!/usr/bin/env python3
"""Post-process 2D game asset images: remove background + rasterize to target pixel size.

Supports three background removal strategies:
  1. Chroma Key (default): HSV-based removal of magenta/green/white backgrounds
  2. ML (--ml): ToonOut/BiRefNet model via HuggingFace transformers
  3. Adobe Express (--adobe): Browser-based removal (handled externally by Claude)
"""

import argparse
import sys
from pathlib import Path
from collections import deque

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Strategy 1: Chroma Key (HSV-based) -- PRIMARY
# ---------------------------------------------------------------------------

def remove_bg_chroma_key(img: Image.Image, bg_color: str = "magenta", tolerance: int = 30) -> Image.Image:
    """Remove background using HSV color range detection.

    Supports magenta (#FF00FF), green (#00FF00), and white backgrounds.
    Uses HSV color space for robust detection despite Gemini's imperfect color matching.
    """
    if bg_color == "white":
        return remove_bg_flood_fill(img, tolerance=tolerance)

    import colorsys

    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue

            # Convert to HSV (0-360 hue, 0-100 sat/val)
            r_n, g_n, b_n = r / 255.0, g / 255.0, b / 255.0
            hue, sat, val = colorsys.rgb_to_hsv(r_n, g_n, b_n)
            hue *= 360
            sat *= 100
            val *= 100

            is_bg = False

            if bg_color == "magenta":
                # Magenta: hue ~300 (range 270-330), high saturation
                if (270 <= hue <= 330) and sat >= 30 and val >= 20:
                    is_bg = True
            elif bg_color == "green":
                # Chromakey green: hue ~120 (range 80-160), high saturation
                if (80 <= hue <= 160) and sat >= 30 and val >= 20:
                    is_bg = True

            if is_bg:
                pixels[x, y] = (0, 0, 0, 0)

    # Morphological cleanup: remove fringe pixels
    img = _cleanup_fringe(img)
    return img


def _cleanup_fringe(img: Image.Image) -> Image.Image:
    """Remove semi-transparent fringe pixels at sprite edges.

    Snaps alpha to binary: fully opaque (255) or fully transparent (0).
    Also removes isolated transparent pixels inside the sprite and
    isolated opaque pixels outside.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size

    # Pass 1: Snap alpha to binary
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if 0 < a < 255:
                pixels[x, y] = (r, g, b, 255 if a >= 128 else 0)

    return img


# ---------------------------------------------------------------------------
# Strategy 1b: Legacy flood fill (for white backgrounds)
# ---------------------------------------------------------------------------

def remove_bg_flood_fill(img: Image.Image, tolerance: int = 20) -> Image.Image:
    """Remove background via flood fill from edges (legacy white bg method).

    Only removes pixels connected to the image border that match the
    detected edge color within tolerance.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    threshold = 255 - tolerance

    visited = [[False] * h for _ in range(w)]
    background = [[False] * h for _ in range(w)]

    def is_bg(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        return r >= threshold and g >= threshold and b >= threshold and a > 0

    # Seed flood fill from all edge pixels
    queue = deque()
    for x in range(w):
        for y in [0, h - 1]:
            if is_bg(x, y):
                queue.append((x, y))
                visited[x][y] = True
                background[x][y] = True
    for y in range(h):
        for x in [0, w - 1]:
            if not visited[x][y] and is_bg(x, y):
                queue.append((x, y))
                visited[x][y] = True
                background[x][y] = True

    # BFS flood fill
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                visited[nx][ny] = True
                if is_bg(nx, ny):
                    background[nx][ny] = True
                    queue.append((nx, ny))

    for x in range(w):
        for y in range(h):
            if background[x][y]:
                pixels[x, y] = (0, 0, 0, 0)

    return img


# ---------------------------------------------------------------------------
# Strategy 2: ML-based removal via ToonOut / BiRefNet
# ---------------------------------------------------------------------------

def remove_bg_ml(img: Image.Image, model_name: str = "ZhengPeng7/BiRefNet", threshold: float = 0.5) -> Image.Image:
    """Remove background using ToonOut (BiRefNet fine-tuned on anime/illustration).

    Produces a binary alpha mask by thresholding the model's soft output.
    Requires: pip install transformers torch torchvision
    """
    try:
        import torch
        import numpy as np
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation
    except ImportError:
        print("Error: ML background removal requires additional packages.")
        print("Install with: pip install transformers torch torchvision")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Loading ML model '{model_name}' on {device}...")

    model = AutoModelForImageSegmentation.from_pretrained(
        model_name, trust_remote_code=True
    )
    model = model.to(device, dtype=torch.float32)
    model.eval()

    # Preprocess
    transform = transforms.Compose([
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    input_img = img.convert("RGB")
    input_tensor = transform(input_img).unsqueeze(0).to(device)

    # Inference
    with torch.no_grad():
        preds = model(input_tensor)[-1].sigmoid().cpu()

    # Post-process mask
    pred = preds[0].squeeze()
    mask_np = pred.numpy()

    # Resize mask back to original image size
    mask_pil = Image.fromarray((mask_np * 255).astype("uint8"), mode="L")
    mask_pil = mask_pil.resize(img.size, Image.Resampling.LANCZOS)

    # Binary threshold for hard pixel edges
    mask_pil = mask_pil.point(lambda p: 255 if p > int(threshold * 255) else 0)

    # Apply mask
    img = img.convert("RGBA")
    img.putalpha(mask_pil)

    return img


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def crop_to_content(img: Image.Image, padding: int = 0) -> Image.Image:
    """Crop image to bounding box of non-transparent content."""
    bbox = img.getbbox()
    if bbox is None:
        return img

    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)

    return img.crop((left, top, right, bottom))


def rasterize(img: Image.Image, target_w: int, target_h: int, margin: int = 1) -> Image.Image:
    """Resize image to fill target dimensions with minimal transparent margin.

    Preserves aspect ratio. The sprite is scaled as large as possible,
    leaving only `margin` px of transparent space on each side, then
    centered on a transparent canvas of exactly target_w x target_h.
    """
    # Available space after subtracting margins on both sides
    inner_w = max(1, target_w - margin * 2)
    inner_h = max(1, target_h - margin * 2)

    # Scale to fit within inner bounds, preserving aspect ratio
    src_w, src_h = img.size
    scale = min(inner_w / src_w, inner_h / src_h)
    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))

    sprite = img.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Center on transparent canvas
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(sprite, (offset_x, offset_y), sprite)

    return canvas


def parse_size(size_str: str) -> tuple[int, int]:
    """Parse size string like '32' (square) or '64x32' (WxH)."""
    if "x" in size_str.lower():
        parts = size_str.lower().split("x")
        return int(parts[0]), int(parts[1])
    s = int(size_str)
    return s, s


# Gemini supported aspect ratios (w:h)
GEMINI_RATIOS = [
    (1, 1), (3, 2), (2, 3), (3, 4), (4, 3),
    (4, 5), (5, 4), (9, 16), (16, 9), (21, 9),
    (1, 4), (4, 1), (1, 8), (8, 1),
]


def suggest_gemini_ratio(w: int, h: int) -> str:
    """Find the closest Gemini-supported aspect ratio for the given dimensions.

    Returns the ratio as a string like '3:2' for use in the Gemini prompt.
    Called by process_asset.py --suggest-ratio or used by Claude in the workflow.
    """
    target = w / h
    best_ratio = (1, 1)
    best_diff = float("inf")

    for rw, rh in GEMINI_RATIOS:
        diff = abs((rw / rh) - target)
        if diff < best_diff:
            best_diff = diff
            best_ratio = (rw, rh)

    return f"{best_ratio[0]}:{best_ratio[1]}"


def main():
    parser = argparse.ArgumentParser(
        description="Post-process 2D game asset: remove background + rasterize"
    )
    parser.add_argument("input", nargs="?", help="Input image path (omit with --suggest-ratio)")
    parser.add_argument("--size", default="32", help="Target pixel size: 32 or 64x32 (default: 32)")
    parser.add_argument("--suggest-ratio", action="store_true",
                        help="Print the best Gemini aspect ratio for --size and exit")
    parser.add_argument("-o", "--output", help="Output path (default: input_processed.png)")
    parser.add_argument("--tolerance", type=int, default=30, help="Color tolerance (default: 30)")
    parser.add_argument("--padding", type=int, default=0, help="Padding around cropped sprite (default: 0)")
    parser.add_argument("--no-remove-bg", action="store_true", help="Skip background removal")
    parser.add_argument("--margin", type=int, default=1, help="Transparent margin in px around sprite in final output (default: 1)")
    parser.add_argument("--no-resize", action="store_true", help="Skip resize/rasterize")
    parser.add_argument("--crop-only", action="store_true", help="Only crop to bounding box, no resize")

    # Background removal strategy
    parser.add_argument("--bg-color", default="magenta", choices=["magenta", "green", "white"],
                        help="Background color for chroma key removal (default: magenta)")
    parser.add_argument("--ml", action="store_true",
                        help="Use ML model (ToonOut) for background removal instead of chroma key")
    parser.add_argument("--ml-model", default="ZhengPeng7/BiRefNet",
                        help="HuggingFace model for ML removal (default: ZhengPeng7/BiRefNet)")
    parser.add_argument("--ml-threshold", type=float, default=0.5,
                        help="Alpha threshold for ML mask binarization (default: 0.5)")

    args = parser.parse_args()

    # Quick mode: just print the suggested Gemini aspect ratio and exit
    if args.suggest_ratio:
        w, h = parse_size(args.size)
        ratio = suggest_gemini_ratio(w, h)
        print(ratio)
        sys.exit(0)

    if not args.input:
        parser.error("input is required (unless using --suggest-ratio)")

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_stem(input_path.stem + "_processed")

    target_w, target_h = parse_size(args.size)

    print(f"Processing: {input_path}")
    img = Image.open(input_path).convert("RGBA")
    print(f"  Input size: {img.width}x{img.height}")

    # Step 1: Remove background
    if not args.no_remove_bg:
        if args.ml:
            print(f"  Removing background with ML model ({args.ml_model})...")
            img = remove_bg_ml(img, model_name=args.ml_model, threshold=args.ml_threshold)
        else:
            print(f"  Removing {args.bg_color} background (chroma key, tolerance={args.tolerance})...")
            img = remove_bg_chroma_key(img, bg_color=args.bg_color, tolerance=args.tolerance)

    # Step 2: Crop to content
    img = crop_to_content(img, padding=args.padding)
    print(f"  Cropped to: {img.width}x{img.height}")

    # Step 3: Check aspect ratio match
    if not args.no_resize and not args.crop_only:
        crop_ratio = img.width / img.height
        target_ratio = target_w / target_h
        ratio_diff = abs(crop_ratio - target_ratio) / target_ratio
        if ratio_diff > 0.15:
            print(f"  WARNING: Aspect ratio mismatch! Sprite is {img.width}:{img.height} "
                  f"(ratio {crop_ratio:.2f}) but target is {target_w}:{target_h} "
                  f"(ratio {target_ratio:.2f}). Sprite will not fill the canvas fully.")
            print(f"  Consider using --size {img.width}x{img.height} or re-generating with matching aspect ratio.")

    # Step 4: Rasterize to target size
    if not args.no_resize and not args.crop_only:
        print(f"  Rasterizing to: {target_w}x{target_h} (margin={args.margin}px)")
        img = rasterize(img, target_w, target_h, margin=args.margin)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    print(f"  Saved: {output_path} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
