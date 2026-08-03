#!/usr/bin/env python3
"""Synthesize scene narration with retries, then create one concatenated audio file."""
import argparse, asyncio, json, subprocess
from pathlib import Path
import edge_tts
from gtts import gTTS
from mutagen.mp3 import MP3

async def save(text, voice, path):
    last=None
    for attempt in range(1,4):
        try: await edge_tts.Communicate(text, voice, rate="-8%").save(str(path)); return
        except Exception as exc:
            last=exc; print(f"TTS lần {attempt}/3 thất bại: {exc}"); await asyncio.sleep(attempt*2)
    # Google Translate TTS keeps the pipeline useful in networks that route
    # normal HTTPS but explicitly block speech.platform.bing.com.
    print(f"Edge TTS không khả dụng; dùng giọng dự phòng gTTS: {last}")
    await asyncio.to_thread(gTTS(text=text, lang="vi").save, str(path))

async def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",default="assets/scenes.json"); ap.add_argument("--voice",default="vi-VN-HoaiMyNeural"); a=ap.parse_args()
    path=Path(a.input); data=json.loads(path.read_text(encoding="utf-8")); audio=path.parent/"audio"; audio.mkdir(exist_ok=True)
    for scene in data["scenes"]:
        target=audio/f"scene-{scene['id']:02}.mp3"; await save(scene["text"],a.voice,target)
        scene["audio_path"]=str(target); scene["duration"]=round(MP3(target).info.length,3)
    concat=audio/"concat.txt"; concat.write_text("".join(f"file '{Path(s['audio_path']).resolve()}'\n" for s in data["scenes"]),encoding="utf-8")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c:a","libmp3lame",str(audio/"narration.mp3")],check=True)
    data["audio_path"]=str(audio/"narration.mp3"); data["voice"]=a.voice; path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Tổng thời lượng: {sum(s['duration'] for s in data['scenes']):.1f} giây")
if __name__=="__main__": asyncio.run(main())
