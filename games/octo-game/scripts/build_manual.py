#!/usr/bin/env python3
"""Build the staged Octo Game instruction manual artwork and PDF."""

from __future__ import annotations

import math
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


GAME_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = GAME_ROOT / "docs"
ART_DIR = DOCS_DIR / "assets" / "manual-art"
LAYOUT_ART_DIR = DOCS_DIR / "assets" / "manual-layout"
PAGES_DIR = DOCS_DIR / "manual-pages"
PREVIEWS_DIR = DOCS_DIR / "previews"

PAGE_SIZE = (1650, 2550)  # 5.5 x 8.5 inches at 300 dpi
CREAM = "#f7f1de"
ORANGE = "#ee4f13"
BLUE = "#27aee4"
INK = "#161616"

FONT_REGULAR = Path("/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Regular.otf")
FONT_BOLD = Path("/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf")
FONT_SECTION = Path("/usr/share/fonts/opentype/urw-base35/URWBookman-Demi.otf")
FONT_BLUE_HEADING = FONT_BOLD
FONT_BODY_SIZE = 38


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def centered_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    typeface: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    box = draw.textbbox((0, 0), text, font=typeface)
    width = box[2] - box[0]
    x = (PAGE_SIZE[0] - width) // 2 - box[0]
    draw.text((x, y), text, font=typeface, fill=fill)


def paste_centered_asset(
    page: Image.Image,
    asset_path: Path,
    center: tuple[int, int],
    max_size: tuple[int, int],
    background: str | None = None,
    transparent_edge_background: bool = False,
    crop_to_ink: bool = False,
) -> None:
    # Preserve alpha for transparent layout assets such as the title and
    # instruction-banner lettering. Converting them to RGB first turns
    # transparent enclosed pixels into black marks when they are composited.
    source = Image.open(asset_path)
    asset = source.convert("RGBA" if "A" in source.getbands() else "RGB")
    if background is not None:
        # The scanned Missile Command joystick has a paper-white field. Blend
        # that field into this manual's cream stock while retaining antialiased
        # graphite edges around the line art.
        background_rgb = tuple(int(background[index : index + 2], 16) for index in (1, 3, 5))
        pixels = asset.load()
        for py in range(asset.height):
            for px in range(asset.width):
                original = pixels[px, py]
                lightness = min(original)
                if lightness > 190:
                    ink_weight = min(1.0, max(0.0, (255 - lightness) / 65.0))
                    pixels[px, py] = tuple(
                        round(background_rgb[channel] * (1.0 - ink_weight) + original[channel] * ink_weight)
                        for channel in range(3)
                    )
    if crop_to_ink:
        # The supplied Missile Command joystick scan contains a large blank
        # right margin. Crop to the illustration so its visible drawing, not
        # the scan canvas, can be centered in the column.
        ink = asset.load()
        points = [
            (px, py)
            for py in range(asset.height)
            for px in range(asset.width)
            if min(ink[px, py]) < 235
        ]
        if points:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            asset = asset.crop((max(0, min(xs) - 8), max(0, min(ys) - 8),
                                min(asset.width, max(xs) + 9), min(asset.height, max(ys) + 9)))

    asset = asset.convert("RGBA")
    if transparent_edge_background:
        # Remove only the black scan field connected to the image edge. The
        # dark outlines around the cream lettering remain intact.
        from collections import deque

        pixels = asset.load()
        queue = deque()
        seen: set[tuple[int, int]] = set()
        for px in range(asset.width):
            queue.extend(((px, 0), (px, asset.height - 1)))
        for py in range(asset.height):
            queue.extend(((0, py), (asset.width - 1, py)))
        while queue:
            px, py = queue.popleft()
            if (px, py) in seen or not (0 <= px < asset.width and 0 <= py < asset.height):
                continue
            seen.add((px, py))
            red, green, blue, _ = pixels[px, py]
            if max(red, green, blue) > 90:
                continue
            pixels[px, py] = (red, green, blue, 0)
            queue.extend(((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)))
    scale = min(max_size[0] / asset.width, max_size[1] / asset.height, 1.0)
    if scale < 1.0:
        asset = asset.resize(
            (round(asset.width * scale), round(asset.height * scale)),
            Image.Resampling.LANCZOS,
        )
    x = center[0] - asset.width // 2
    y = center[1] - asset.height // 2
    page.paste(asset, (x, y), asset)


