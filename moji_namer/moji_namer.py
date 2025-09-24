#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.

A script to rename the bitmoji pictures.


Usage:

    cd ~/rp/zz_forks/moji_namer/moji_namer/
    ipython -i moji_namer.py -- /home/paul/rp/zz_forks/label --dry-run
    ipython -i moji_namer.py -- /home/paul/rp/zz_forks/label

"""

# Modules #
import argparse
import base64
import glob
import mimetypes
import os
import re
from pathlib import Path
from typing import List
from openai import OpenAI


def get_openai_client() -> OpenAI:
    """
    Create an OpenAI client. Reads the API key from the environment.
    Requires the environment variable `OPENAI_API_KEY` to be set.
    """
    return OpenAI()


def encode_image_as_data_url(image_path: str) -> str:
    """Return a data URL for a local image file suitable for vision input."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    with open(image_path, "rb") as handle:
        b64 = base64.b64encode(handle.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def request_image_name(
    client: OpenAI, image_path: str, model: str = "gpt-4o-mini"
) -> str:
    """Ask the model to generate a short, file-safe base name for the image."""
    data_url = encode_image_as_data_url(image_path)
    system_prompt = (
        "You name image files succinctly for easy search."
        "Respond with a single short snake_case name, no spaces, lowercase, "
        "ASCII letters/numbers/underscores only. 3-6 words, max 42 characters. "
        "Do not include the file extension or any punctuation beyond underscores."
    )
    user_text = (
        "Give a concise, descriptive base name for this image. "
        "Return only the name, nothing else."
    )
    msg = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]
    resp = client.chat.completions.create(
        model=model,
        messages=msg,
        temperature=0.2,
        max_tokens=20,
    )
    text = resp.choices[0].message.content.strip()
    return text


def sanitize_to_slug(text: str, max_length: int = 40) -> str:
    """Sanitize arbitrary text to a safe snake_case slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9_\-\s]+", "", text)
    text = re.sub(r"[\s\-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("_")
    if not text:
        text = "image"
    return text[:max_length]


def make_unique_path(directory: Path, base_name: str, extension: str) -> Path:
    """Return a non-colliding Path by appending a numeric suffix if needed."""
    candidate = directory / f"{base_name}{extension}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{base_name}-{counter}{extension}"
        counter += 1
    return candidate


def main(directory_path: str, model: str, dry_run: bool) -> None:
    """Rename the pictures in the directory using ChatGPT vision."""
    directory = Path(directory_path).expanduser().resolve()
    if not directory.is_dir():
        raise SystemExit(f"Not a directory: {directory}")

    client = get_openai_client()

    patterns: List[str] = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
    picture_paths: List[str] = []
    for pattern in patterns:
        picture_paths.extend(glob.glob(str(directory / pattern)))

    for picture in sorted(picture_paths):
        src = Path(picture)
        try:
            suggested = request_image_name(client, str(src), model=model)
        except Exception as exc:
            print(f"[skip] {src.name}: API error: {exc}")
            raise exc
            # continue

        slug = sanitize_to_slug(suggested)
        if not slug:
            print(f"[skip] {src.name}: empty suggestion")
            continue

        dest = make_unique_path(src.parent, slug, src.suffix.lower())
        if dest == src:
            print(f"[keep] {src.name}")
            continue

        if dry_run:
            print(f"[plan] {src.name} -> {dest.name}")
        else:
            os.rename(src, dest)
            print(f"[renamed] {src.name} -> {dest.name}")


if __name__ == "__main__":
    # Make an argparse object
    desc = "Rename images using ChatGPT vision."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "path",
        type=str,
        help="The path to the directory with the pictures.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned renames without changing files",
    )
    args = parser.parse_args()

    # Call the main function #
    main(args.path, model=args.model, dry_run=args.dry_run)
