import argparse
from pathlib import Path
import json

import numpy as np
from PIL import Image, ImageDraw, ImageOps


SOURCE = Path(r"C:\Users\azmi maulana\AppData\Local\Libera Scanner\photo\2017-3")
OUTPUT = Path(r"C:\Users\azmi maulana\Documents\antigravity\converter\analysis-2017")


def number(path: Path) -> int:
    return int(path.stem.split("-")[1])


def thumbnail(path: Path) -> np.ndarray:
    return np.asarray(ImageOps.exif_transpose(Image.open(path)).convert("L").resize((160, 120)), dtype=np.float32)


def cover_score(path: Path) -> float:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB").resize((160, 120))
    pixels = np.asarray(image, dtype=np.float32)[12:108, 88:152]
    return float((pixels[:, :, 0] - pixels[:, :, 2]).mean())


def save_contact_sheet(paths: list[Path], index: int, width: int = 260, height: int = 230, columns: int = 4) -> None:
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (width * columns, height * rows), "white")
    draw = ImageDraw.Draw(sheet)
    for position, path in enumerate(paths):
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        image.thumbnail((width - 12, height - 50))
        x = (position % columns) * width + (width - image.width) // 2
        y = (position // columns) * height + 25
        sheet.paste(image, (x, y))
        draw.text(((position % columns) * width + 6, (position // columns) * height + 5), path.name, fill="black")
    sheet.save(OUTPUT / f"sheet-{index:02d}.jpg", quality=88)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=int, action="append", default=[])
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--files", nargs="+", default=[])
    parser.add_argument("--large-files", nargs="+", default=[])
    parser.add_argument("--cover-scores", action="store_true")
    parser.add_argument("--score-files", nargs="+", default=[])
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--group-sheet", type=int)
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    paths = sorted(SOURCE.glob("*.jpeg"), key=number)

    if args.group_sheet is not None:
        selected = [path for path in paths if path.name not in set(args.exclude)]
        start = (args.group_sheet - 1) * 30
        chunk = selected[start:start + 30]
        if not chunk:
            raise ValueError(f"Nomor group sheet di luar batas: {args.group_sheet}")
        save_contact_sheet(chunk, 97, width=400, height=300, columns=3)
        print(f"Tersimpan group sheet {args.group_sheet} untuk {len(chunk)} foto terpilih.")
        return

    if args.score_files:
        requested = [SOURCE / name for name in args.score_files]
        missing = [path.name for path in requested if not path.is_file()]
        if missing:
            raise ValueError(f"File tidak ditemukan: {', '.join(missing)}")
        for path in requested:
            print(f"{path.name}: {cover_score(path):.2f}")
        return

    if args.cover_scores:
        scores = [{"name": path.name, "score": round(cover_score(path), 2)} for path in paths]
        (OUTPUT / "cover-scores.json").write_text(json.dumps(scores, indent=2), encoding="utf-8")
        print(f"Tersimpan skor sampul untuk {len(scores)} foto.")
        return

    if args.large_files:
        requested = [SOURCE / name for name in args.large_files]
        missing = [path.name for path in requested if not path.is_file()]
        if missing:
            raise ValueError(f"File tidak ditemukan: {', '.join(missing)}")
        save_contact_sheet(requested, 98, width=600, height=500, columns=2)
        print(f"Tersimpan pratinjau besar untuk {len(requested)} foto.")
        return

    if args.files:
        requested = [SOURCE / name for name in args.files]
        missing = [path.name for path in requested if not path.is_file()]
        if missing:
            raise ValueError(f"File tidak ditemukan: {', '.join(missing)}")
        save_contact_sheet(requested, 99)
        print(f"Tersimpan pratinjau untuk {len(requested)} foto.")
        return

    if args.sheet:
        for index in args.sheet:
            start = (index - 1) * 32
            if start < 0 or start >= len(paths):
                raise ValueError(f"Nomor sheet di luar batas: {index}")
            save_contact_sheet(paths[start:start + 32], index)
        print(f"Tersimpan {len(args.sheet)} sheet dari {len(paths)} foto.")
        return

    if not args.report:
        print(f"Ada {len(paths)} foto. Gunakan --sheet atau --report.")
        return

    thumbs = [thumbnail(path) for path in paths]
    rows = []
    for path, thumb in zip(paths, thumbs):
        edge = float(np.abs(np.diff(thumb, axis=0)).mean() + np.abs(np.diff(thumb, axis=1)).mean())
        rows.append({"name": path.name, "edge": round(edge, 3), "contrast": round(float(thumb.std()), 3), "brightness": round(float(thumb.mean()), 3), "bytes": path.stat().st_size})
    adjacent = []
    for left, right, left_thumb, right_thumb in zip(paths, paths[1:], thumbs, thumbs[1:]):
        difference = float(np.mean(np.abs(left_thumb - right_thumb)))
        adjacent.append({"left": left.name, "right": right.name, "difference": round(difference, 3)})
    report = {
        "count": len(paths),
        "gaps": [number(right) for left, right in zip(paths, paths[1:]) if number(right) != number(left) + 1],
        "low_edge": sorted(rows, key=lambda row: row["edge"])[:40],
        "low_contrast": sorted(rows, key=lambda row: row["contrast"])[:30],
        "smallest": sorted(rows, key=lambda row: row["bytes"])[:30],
        "similar_adjacent": sorted(adjacent, key=lambda row: row["difference"])[:40],
    }
    (OUTPUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Tersimpan laporan untuk {len(paths)} foto.")


if __name__ == "__main__":
    main()