def instruction_banner(page: Image.Image, draw: ImageDraw.ImageDraw, y: int) -> None:
    left, right = 175, PAGE_SIZE[0] - 175
    height = 62
    draw.rectangle((left, y, right, y + height), fill=ORANGE)
    draw.line((left, y - 15, right, y - 15), fill=ORANGE, width=4)
    draw.line((left, y + height + 15, right, y + height + 15), fill=ORANGE, width=4)
    paste_centered_asset(
        page,
        LAYOUT_ART_DIR / "instruction-banner-label.png",
        ((left + right) // 2, y + height // 2),
        (1100, 52),
        transparent_edge_background=True,
    )


def make_interior_page() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Return a blank interior page with the shared instruction header."""
    page = Image.new("RGB", PAGE_SIZE, CREAM)
    draw = ImageDraw.Draw(page)
    instruction_banner(page, draw, 86)
    return page, draw


def section_heading(draw: ImageDraw.ImageDraw, number: int, title: str, y: int) -> None:
    # The Missile Command interior headings use a compact, heavy blue sans face.
    # Keep the Bookman face for the contents rows, which have a different role.
    heading = ImageFont.truetype(str(FONT_BLUE_HEADING), 86)
    centered_text(draw, y, f"{number}. {title.upper()}", heading, BLUE)


def page_number(draw: ImageDraw.ImageDraw, number: int) -> None:
    label = str(number)
    face = font(37)
    box = draw.textbbox((0, 0), label, font=face)
    draw.text(
        ((PAGE_SIZE[0] - (box[2] - box[0])) // 2, 2446),
        label,
        font=face,
        fill=INK,
    )


def wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    typeface: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_spacing: int = 10,
) -> None:
    """Draw text wrapped by measured pixel width rather than character count."""
    x, y = xy
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        box = draw.textbbox((0, 0), candidate, font=typeface)
        if current and box[2] - box[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)

    line_height = typeface.getbbox("Ag")[3] - typeface.getbbox("Ag")[1]
    for line in lines:
        draw.text((x, y), line, font=typeface, fill=fill)
        y += line_height + line_spacing


def make_survival_orders_page() -> Image.Image:
    page, draw = make_interior_page()
    section_heading(draw, 1, "The Game Begins", 235)

    story_art = Image.open(ART_DIR / "story-illustration-v3.png").convert("RGB")
    art_box = (390, 375, 1260, 1680)
    story_art = story_art.resize(
        (art_box[2] - art_box[0], art_box[3] - art_box[1]),
        Image.Resampling.LANCZOS,
    )
    page.paste(story_art, art_box[:2])
    draw.rectangle(art_box, outline=ORANGE, width=5)

    copy_face = font(FONT_BODY_SIZE)
    left_copy = (
        "On a nameless station beyond the mapped stars, a debt-relief bureau "
        "announced the first interplanetary children's game show. The prize was "
        "a clean slate. The fine print was printed in a font too small for most "
        "tentacles. Contestants were promised food, fame, and a fresh start, "
        "then quietly delivered to an arena watched by an enormous nursery "
        "automaton. The Directorate called it research. The contestants called "
        "it a very bad morning."
    )
    right_copy = (
        "At the starting line, the rules sound simple. When the Watcher turns "
        "away and the signal glows green, move. When she turns back and the "
        "signal burns red, freeze completely. A twitch, a wobble, or an "
        "overconfident tentacle can end your run. Outsmart the trees and "
        "boulders, beat the merciless clock, and survive nine rounds. Fame, "
        "freedom, and a commemorative scratch-n-sniff sticker await the last "
        "octopus standing."
    )
    wrapped_text(draw, (120, 1750), left_copy, copy_face, INK, 650, 9)
    wrapped_text(draw, (880, 1750), right_copy, copy_face, INK, 650, 9)
    page_number(draw, 1)
    return page


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: str = ORANGE, width: int = 8) -> None:
    draw.line((*start, *end), fill=fill, width=width)
    head = 22
    draw.polygon(
        [
            (end[0], end[1]),
            (end[0] - head, end[1] - head // 2),
            (end[0] - head, end[1] + head // 2),
        ],
        fill=fill,
    )


def draw_octopus_icon(draw: ImageDraw.ImageDraw, center: tuple[int, int], scale: int = 1, fill: str = BLUE) -> None:
    x, y = center
    radius = 30 * scale
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=INK, width=max(2, 3 * scale))
    for dx in (-12, 12):
        draw.ellipse((x + dx * scale - 4 * scale, y - 4 * scale, x + dx * scale + 4 * scale, y + 4 * scale), fill=CREAM)
    for dx in (-12, 12):
        draw.ellipse((x + dx * scale - 2 * scale, y - 2 * scale, x + dx * scale + 2 * scale, y + 2 * scale), fill=INK)
    draw.arc((x - 12 * scale, y + 2 * scale, x + 12 * scale, y + 20 * scale), 10, 170, fill=INK, width=max(2, 3 * scale))
    for i in range(6):
        tx = x - 34 * scale + i * 14 * scale
        draw.arc((tx, y + 14 * scale, tx + 28 * scale, y + 64 * scale), 10, 165, fill=fill, width=max(3, 8 * scale))


def draw_tree_icon(draw: ImageDraw.ImageDraw, center: tuple[int, int], scale: int = 1) -> None:
    x, y = center
    draw.rectangle((x - 12 * scale, y + 28 * scale, x + 12 * scale, y + 80 * scale), fill="#83542b", outline=INK, width=max(2, 3 * scale))
    draw.ellipse((x - 58 * scale, y - 35 * scale, x + 5 * scale, y + 38 * scale), fill="#3f8b55", outline=INK, width=max(2, 3 * scale))
    draw.ellipse((x - 5 * scale, y - 48 * scale, x + 55 * scale, y + 38 * scale), fill="#3f8b55", outline=INK, width=max(2, 3 * scale))


def draw_boulder_icon(draw: ImageDraw.ImageDraw, center: tuple[int, int], scale: int = 1) -> None:
    x, y = center
    draw.ellipse((x - 42 * scale, y - 25 * scale, x + 42 * scale, y + 30 * scale), fill="#8b8172", outline=INK, width=max(2, 3 * scale))
    draw.arc((x - 25 * scale, y - 14 * scale, x + 8 * scale, y + 14 * scale), 180, 320, fill="#c5b9a8", width=max(2, 3 * scale))


def make_game_play_page() -> Image.Image:
    page, draw = make_interior_page()
    # Missile Command uses a centered blue serif display heading on the gameplay
    # page. The numbered story page has its own compact sans heading.
    centered_text(draw, 245, "2. GAME PLAY", ImageFont.truetype(str(FONT_SECTION), 78), BLUE)

    draw.rounded_rectangle((120, 390, 740, 1045), radius=24, outline=ORANGE, width=5)
    draw.text((185, 445), "THE SIGNAL", font=ImageFont.truetype(str(FONT_SECTION), 47), fill=BLUE)
    draw.ellipse((205, 570, 425, 790), fill="#2baf64", outline=INK, width=5)
    draw.ellipse((435, 570, 655, 790), fill="#d44736", outline=INK, width=5)

    def circle_label(center: tuple[int, int], label: str) -> None:
        face = font(36, bold=True)
        box = draw.textbbox((0, 0), label, font=face)
        width = box[2] - box[0]
        height = box[3] - box[1]
        draw.text(
            (center[0] - width // 2 - box[0], center[1] - height // 2 - box[1]),
            label,
            font=face,
            fill="#ffffff",
            stroke_width=4,
            stroke_fill=INK,
        )

    circle_label((315, 680), "MOVE")
    circle_label((545, 680), "FREEZE")
    draw_arrow(draw, (385, 835), (475, 835), ORANGE, 7)
    signal_summary_face = font(32, bold=True)
    for y, label in ((900, "Green means go."), (950, "Red means stop.")):
        label_box = draw.textbbox((0, 0), label, font=signal_summary_face)
        label_width = label_box[2] - label_box[0]
        draw.text((430 - label_width // 2 - label_box[0], y), label, font=signal_summary_face, fill=ORANGE)

    draw.rounded_rectangle((805, 390, 1530, 1045), radius=24, outline=ORANGE, width=5)
    draw.text((875, 440), "SCREEN ELEMENTS", font=ImageFont.truetype(str(FONT_SECTION), 42), fill=BLUE)
    game_screen = Image.open(ART_DIR / "gameplay-level1-v1.png").convert("RGB")
    screen_box = (900, 570, 1435, 971)
    game_screen = game_screen.resize((screen_box[2] - screen_box[0], screen_box[3] - screen_box[1]), Image.Resampling.NEAREST)
    page.paste(game_screen, screen_box[:2])
    draw.rectangle(screen_box, outline=INK, width=4)

    callout_face = font(25, bold=True)
    draw.text((865, 505), "SCORE", font=callout_face, fill=ORANGE)
    draw.line((920, 535, 955, 585), fill=ORANGE, width=3)
    draw.text((1300, 505), "TIMER", font=callout_face, fill=ORANGE)
    draw.line((1340, 535, 1225, 585), fill=ORANGE, width=3)
    draw.text((875, 985), "PLAYER", font=callout_face, fill=ORANGE)
    draw.line((940, 980, 1160, 910), fill=ORANGE, width=3)
    draw.text((1260, 985), "WATCHER", font=callout_face, fill=ORANGE)
    draw.line((1325, 980, 1190, 640), fill=ORANGE, width=3)

    draw.rounded_rectangle((120, 1140, 1530, 1430), radius=24, outline=ORANGE, width=5)
    draw.text((185, 1185), "YOUR MISSION", font=ImageFont.truetype(str(FONT_SECTION), 48), fill=BLUE)
    mission = (
        "Guide your octopus from the starting line to the finish line. Move only while "
        "the signal is green. Before the Watcher turns back and the signal turns red, "
        "release the joystick and become perfectly still."
    )
    wrapped_text(draw, (185, 1290), mission, font(FONT_BODY_SIZE), INK, 1220, 7)

    draw.rounded_rectangle((120, 1510, 1530, 2255), radius=24, outline=INK, width=4)
    draw.text((185, 1560), "HOW IT WORKS", font=ImageFont.truetype(str(FONT_SECTION), 50), fill=BLUE)
    draw.line((825, 1665, 825, 2080), fill=ORANGE, width=4)
    draw.text((185, 1690), "GREEN LIGHT", font=ImageFont.truetype(str(FONT_SECTION), 42), fill=BLUE)
    draw.text((900, 1690), "RED LIGHT", font=ImageFont.truetype(str(FONT_SECTION), 42), fill=BLUE)
    green_copy = (
        "Green means go. Hold UP to advance toward the finish line. Use LEFT "
        "and RIGHT to steer around obstacles. The signal timing is unpredictable, "
        "so watch the light and keep your tentacles ready."
    )
    red_copy = (
        "Red means stop. Any joystick direction during a red light causes immediate "
        "elimination. Release the controller completely until the signal turns green. "
        "The timer keeps running while you wait."
    )
    wrapped_text(draw, (185, 1800), green_copy, font(FONT_BODY_SIZE), INK, 560, 7)
    wrapped_text(draw, (900, 1800), red_copy, font(FONT_BODY_SIZE), INK, 560, 7)
    draw.line((185, 2080, 1450, 2080), fill=ORANGE, width=4)
    draw.text((185, 2125), "Move on green, freeze on red, and reach the finish line.", font=font(31, bold=True), fill=ORANGE)
    page_number(draw, 2)
    return page


def make_game_play_obstacles_page() -> Image.Image:
    page, draw = make_interior_page()
    section_heading(draw, 2, "Game Play Continued", 235)

    draw.rounded_rectangle((120, 390, 1530, 1110), radius=24, outline=ORANGE, width=5)
    draw.text((185, 450), "THE OBSTACLE COURSE", font=ImageFont.truetype(str(FONT_SECTION), 50), fill=BLUE)
    draw.line((220, 790, 1430, 790), fill=INK, width=7)
    draw_octopus_icon(draw, (300, 760), 1, BLUE)
    draw_tree_icon(draw, (620, 700), 1)
    draw_boulder_icon(draw, (900, 765), 1)
    draw_boulder_icon(draw, (1120, 765), 1)
    draw.polygon([(1370, 720), (1370, 860), (1425, 790)], fill=ORANGE, outline=INK)
    draw.text((235, 900), "START", font=font(31, bold=True), fill=ORANGE)
    draw.text((1320, 900), "FINISH", font=font(31, bold=True), fill=ORANGE)
    obstacle_copy = (
        "Some rounds are clear. On obstacle levels, one tree and two boulders "
        "block the route. Their positions change from round to round, and each "
        "obstacle has solid collision. Steer around them while the light is green."
    )
    wrapped_text(draw, (185, 960), obstacle_copy, font(FONT_BODY_SIZE), INK, 1260, 7)

    draw.rounded_rectangle((120, 1210, 790, 1810), radius=24, outline=INK, width=4)
    draw.text((185, 1265), "THE TIMER", font=ImageFont.truetype(str(FONT_SECTION), 48), fill=BLUE)
    timer_copy = (
        "Every round begins at 999. The countdown reaches 000 after about "
        "thirty seconds. Reach the finish line before time runs out."
    )
    wrapped_text(draw, (185, 1385), timer_copy, font(FONT_BODY_SIZE), INK, 540, 8)
    draw.rounded_rectangle((230, 1630, 680, 1740), radius=14, fill=INK)
    draw.text((315, 1650), "999  →  000", font=font(45, bold=True), fill="#ffd76a")

    draw.rounded_rectangle((860, 1210, 1530, 1810), radius=24, outline=INK, width=4)
    draw.text((925, 1265), "NINE ROUNDS", font=ImageFont.truetype(str(FONT_SECTION), 48), fill=BLUE)
    rounds_copy = (
        "Survive one round to advance to the next. The signal intervals become "
        "shorter as the levels advance. Levels 2, 4, 6, and 8 add the tree and "
        "two boulders to the challenge."
    )
    wrapped_text(draw, (925, 1385), rounds_copy, font(FONT_BODY_SIZE), INK, 540, 8)
    draw.text((925, 1690), "1  2  3  4  5  6  7  8  9", font=font(34, bold=True), fill=ORANGE)

    draw.rounded_rectangle((120, 1910, 1530, 2265), radius=24, outline=ORANGE, width=5)
    draw.text((185, 1965), "KEEP GOING", font=ImageFont.truetype(str(FONT_SECTION), 48), fill=BLUE)
    finish_copy = (
        "Reach the finish line to clear the round. You only have one life. If you "
        "move during a red light, you are eliminated and the game ends. Press FIRE "
        "after elimination to begin again at level 1. Clear level 9 to open the "
        "final survival screen."
    )
    wrapped_text(draw, (185, 2080), finish_copy, font(FONT_BODY_SIZE), INK, 1220, 7)
    page_number(draw, 3)
    return page


def make_level2_screenshot() -> Image.Image:
    """Create a manual-ready level-2 frame from the verified gameplay capture."""
    screen = Image.open(ART_DIR / "gameplay-level1-v1.png").convert("RGB")
    draw = ImageDraw.Draw(screen)
    red_border = (174, 57, 57)
    draw.rectangle((0, 122, 15, 479), fill=red_border)
    draw.rectangle((624, 122, 639, 479), fill=red_border)

    # Level 2 adds the tree and two boulders to the playfield.
    draw.rectangle((280, 300, 291, 345), fill=(116, 76, 39))
    draw.ellipse((245, 260, 302, 325), fill=(63, 139, 85), outline=(20, 40, 20))
    draw.ellipse((285, 250, 345, 325), fill=(63, 139, 85), outline=(20, 40, 20))
    draw.ellipse((380, 355, 445, 392), fill=(122, 111, 98), outline=(20, 20, 20))
    draw.ellipse((485, 330, 550, 367), fill=(122, 111, 98), outline=(20, 20, 20))
    draw.arc((395, 360, 425, 378), 180, 320, fill=(190, 180, 165), width=2)
    draw.arc((500, 335, 530, 353), 180, 320, fill=(190, 180, 165), width=2)
    return screen


def draw_joystick_figure(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    x, y = center
    draw.polygon([(x - 125, y + 70), (x + 100, y + 70), (x + 125, y + 110), (x - 95, y + 110)], fill="#d8d0bd", outline=INK)
    draw.polygon([(x - 100, y + 110), (x + 125, y + 110), (x + 95, y + 145), (x - 70, y + 145)], fill="#c0b7a5", outline=INK)
    draw.ellipse((x - 105, y + 55, x + 105, y + 100), fill="#c8beab", outline=INK, width=4)
    draw.ellipse((x - 75, y + 70, x + 75, y + 105), fill="#5d574f", outline=INK, width=4)
    draw.rectangle((x - 20, y - 125, x + 20, y + 75), fill="#c8beab", outline=INK, width=4)
    draw.ellipse((x - 20, y - 140, x + 20, y - 112), fill="#e5dcc9", outline=INK, width=4)


def draw_direction_figure(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    x, y = center
    draw.ellipse((x - 60, y - 60, x + 60, y + 60), outline=INK, width=5)
    draw.ellipse((x - 23, y - 23, x + 23, y + 23), outline=INK, width=5)
    directions = [
        (0, -180, "UP"), (-180, 0, "LEFT"), (180, 0, "RIGHT"),
        (-132, -132, ""), (132, -132, ""), (-132, 132, ""), (132, 132, ""),
    ]
    for dx, dy, label in directions:
        draw.line((x, y, x + dx, y + dy), fill=INK, width=5)
        if dx or dy:
            tipx, tipy = x + dx, y + dy
            length = math.hypot(dx, dy)
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            base_x = tipx - ux * 28
            base_y = tipy - uy * 28
            draw.polygon(
                [
                    (tipx, tipy),
                    (base_x + px * 13, base_y + py * 13),
                    (base_x - px * 13, base_y - py * 13),
                ],
                fill=INK,
            )
        if label:
            face = font(28, bold=True)
            box = draw.textbbox((0, 0), label, font=face)
            draw.text((x + dx - (box[2] - box[0]) // 2, y + dy + (22 if dy > 0 else -44)), label, font=face, fill=INK)
    draw.multiline_text((x + 112, y - 215), "MOVE\nDIAGONALLY", font=font(24, bold=True), fill=INK, spacing=0)


def make_controller_controls_page() -> Image.Image:
    page, draw = make_interior_page()
    centered_text(draw, 245, "3. USING THE CONTROLLERS", ImageFont.truetype(str(FONT_SECTION), 68), BLUE)

    paste_centered_asset(
        page,
        ART_DIR / "joystick-missile-command.png",
        (1195, 500),
        (560, 460),
        background=CREAM,
        crop_to_ink=True,
    )
    # Keep the two controller references on one centerline, with a deliberate
    # gap between the joystick and directional guide. Their combined group is
    # vertically aligned with the controller copy in the left column.
    draw_direction_figure(draw, (1110, 940))

    controller_copy = (
        "Use your Joystick Controllers with this ATARI® Game Program™ cartridge. "
        "Be sure the Joystick Controller cables are firmly plugged into the "
        "CONTROLLER jacks at the back of your ATARI® Video Computer System™ game. "
        "For one-player games, use the Joystick Controller plugged into the LEFT "
        "CONTROLLER jack. Hold the Joystick with the red button to your upper left, "
        "toward the television screen. See Section 3 of your owner's manual for "
        "further details."
    )
    # The reference column wraps after “with” at the chosen manual-wide body size.
    wrapped_text(draw, (120, 385), controller_copy, font(FONT_BODY_SIZE), INK, 520, 9)
    eliminated_copy = (
        "If you are eliminated, that is the end of the game. Press the FIRE button "
        "to start a new game."
    )
    wrapped_text(draw, (120, 1135), eliminated_copy, font(FONT_BODY_SIZE), INK, 520, 9)

    centered_text(draw, 1510, "4. CONSOLE CONTROLS", ImageFont.truetype(str(FONT_SECTION), 68), BLUE)
    reset_copy = (
        "Press the GAME RESET switch to begin a new run. After you clear round 9, "
        "press GAME RESET to start over at round 1. The score and timer return to "
        "their starting values, and the game begins again."
    )
    wrapped_text(draw, (120, 1655), reset_copy, font(FONT_BODY_SIZE), INK, 650, 8)
    draw.text((120, 1980), "GAME RESET → START OVER", font=font(30, bold=True), fill=ORANGE)

    level2 = make_level2_screenshot()
    screen_box = (900, 1660, 1450, 2072)
    level2 = level2.resize((screen_box[2] - screen_box[0], screen_box[3] - screen_box[1]), Image.Resampling.NEAREST)
    page.paste(level2, screen_box[:2])
    draw.rectangle(screen_box, outline=INK, width=4)
    draw.text((895, 1610), "RED BORDER", font=font(27, bold=True), fill=ORANGE)
    draw.line((1015, 1625, 905, 1790), fill=ORANGE, width=3)
    draw.text((1300, 1610), "TREE", font=font(27, bold=True), fill=ORANGE)
    draw.line((1340, 1625, 1180, 1890), fill=ORANGE, width=3)
    draw.text((895, 2110), "BOULDERS", font=font(27, bold=True), fill=ORANGE)
    draw.line((1015, 2105, 1300, 1940), fill=ORANGE, width=3)
    page_number(draw, 4)
    return page


def make_scoring_page() -> Image.Image:
    page, draw = make_interior_page()
    centered_text(draw, 245, "5. SCORING", ImageFont.truetype(str(FONT_SECTION), 78), BLUE)

    intro = (
        "Your score starts at 0000 and carries from round to round. Finish each "
        "round to add bonus points, then keep moving until you clear round 9. "
        "Compete with your friends to see who can finish all 9 rounds and get the highest score."
    )
    wrapped_text(draw, (120, 390), intro, font(FONT_BODY_SIZE), INK, 1410, 10)

    draw.rounded_rectangle((120, 650, 770, 1490), radius=24, outline=ORANGE, width=5)

    rows = [
        ("ROUND CLEAR", "+100", "Reach the finish line."),
        ("TIME LEFT", "+ TIMER", "Every point still showing."),
        ("TOTAL SCORE", "CARRIES", "Added to your running score."),
    ]
    row_y = 775
    for label, value, detail in rows:
        draw.line((185, row_y - 22, 705, row_y - 22), fill=ORANGE, width=3)
        draw.text((185, row_y), label, font=font(31, bold=True), fill=INK)
        value_box = draw.textbbox((0, 0), value, font=font(37, bold=True))
        draw.text((705 - (value_box[2] - value_box[0]), row_y - 4), value, font=font(37, bold=True), fill=ORANGE)
        wrapped_text(draw, (185, row_y + 65), detail, font(32), INK, 500, 6)
        row_y += 185

    draw.rounded_rectangle((840, 650, 1530, 1490), radius=24, outline=INK, width=4)
    draw.text((905, 745), "CLEAR ALL NINE ROUNDS", font=font(34, bold=True), fill=ORANGE)
    for index in range(9):
        cx = 930 + (index % 5) * 112
        cy = 875 + (index // 5) * 130
        draw.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=BLUE, outline=INK, width=3)
        number = str(index + 1)
        box = draw.textbbox((0, 0), number, font=font(30, bold=True))
        draw.text((cx - (box[2] - box[0]) // 2 - box[0], cy - (box[3] - box[1]) // 2 - box[1]), number, font=font(30, bold=True), fill=CREAM)
    win_copy = (
        "A round is won when your octopus reaches the finish line. Clear round 9 "
        "to win the game. The final survival "
        "screen appears with your score."
    )
    wrapped_text(draw, (905, 1170), win_copy, font(FONT_BODY_SIZE), INK, 560, 8)

    draw.rounded_rectangle((120, 1570, 1530, 2220), radius=24, outline=ORANGE, width=5)
    draw.text((185, 1640), "SCORING EXAMPLE", font=ImageFont.truetype(str(FONT_SECTION), 48), fill=BLUE)
    example = (
        "You reach the finish line with 742 on the timer. Your round score is "
        "100 completion points plus 742 time points."
    )
    wrapped_text(draw, (185, 1760), example, font(FONT_BODY_SIZE), INK, 1250, 8)

    draw.rounded_rectangle((240, 1900, 1410, 2045), radius=18, fill=INK)
    draw.text((315, 1933), "100  +  742  =  842 POINTS", font=font(48, bold=True), fill="#ffd76a")
    wrapped_text(
        draw,
        (185, 2110),
        "The score continues into the next round. If your score passes 9999, the display stays at 9999.",
        font(32),
        INK,
        1250,
        7,
    )
    page_number(draw, 5)
    return page


def make_inside_cover_page() -> Image.Image:
    page = Image.new("RGB", PAGE_SIZE, CREAM)
    draw = ImageDraw.Draw(page)

    # The reference inside cover is intentionally quiet, with one small feature
    # badge low on the page and the cartridge note along the bottom edge.
    card_left, card_top, card_right, card_bottom = 675, 1690, 975, 2160
    draw.rounded_rectangle(
        (card_left, card_top, card_right, card_bottom),
        radius=24,
        outline=INK,
        width=4,
    )
    card_center = (card_left + card_right) // 2

    octopus_path = ART_DIR / "inside-cover-octopus-v1.png"
    octopus = Image.open(octopus_path).convert("RGBA")
    alpha_bbox = octopus.getchannel("A").getbbox()
    if alpha_bbox:
        octopus = octopus.crop(alpha_bbox)
    scale = min(112 / octopus.width, 112 / octopus.height, 1.0)
    octopus = octopus.resize(
        (round(octopus.width * scale), round(octopus.height * scale)),
        Image.Resampling.LANCZOS,
    )
    page.paste(
        octopus,
        (
            card_center - octopus.width // 2,
            card_top + 34,
        ),
        octopus,
    )

    def card_text(y: int, text: str, typeface: ImageFont.FreeTypeFont) -> None:
        box = draw.textbbox((0, 0), text, font=typeface)
        width = box[2] - box[0]
        draw.text((card_center - width // 2 - box[0], y), text, font=typeface, fill=INK)

    card_text(1840, "THANK YOU", font(40, bold=True))
    card_text(1910, "Thanks for trying", font(31))
    card_text(1955, "out this game.", font(31))
    card_text(2010, "Let me know how I", font(31))
    card_text(2055, "can make it better.", font(31))

    note = (
        "NOTE: Always turn the console power switch off when inserting or "
        "removing an ATARI® Game Program™ cartridge. This will protect the "
        "electronic components and prolong the life of your ATARI® Video "
        "Computer System™ game."
    )
    wrapped_text(draw, (105, 2240), note, font(FONT_BODY_SIZE), INK, 1440, 5)

    centered_text(
        draw,
        2420,
        "MANUAL, PROGRAM, AND AUDIOVISUAL © 2026 AARON NEWCOMB",
        font(27, bold=True),
        INK,
    )
    return page


def make_contents_page() -> Image.Image:
    page, draw = make_interior_page()
    centered_text(draw, 245, "TABLE OF CONTENTS", ImageFont.truetype(str(FONT_SECTION), 78), BLUE)

    entries = [
        ("1.  THE GAME BEGINS", "1"),
        ("2.  GAME PLAY", "2"),
        ("3.  USING THE CONTROLLERS", "3"),
        ("4.  CONSOLE CONTROLS", "4"),
        ("5.  SCORING", "5"),
    ]
    y = 500
    row_face = ImageFont.truetype(str(FONT_SECTION), 43)
    number_face = font(43, bold=True)
    for label, number in entries:
        draw.text((210, y), label, font=row_face, fill=BLUE)
        box = draw.textbbox((0, 0), number, font=number_face)
        draw.text((1410 - (box[2] - box[0]), y), number, font=number_face, fill=INK)
        draw.line((210, y + 72, 1440, y + 72), fill=INK, width=2)
        y += 190

    return page


def make_cover() -> Image.Image:
    page = Image.new("RGB", PAGE_SIZE, CREAM)
    draw = ImageDraw.Draw(page)

    paste_centered_asset(
        page,
        LAYOUT_ART_DIR / "cover-title.png",
        (PAGE_SIZE[0] // 2, 151),
        (1320, 166),
    )
    instruction_banner(page, draw, 258)

    art = Image.open(ART_DIR / "cover-illustration-v4.png").convert("RGB")
    art_box = (200, 390, 1450, 2265)
    art = art.resize(
        (art_box[2] - art_box[0], art_box[3] - art_box[1]),
        Image.Resampling.LANCZOS,
    )
    page.paste(art, art_box[:2])
    draw.rectangle(art_box, outline=ORANGE, width=7)

    baseline = 2325
    draw.text((205, baseline), "9 SURVIVAL\nLEVELS", font=font(42, bold=True), fill=ORANGE, spacing=14)

    right_x = 1200
    draw.text((right_x, baseline + 25), "1 PLAYER", font=font(44, bold=True), fill=ORANGE)

    draw.text((1334, 2198), "AG-0001", font=font(27, bold=True), fill=CREAM)
    return page


def save_outputs() -> None:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    cover = make_cover()
    cover_path = PAGES_DIR / "01-cover.png"
    cover.save(cover_path, optimize=True)
    cover_v2_path = PAGES_DIR / "01-cover-v2.png"
    cover.save(cover_v2_path, optimize=True)

    preview = cover.resize((660, 1020), Image.Resampling.LANCZOS)
    preview.save(PREVIEWS_DIR / "01-cover-preview.jpg", quality=88, optimize=True)

    inside_cover = make_inside_cover_page()
    inside_cover_path = PAGES_DIR / "02-inside-cover.png"
    inside_cover.save(inside_cover_path, optimize=True)
    inside_cover.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "02-inside-cover-preview.jpg", quality=88, optimize=True
    )

    contents = make_contents_page()
    contents_path = PAGES_DIR / "03-contents.png"
    contents.save(contents_path, optimize=True)
    contents_v2_path = PAGES_DIR / "03-contents-v2.png"
    contents.save(contents_v2_path, optimize=True)
    contents.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "03-contents-preview.jpg", quality=88, optimize=True
    )

    survival_orders = make_survival_orders_page()
    survival_path = PAGES_DIR / "04-game-begins.png"
    survival_orders.save(survival_path, optimize=True)

    survival_preview = survival_orders.resize((660, 1020), Image.Resampling.LANCZOS)
    survival_preview.save(
        PREVIEWS_DIR / "04-game-begins-preview.jpg",
        quality=88,
        optimize=True,
    )

    game_play = make_game_play_page()
    game_play_path = PAGES_DIR / "05-game-play.png"
    game_play.save(game_play_path, optimize=True)
    game_play.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "05-game-play-preview.jpg", quality=88, optimize=True
    )

    game_play_obstacles = make_game_play_obstacles_page()
    obstacles_path = PAGES_DIR / "06-game-play-continued.png"
    game_play_obstacles.save(obstacles_path, optimize=True)
    obstacles_v2_path = PAGES_DIR / "06-game-play-continued-v2.png"
    game_play_obstacles.save(obstacles_v2_path, optimize=True)
    game_play_obstacles.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "06-game-play-continued-preview.jpg", quality=88, optimize=True
    )

    level2_screen = make_level2_screenshot()
    level2_screen.save(ART_DIR / "gameplay-level2-v1.png", optimize=True)

    controller_controls = make_controller_controls_page()
    controller_path = PAGES_DIR / "07-controllers-and-console.png"
    controller_controls.save(controller_path, optimize=True)
    controller_controls.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "07-controllers-and-console-preview.jpg", quality=88, optimize=True
    )
    controller_v8_path = PAGES_DIR / "07-controllers-and-console-v8.png"
    controller_controls.save(controller_v8_path, optimize=True)
    controller_controls.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "07-controllers-and-console-v8-preview.jpg",
        quality=88,
        optimize=True,
    )
    controller_v9_path = PAGES_DIR / "07-controllers-and-console-v9.png"
    controller_controls.save(controller_v9_path, optimize=True)
    controller_controls.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "07-controllers-and-console-v9-preview.jpg",
        quality=88,
        optimize=True,
    )
    controller_v10_path = PAGES_DIR / "07-controllers-and-console-v10.png"
    controller_controls.save(controller_v10_path, optimize=True)
    controller_controls.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "07-controllers-and-console-v10-preview.jpg",
        quality=88,
        optimize=True,
    )

    scoring = make_scoring_page()
    scoring_path = PAGES_DIR / "08-scoring.png"
    scoring.save(scoring_path, optimize=True)
    scoring.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "08-scoring-preview.jpg", quality=88, optimize=True
    )
    scoring_v1_path = PAGES_DIR / "08-scoring-v1.png"
    scoring.save(scoring_v1_path, optimize=True)
    scoring.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "08-scoring-v1-preview.jpg", quality=88, optimize=True
    )
    scoring_v2_path = PAGES_DIR / "08-scoring-v2.png"
    scoring.save(scoring_v2_path, optimize=True)
    scoring.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "08-scoring-v2-preview.jpg", quality=88, optimize=True
    )
    scoring_v3_path = PAGES_DIR / "08-scoring-v3.png"
    scoring.save(scoring_v3_path, optimize=True)
    scoring.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "08-scoring-v3-preview.jpg", quality=88, optimize=True
    )
    scoring_v4_path = PAGES_DIR / "08-scoring-v4.png"
    scoring.save(scoring_v4_path, optimize=True)
    scoring.resize((660, 1020), Image.Resampling.LANCZOS).save(
        PREVIEWS_DIR / "08-scoring-v4-preview.jpg", quality=88, optimize=True
    )

    # During staged approval this PDF contains only approved or review-ready pages.
    cover.save(
        DOCS_DIR / "manual-draft.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls],
        resolution=300.0,
    )
    cover.save(
        DOCS_DIR / "manual-draft-controls-v8.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls],
        resolution=300.0,
    )
    cover.save(
        DOCS_DIR / "manual-draft-controls-v9.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls],
        resolution=300.0,
    )
    cover.save(
        DOCS_DIR / "manual-draft-scoring-v1.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls, scoring],
        resolution=300.0,
    )
    cover.save(
        DOCS_DIR / "manual-draft-scoring-v2.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls, scoring],
        resolution=300.0,
    )
    cover.save(
        DOCS_DIR / "manual-draft-scoring-v3.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls, scoring],
        resolution=300.0,
    )
    cover.save(
        DOCS_DIR / "manual-draft-final-v1.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls, scoring],
        resolution=300.0,
    )
    cover.save(
        DOCS_DIR / "octo-game-manual.pdf",
        "PDF",
        save_all=True,
        append_images=[inside_cover, contents, survival_orders, game_play, game_play_obstacles, controller_controls, scoring],
        resolution=300.0,
    )


if __name__ == "__main__":
    save_outputs()
