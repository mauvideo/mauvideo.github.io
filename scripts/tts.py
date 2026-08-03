#!/usr/bin/env python3
"""Synthesize scene narration with Edge TTS, falling back to gTTS on errors."""

import argparse
import asyncio
import json
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

import edge_tts
from gtts import gTTS
from mutagen.mp3 import MP3


DEFAULT_VOICE = "vi-VN-NamMinhNeural"
RATE = "+5%"
PITCH = "-2%"

_DIGITS = ("không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")
_SCALES = ("", "nghìn", "triệu", "tỷ")


def _read_three_digits(number, full=False):
    """Read a number from 0 to 999 in Vietnamese."""
    hundreds, remainder = divmod(number, 100)
    tens, units = divmod(remainder, 10)
    words = []
    if hundreds or full:
        words.extend((_DIGITS[hundreds], "trăm"))
    if tens > 1:
        words.extend((_DIGITS[tens], "mươi"))
        if units == 1:
            words.append("mốt")
        elif units == 4:
            words.append("tư")
        elif units == 5:
            words.append("lăm")
        elif units:
            words.append(_DIGITS[units])
    elif tens == 1:
        words.append("mười")
        if units == 5:
            words.append("lăm")
        elif units:
            words.append(_DIGITS[units])
    elif units:
        if hundreds or full:
            words.append("lẻ")
        words.append(_DIGITS[units])
    return " ".join(words)


def natural_number_to_words(value):
    """Convert a non-negative integer string to Vietnamese words."""
    number = int(value)
    if number == 0:
        return _DIGITS[0]

    groups = []
    while number:
        groups.append(number % 1000)
        number //= 1000

    words = []
    for index in range(len(groups) - 1, -1, -1):
        group = groups[index]
        if not group:
            continue
        # A non-leading group needs an explicit zero hundred (for example 1,005).
        words.append(_read_three_digits(group, full=index < len(groups) - 1 and group < 100))
        if index:
            words.append(_SCALES[index % 3])
            words.extend("tỷ" for _ in range(index // 3))
    return " ".join(words)


def normalize_text(text):
    """Normalize narration text before sending it to either TTS provider."""
    text = re.sub(r"\s+", " ", str(text)).strip()
    text = re.sub(r"\s+([,.])", r"\1", text)
    text = re.sub(r"(?i)\bkm\b", "ki lô mét", text)
    text = re.sub(r"%", " phần trăm", text)
    text = re.sub(r"\d+", lambda match: natural_number_to_words(match.group()), text)
    return re.sub(r"\s+", " ", text).strip()


def ssml_content(text):
    """Return escaped SSML content with pauses after periods and commas."""
    content = escape(normalize_text(text))
    content = re.sub(r"\.(?!\d)", '.<break time="300ms"/>', content)
    return re.sub(r",", ',<break time="200ms"/>', content)


def edge_communicate(text, voice):
    """Create an Edge communicator whose payload contains the requested SSML."""
    communicate = edge_tts.Communicate(" ", voice, rate=RATE)
    # edge-tts creates the outer speak/voice/prosody elements. Its public pitch
    # validator only accepts Hz, while Edge's SSML endpoint also supports percent.
    communicate.tts_config.pitch = PITCH
    communicate.texts = iter([ssml_content(text).encode("utf-8")])
    return communicate


async def save(text, voice, path):
    normalized = normalize_text(text)
    last_error = None
    for attempt in range(1, 4):
        try:
            await edge_communicate(text, voice).save(str(path))
            return
        except Exception as exc:
            last_error = exc
            print(f"TTS lần {attempt}/3 thất bại: {exc}")
            await asyncio.sleep(attempt * 2)

    print(f"Edge TTS không khả dụng; dùng giọng dự phòng gTTS: {last_error}")
    await asyncio.to_thread(gTTS(text=normalized, lang="vi").save, str(path))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="assets/scenes.json")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    args = parser.parse_args()
    path = Path(args.input)
    data = json.loads(path.read_text(encoding="utf-8"))
    audio = path.parent / "audio"
    audio.mkdir(exist_ok=True)
    for scene in data["scenes"]:
        target = audio / f"scene-{scene['id']:02}.mp3"
        await save(scene["text"], args.voice, target)
        scene["audio_path"] = str(target)
        scene["duration"] = round(MP3(target).info.length, 3)
    concat = audio / "concat.txt"
    concat.write_text(
        "".join(f"file '{Path(scene['audio_path']).resolve()}'\n" for scene in data["scenes"]),
        encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:a", "libmp3lame", str(audio / "narration.mp3")],
        check=True,
    )
    data["audio_path"] = str(audio / "narration.mp3")
    data["voice"] = args.voice
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tổng thời lượng: {sum(scene['duration'] for scene in data['scenes']):.1f} giây")


if __name__ == "__main__":
    asyncio.run(main())
