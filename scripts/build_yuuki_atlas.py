"""Build Yuuki's movement atlas from reviewed source animation strips."""
from pathlib import Path
from collections import deque
from PIL import Image, ImageFilter
import json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Assets" / "Game" / "Art" / "Yuuki"
CELL = 512
COLS = 6
ROWS = 6
DEFINITIONS = [
    ("walk_left", "Art/Yuuki/Left/walk-left-clean-v3.png", 0, 2, 8, True, "cleaned_walk_candidate"),
    ("walk_right", "Art/Yuuki/Right/walk-right-legs-v2.png", 0, 1, 8, True, "revised_walk_candidate"),
    ("run_left", "Art/Yuuki/Left/run-left-clean-v3.png", 0, 2, 12, True, "cleaned_run_candidate"),
    ("run_right", "Art/Yuuki/Right/run-jump-study-v2.png", 0, 3, 12, True, "user_approved_frames"),
    ("jump_left", "Art/Yuuki/Left/jump-left-clean-v3.png", 0, 2, 10, False, "cleaned_jump_candidate"),
    ("jump_right", "Art/Yuuki/Right/run-jump-study-v2.png", 1, 3, 10, False, "study_not_approved"),
]

def bounds(index, total, count):
    return round(index * total / count), round((index + 1) * total / count)

def prepared_walk_frame(source, col):
    """Normalize the new 724px tall strip to the existing character scale."""
    if source.size != (2172, 724):
        raise ValueError(f"Unexpected generated walk dimensions: {source.size}")
    source_cell = source.crop((col * 362, 0, (col + 1) * 362, 724))
    solid = source_cell.getchannel("A").point(lambda alpha: 255 if alpha >= 128 else 0)
    box = solid.getbbox()
    if box is None or box[0] == 0 or box[1] < 150 or box[3] > 570:
        raise ValueError(f"Walk frame {col} touches a cell edge: {box}")
    if col < 5 and source.getchannel("A").crop(((col + 1) * 362, 0, (col + 1) * 362 + 1, 724)).getextrema()[1] >= 128:
        raise ValueError(f"Walk frames {col} and {col + 1} overlap")
    frame = source_cell.crop((0, 150, 362, 570))
    # Remove near-transparent generation speckles without changing opaque art.
    frame.putalpha(frame.getchannel("A").point(lambda alpha: 0 if alpha < 64 else alpha))
    frame = frame.resize((272, 315), Image.Resampling.NEAREST)
    return frame

def remove_detached_pixels(frame):
    """Keep the connected character; discard stray pieces from adjacent cells."""
    width, height = frame.size
    alpha = frame.getchannel("A")
    values = alpha.tobytes()
    visited = bytearray(width * height)
    largest = []
    for start, value in enumerate(values):
        if value < 64 or visited[start]:
            continue
        queue = deque([start])
        visited[start] = 1
        component = []
        while queue:
            index = queue.popleft()
            component.append(index)
            y, x = divmod(index, width)
            for near_y in range(max(0, y - 1), min(height, y + 2)):
                for near_x in range(max(0, x - 1), min(width, x + 2)):
                    neighbor = near_y * width + near_x
                    if values[neighbor] >= 64 and not visited[neighbor]:
                        visited[neighbor] = 1
                        queue.append(neighbor)
        if len(component) > len(largest):
            largest = component
    if len(largest) < 1000:
        raise ValueError("No complete sprite found for detached-pixel cleanup")
    kept = bytearray(width * height)
    for index in largest:
        kept[index] = 255
    # Retain the anti-aliased edge immediately around the connected sprite.
    neighborhood = Image.frombytes("L", frame.size, bytes(kept)).filter(ImageFilter.MaxFilter(5))
    clean_alpha = bytes(value if mask else 0 for value, mask in zip(values, neighborhood.tobytes()))
    removed = sum(1 for before, after in zip(values, clean_alpha) if before and not after)
    frame.putalpha(Image.frombytes("L", frame.size, clean_alpha))
    # Generated files may contain colored RGB under alpha=0. Canonicalize it
    # so downstream reference tools cannot mistake invisible data for artwork.
    clean = Image.new("RGBA", frame.size)
    clean.alpha_composite(frame)
    return clean, removed


