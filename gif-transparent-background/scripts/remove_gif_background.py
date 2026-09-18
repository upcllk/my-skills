#!/usr/bin/env python3
"""Remove an animated image background frame-by-frame with rembg."""

from __future__ import annotations

import argparse
import io
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Segment every animation frame and write a transparent GIF or WebP."
    )
    parser.add_argument("input", type=Path, help="Source GIF or animated image")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path; use .gif or .webp",
    )
    parser.add_argument(
        "--model",
        default="u2netp",
        help="rembg model name (default: u2netp; use u2net for higher quality)",
    )
    return parser.parse_args()


def segment_frame(frame: Image.Image, session: object) -> Image.Image:
    try:
        from PIL import Image
        from rembg import remove
    except ImportError as exc:
        raise SystemExit(
            "Missing GIF transparency dependencies. Install them with: "
            "python3 -m pip install -r requirements.txt"
        ) from exc

    rgba = frame.convert("RGBA")
    buffer = io.BytesIO()
    rgba.save(buffer, format="PNG")
    result = remove(buffer.getvalue(), session=session)
    return Image.open(io.BytesIO(result)).convert("RGBA")


def main() -> None:
    args = parse_args()
    try:
        from PIL import Image, ImageSequence
        from rembg import new_session
    except ImportError as exc:
        raise SystemExit(
            "Missing GIF transparency dependencies. Install them with: "
            "python3 -m pip install -r requirements.txt"
        ) from exc

    if not args.input.is_file():
        raise SystemExit(f"Input does not exist: {args.input}")
    if args.output.suffix.lower() not in {".gif", ".webp"}:
        raise SystemExit("Output must use .gif or .webp")

    source = Image.open(args.input)
    # Reuse one model session for the whole animation; creating one per frame
    # multiplies memory use and can exhaust small machines.
    session = new_session(args.model)
    frames = [segment_frame(frame, session) for frame in ImageSequence.Iterator(source)]
    if not frames:
        raise SystemExit("Input contains no frames")

    durations = [
        frame.info.get("duration", source.info.get("duration", 100))
        for frame in ImageSequence.Iterator(source)
    ]
    loop = source.info.get("loop", 0)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    save_kwargs = {
        "save_all": True,
        "append_images": frames[1:],
        "duration": durations,
        "loop": loop,
    }
    if args.output.suffix.lower() == ".gif":
        # GIF stores alpha as a transparent palette index, not smooth RGBA alpha.
        save_kwargs.update(disposal=2, transparency=0, optimize=False)
        frames[0].save(args.output, format="GIF", **save_kwargs)
    else:
        frames[0].save(
            args.output,
            format="WEBP",
            lossless=True,
            minimize_size=False,
            **save_kwargs,
        )

    print(f"Wrote {len(frames)} frames to {args.output}")


if __name__ == "__main__":
    main()
