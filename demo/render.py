"""Render a short video replay of a real local scan of the synthetic examples.

Requires Pillow and ffmpeg only for the optional demo; the scanner is stdlib-only.
Run the README scan with --output result.json before rendering.
"""

import csv
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RESULT = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
DRAFT = json.loads((ROOT / "examples" / "draft.json").read_text(encoding="utf-8"))
with (ROOT / "examples" / "history.csv").open(encoding="utf-8", newline="") as handle:
    HISTORY = {row["id"]: row for row in csv.DictReader(handle)}

assert RESULT["verdict"] == "review_needed"
assert RESULT["comparisons"][0]["prior_id"] == "CASE-014"
assert RESULT["comparisons"][0]["decision"] in {"related", "repeat"}
assert RESULT["comparisons"][1]["prior_id"] == "CASE-021"
assert RESULT["comparisons"][1]["decision"] == "distinct"

W, H, FPS, SECONDS = 1280, 720, 24, 27
BG = (13, 20, 32)
CARD = (24, 35, 52)
INK = (234, 242, 248)
MUTED = (143, 162, 181)
ACCENT = (99, 227, 184)
YELLOW = (255, 205, 111)
RED = (255, 134, 143)


def font(size, bold=False):
    windows = Path("C:/Windows/Fonts")
    name = "seguisb.ttf" if bold else "segoeui.ttf"
    path = windows / name
    if not path.exists():
        path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size)


F15, F20, F24, F34, F54 = font(15), font(20), font(24), font(34, True), font(54, True)


def wrap(draw, value, f, width):
    lines = []
    line = ""
    for word in value.split():
        trial = f"{line} {word}".strip()
        if line and draw.textbbox((0, 0), trial, font=f)[2] > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def paragraph(draw, value, x, y, width, f=F20, fill=INK, spacing=10, max_lines=8):
    for line in wrap(draw, value, f, width)[:max_lines]:
        draw.text((x, y), line, font=f, fill=fill)
        y += f.size + spacing
    return y


def card(draw, box, title, body, color=ACCENT):
    draw.rounded_rectangle(box, radius=18, fill=CARD, outline=(44, 63, 81), width=2)
    x, y, x2, _ = box
    draw.text((x + 25, y + 23), title, font=F20, fill=color)
    paragraph(draw, body, x + 25, y + 60, x2 - x - 50, F20)


def shell(draw, x, y, width, lines, cursor=False):
    draw.rounded_rectangle((x, y, x + width, y + 260), radius=18, fill=(8, 14, 24), outline=(47, 67, 84), width=2)
    draw.rounded_rectangle((x, y, x + width, y + 36), radius=18, fill=(34, 47, 64))
    draw.text((x + 22, y + 53), "before-report  /  local scan", font=F20, fill=MUTED)
    for i, (line, color) in enumerate(lines):
        draw.text((x + 22, y + 91 + i * 31), line, font=F20, fill=color)
    if cursor:
        draw.rectangle((x + 22, y + 91 + len(lines) * 31, x + 34, y + 115 + len(lines) * 31), fill=ACCENT)


def frame(t):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((60, 42), "BEFORE REPORT", font=F15, fill=ACCENT)
    d.line((60, 75, W - 60, 75), fill=(48, 66, 82), width=2)
    if t < 4:
        d.text((60, 175), "Know when you've been here before.", font=F54, fill=INK)
        paragraph(d, "A local Gemma model compares a draft with your private case history before you send it.", 64, 272, 1010, F24, MUTED)
        d.rounded_rectangle((64, 415, 694, 480), radius=13, fill=(30, 61, 61))
        d.text((89, 432), "Own history  +  exact excerpts  +  human judgment", font=F24, fill=ACCENT)
        d.text((64, 646), "Recorded synthetic example  •  15 October 2026", font=F20, fill=MUTED)
    elif t < 10:
        d.text((60, 111), "One draft, three earlier cases", font=F34, fill=INK)
        card(d, (60, 181, 610, 547), "DRAFT  ·  PDF thumbnail", DRAFT["root_cause"], YELLOW)
        card(d, (635, 181, 1220, 547), "PRIOR  ·  Document preview", HISTORY["CASE-014"]["root_cause"], ACCENT)
        d.text((62, 593), "Different surface. Same share-revocation check to investigate.", font=F24, fill=MUTED)
    elif t < 17:
        d.text((60, 111), "The local scan", font=F34, fill=INK)
        shown = max(1, min(4, int((t - 10) * 1.2)))
        lines = [
            ("$ python before_report.py scan --history examples/history.csv ...", INK),
            ("  verdict: review_needed", YELLOW),
            ("  CASE-014: related  ·  inspect the shared check", ACCENT),
            ("  CASE-021: distinct · HTML escaping is unrelated", MUTED),
        ][:shown]
        shell(d, 60, 197, 1160, lines, cursor=shown < 4)
        paragraph(d, "The result comes from an actual Gemma 3 4B run against synthetic files. The model returns exact excerpts, and the program rejects ungrounded answers.", 64, 509, 1140, F20, MUTED)
    elif t < 23:
        d.text((60, 111), "A negative control matters", font=F34, fill=INK)
        card(d, (60, 195, 610, 480), "OLDER CASE  ·  HTML export", HISTORY["CASE-021"]["root_cause"], RED)
        d.rounded_rectangle((635, 195, 1220, 480), radius=18, fill=CARD, outline=(44, 63, 81), width=2)
        d.text((667, 235), "DISTINCT", font=F34, fill=ACCENT)
        paragraph(d, "Same product, different operation and failure mode. Similar names alone are not enough.", 667, 302, 500, F20)
        d.text((62, 560), "The fifteen-pair smoke test had zero false clearances and one false alarm.", font=F20, fill=MUTED)
    else:
        d.text((60, 170), "A pause before sending — not a verdict.", font=F54, fill=INK)
        paragraph(d, "BeforeReport sees only the prior cases you provide. It cannot see private reports held by a bounty program, and a model can still be wrong. Review the evidence yourself.", 64, 270, 1080, F24, MUTED)
        d.rounded_rectangle((64, 470, 1090, 535), radius=13, fill=(30, 61, 61))
        d.text((89, 488), "Local model  ·  no cloud API in this demo  ·  open-source code", font=F24, fill=ACCENT)
    d.text((60, 680), "BeforeReport  •  synthetic demonstration", font=F15, fill=MUTED)
    return im


def main():
    output = ROOT / "demo" / "before-report-demo.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
        "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ], stdin=subprocess.PIPE)
    try:
        for i in range(FPS * SECONDS):
            proc.stdin.write(frame(i / FPS).tobytes())
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")
    print(output)


if __name__ == "__main__":
    main()