def prepared_grid_frames(source, name):
    """Pack the retouched 3x2 sheets with one scale for the entire clip."""
    if source.size != (1536, 1024):
        raise ValueError(f"Unexpected retouched grid size: {source.size}")
    ratio = {"walk_left": 0.87, "run_left": 0.90, "jump_left": 1.0}[name]
    frames = []
    for index in range(6):
        x, y = (index % 3) * CELL, (index // 3) * CELL
        frame, removed = remove_detached_pixels(source.crop((x, y, x + CELL, y + CELL)))
        size = round(CELL * ratio)
        frame = frame.resize((size, size), Image.Resampling.NEAREST)
        box = frame.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()
        if box is None or min(box[:2]) < 8 or max(box[2:]) >= size - 8:
            raise ValueError(f"{name} frame {index} touches its source cell")
        # Gold halo is a stable horizontal landmark; never scale frames separately.
        points = [(px, py) for py in range(box[1], min(box[1] + 80, size))
                  for px in range(size)
                  if (lambda p: p[3] >= 128 and p[0] > p[1] > p[2] and p[0] - p[2] > 45)(frame.getpixel((px, py)))]
        if len(points) < 20:
            raise ValueError(f"Cannot locate halo in {name} frame {index}")
        halo_x = sum(p[0] for p in points) / len(points)
        frames.append((frame, box, round(220 - halo_x), removed))
    # Walks keep the supporting foot on the floor. Runs retain their flight phase:
    # align each three-frame half-cycle together, without pulling lifted feet down.
    ground = [max(f[1][3] for f in frames[:3]), max(f[1][3] for f in frames[3:])]
    result = []
    for index, (frame, box, xoff, removed) in enumerate(frames):
        yoff = 0 if name == "jump_left" else 400 - (box[3] if name == "walk_left" else ground[index // 3])
        crop_box = (box[0] - 3, box[1] - 3, box[2] + 3, box[3] + 3)
        frame = frame.crop(crop_box)
        xoff += crop_box[0]
        yoff += crop_box[1]
        result.append((frame, xoff, yoff, removed))
    return result


def build_idle():
    sheet = Image.new("RGBA", (CELL * 2, CELL))
    clips = []
    for col, direction in enumerate(("left", "right")):
        source_rel = f"Art/Yuuki/{direction.title()}/idle-{direction}-v1.png"
        source = Image.open(ROOT / source_rel).convert("RGBA")
        source, removed = remove_detached_pixels(source)
        box = source.getchannel("A").point(lambda a: 255 if a >= 64 else 0).getbbox()
        source = source.crop(box)
        source = source.resize((round(source.width * 273 / source.height), 273), Image.Resampling.NEAREST)
        # Feet, not the asymmetric wing silhouette, define the horizontal origin.
        alpha = source.getchannel("A")
        feet = alpha.crop((0, source.height - 22, source.width, source.height)).point(lambda a: 255 if a >= 128 else 0).getbbox()
        feet_x = (feet[0] + feet[2]) / 2
        xoff, yoff = round(256 - feet_x), 400 - source.height
        sheet.alpha_composite(source, (col * CELL + xoff, yoff))
        clips.append({"name": f"idle_{direction}", "column": col, "frames": 1,
                      "pivot_x_px": 256, "pivot_y_from_top_px": 400, "source": source_rel,
                      "removed_detached_pixels": removed, "status": "neutral_pose_candidate"})
    sheet.save(OUTPUT / "Yuuki_Idle_2x1.png", optimize=True)
    (OUTPUT / "Yuuki_Idle_2x1.json").write_text(json.dumps({
        "atlas": "Yuuki_Idle_2x1.png", "dimensions_px": list(sheet.size),
        "frame_size_px": [CELL, CELL], "clips": clips,
        "note": "Grounded neutral poses; no breathing or blink cycle yet."
    }, indent=2) + "\n", encoding="utf-8")

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    atlas = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
    clips = []
    for row, (name, source_rel, source_row, source_rows, fps, loop, status) in enumerate(DEFINITIONS):
        source = Image.open(ROOT / source_rel).convert("RGBA")
        source_boxes = []
        removed_detached = 0
        retouched = name in ("walk_left", "run_left", "jump_left")
        prepared = prepared_grid_frames(source, name) if retouched else None
        for col in range(COLS):
            if retouched:
                frame, xoff, yoff, removed = prepared[col]
                removed_detached += removed
            elif name.startswith("walk_"):
                frame = prepared_walk_frame(source, col)
                xoff = (CELL - frame.width) // 2
                yoff = 96  # Both walk clips share a stable foot pivot at y=400.
            else:
                x0, x1 = bounds(col, source.width, COLS)
                y0, y1 = bounds(source_row, source.height, source_rows)
                frame = source.crop((x0, y0, x1, y1))
                xoff = (CELL - frame.width) // 2
                yoff = (CELL - frame.height) // 2
            if name != "run_right" and not retouched:
                frame, removed = remove_detached_pixels(frame)
                removed_detached += removed
            if xoff < 0 or yoff < 0:
                raise ValueError(f"{name} frame {col} does not fit a {CELL}px cell")
            atlas.paste(frame, (col * CELL + xoff, row * CELL + yoff))
            alpha = frame.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
            box = alpha.getbbox()
            if box is None:
                raise ValueError(f"{name} frame {col} has no visible pixels")
            source_boxes.append(box)
        frame_height = bounds(source_row, source.height, source_rows)[1] - bounds(source_row, source.height, source_rows)[0]
        foot_y = 408 if name == "jump_left" else 400 if name.startswith("walk_") or retouched else yoff + max(box[3] for box in source_boxes)
        clips.append({
            "name": name,
            "row": row,
            "frames": COLS,
            "fps": fps,
            "loop": loop,
            "source": source_rel.replace("\\", "/"),
            "source_row_top_based": source_row,
            "source_row_count": source_rows,
            "source_column_count": 3 if retouched else COLS,
            "source_frame_height_px": frame_height,
            "normalized_frame_height_px": frame.height,
            "pivot_x_px": CELL // 2,
            "pivot_y_from_top_px": foot_y,
            "status": status,
            "possible_source_edge_cut": False if name.startswith("walk_") or retouched else any(box[0] == 0 or box[2] >= bounds(col, source.width, COLS)[1] - bounds(col, source.width, COLS)[0] for col, box in enumerate(source_boxes)),
            "removed_detached_pixels": removed_detached
        })
    atlas_path = OUTPUT / "Yuuki_Movement_6x6.png"
    atlas.save(atlas_path, format="PNG", optimize=True)
    manifest = {
        "format": "6 columns x 6 rows, top to bottom: walk left/right, run left/right, jump left/right",
        "atlas": atlas_path.name,
        "dimensions_px": list(atlas.size),
        "frame_size_px": [CELL, CELL],
        "frame_order": "left to right, original source order",
        "image_operations": "left walk/run/jump retouched and aligned; detached islands and invisible RGB removed except in approved right run, whose pixels are preserved",
        "double_jump_included": False,
        "clips": clips
    }
    (OUTPUT / "Yuuki_Movement_6x6.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(str(atlas_path))
    print(f"{atlas.width}x{atlas.height} RGBA, cells {CELL}x{CELL}")
    for clip in clips:
        print(clip["name"], "pivot y:", clip["pivot_y_from_top_px"], "source edge:", clip["possible_source_edge_cut"])
    build_idle()

if __name__ == "__main__":
    main()
