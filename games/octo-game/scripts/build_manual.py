#!/usr/bin/env python3
"""Generate the graphical Octo Game manual pages and downloadable PDF."""

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PAGES = DOCS / "manual-pages"
PDF = DOCS / "manual.pdf"
TITLE_SCREEN = DOCS / "assets" / "title-screen.png"

WIDTH, HEIGHT = 1275, 1650
BLACK = "#050505"
CORAL = "#df6263"
WHITE = "#f3f3f0"
TEAL = "#35a17f"
BLUE = "#6874ec"
BLUE_DARK = "#3f49b8"
YELLOW = "#fff43c"
RED = "#b3171d"
GRAY = "#b8b8b8"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size)


TITLE = font(76, True)
HEADING = font(48, True)
SUBHEAD = font(32, True)
BODY = font(29)
SMALL = font(23)


def new_page(number: int, heading: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    draw = ImageDraw.Draw(image)
    draw.rectangle((35, 35, WIDTH - 35, HEIGHT - 35), outline=CORAL, width=18)
    if heading:
        draw.text((90, 85), heading.upper(), font=HEADING, fill=WHITE)
        draw.rectangle((90, 155, WIDTH - 90, 164), fill=CORAL)
    draw.text((WIDTH - 155, HEIGHT - 92), f"{number:02d}", font=SMALL, fill=CORAL)
    return image, draw


def centered(draw: ImageDraw.ImageDraw, y: int, text: str, face, color: str) -> None:
    box = draw.textbbox((0, 0), text, font=face)
    draw.text(((WIDTH - (box[2] - box[0])) // 2, y), text, font=face, fill=color)


def paragraph(draw: ImageDraw.ImageDraw, x: int, y: int, text: str,
              width: int = 53, color: str = WHITE, face=BODY,
              spacing: int = 14) -> int:
    lines = []
    for source_line in text.splitlines():
        lines.extend(wrap(source_line, width=width) or [""])
    draw.multiline_text((x, y), "\n".join(lines), font=face, fill=color,
                        spacing=spacing)
    return y + len(lines) * (face.size + spacing)


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
          title: str, color: str = CORAL) -> None:
    draw.rounded_rectangle(box, radius=18, outline=color, width=7)
    draw.rectangle((box[0] + 18, box[1] - 20, box[0] + 330, box[1] + 27), fill=BLACK)
    draw.text((box[0] + 30, box[1] - 19), title.upper(), font=SUBHEAD, fill=color)


def octopus(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int = 18) -> None:
    pixels = [
        "..####..",
        ".######.",
        "########",
        "##.##.##",
        "########",
        ".######.",
        "..####..",
        ".##..##.",
        "##.##.##",
    ]
    for row, bits in enumerate(pixels):
        for column, bit in enumerate(bits):
            if bit == "#":
                draw.rectangle((x + column * scale, y + row * scale,
                                x + (column + 1) * scale - 2,
                                y + (row + 1) * scale - 2), fill=TEAL)


def light(draw: ImageDraw.ImageDraw, x: int, y: int, active: str) -> None:
    draw.rounded_rectangle((x, y, x + 260, y + 510), radius=28,
                           fill="#202020", outline=WHITE, width=6)
    colors = [(RED, "RED"), (YELLOW, "WAIT"), (TEAL, "GREEN")]
    for index, (color, name) in enumerate(colors):
        cy = y + 92 + index * 150
        fill = color if name == active else "#343434"
        draw.ellipse((x + 75, cy - 62, x + 185, cy + 48), fill=fill,
                     outline=WHITE, width=4)


def page_cover() -> Image.Image:
    image, draw = new_page(1, "")
    title_screen = Image.open(TITLE_SCREEN).convert("RGB")
    title_screen = title_screen.resize((1080, 810), Image.Resampling.NEAREST)
    image.paste(title_screen, ((WIDTH - title_screen.width) // 2, 150))
    centered(draw, 1060, "ATARI 2600", HEADING, YELLOW)
    centered(draw, 1140, "INSTRUCTION MANUAL", SUBHEAD, WHITE)
    centered(draw, 1370, "DESIGNED BY AARON NEWCOMB", SMALL, CORAL)
    return image


def page_challenge() -> Image.Image:
    image, draw = new_page(2, "The Challenge")
    octopus(draw, 110, 260, 16)
    draw.line((310, 335, 1050, 335), fill=BLUE, width=18)
    draw.polygon(((1050, 335), (990, 295), (990, 375)), fill=BLUE)
    centered(draw, 470, "REACH THE FINISH LINE", SUBHEAD, YELLOW)
    y = paragraph(draw, 120, 565,
        "Nine rounds stand between your octopus and survival. Advance only "
        "while the light is green. When it turns red, release the joystick "
        "and remain perfectly still.", width=58)
    panel(draw, (105, y + 70, WIDTH - 105, y + 390), "Your mission", TEAL)
    paragraph(draw, 155, y + 145,
        "Reach the top of the arena before the timer reaches 000. Complete "
        "all nine levels to see the final survival screen.", width=53,
        color=WHITE)
    return image


def page_controls() -> Image.Image:
    image, draw = new_page(3, "Controller")
    cx, cy = 380, 500
    draw.rounded_rectangle((170, 280, 590, 760), radius=70, fill="#282828",
                           outline=WHITE, width=8)
    draw.ellipse((255, 365, 505, 615), fill="#151515", outline=GRAY, width=7)
    draw.line((cx, cy, cx, 350), fill=WHITE, width=32)
    draw.ellipse((325, 300, 435, 410), fill=BLACK, outline=WHITE, width=6)
    draw.ellipse((635, 395, 845, 605), fill=CORAL, outline=WHITE, width=8)
    draw.text((680, 470), "FIRE", font=SMALL, fill=BLACK)
    draw.text((270, 800), "JOYSTICK", font=SUBHEAD, fill=TEAL)
    draw.text((660, 800), "BUTTON", font=SUBHEAD, fill=CORAL)
    panel(draw, (105, 930, WIDTH - 105, 1430), "Controls", CORAL)
    paragraph(draw, 155, 1005,
        "UP     Move toward the finish during green lights.\n"
        "LEFT   Steer left around obstacles.\n"
        "RIGHT  Steer right around obstacles.\n"
        "FIRE   Start or restart the game.\n"
        "RESET  Return to the title screen.", width=52, spacing=22)
    return image


def page_lights() -> Image.Image:
    image, draw = new_page(4, "Red Light, Green Light")
    light(draw, 165, 255, "GREEN")
    light(draw, 850, 255, "RED")
    centered(draw, 800, "GREEN: MOVE", SUBHEAD, TEAL)
    centered(draw, 875, "RED: FREEZE", SUBHEAD, CORAL)
    panel(draw, (105, 1010, WIDTH - 105, 1420), "Warning", CORAL)
    paragraph(draw, 155, 1080,
        "Any joystick direction during a red light causes immediate "
        "elimination. Light changes are randomized, and each new level "
        "shortens the reaction time.", width=54)
    return image


def page_scoring() -> Image.Image:
    image, draw = new_page(5, "Obstacles and Scoring")
    draw.rectangle((120, 245, 310, 570), fill="#6c3f1f")
    draw.ellipse((70, 175, 360, 375), fill=TEAL)
    draw.ellipse((470, 310, 710, 520), fill=GRAY, outline=WHITE, width=5)
    draw.ellipse((790, 250, 1070, 500), fill="#8f8f8f", outline=WHITE, width=5)
    centered(draw, 610, "LEVELS 2, 4, 6 AND 8", SUBHEAD, YELLOW)
    paragraph(draw, 120, 700,
        "A tree and two boulders block the arena on alternating levels. Their "
        "positions change at the start of every round. Steer around them while "
        "the light is green.", width=59)
    panel(draw, (105, 1000, WIDTH - 105, 1425), "Scoring", BLUE)
    paragraph(draw, 155, 1070,
        "LEVEL CLEAR  = 100 POINTS\n"
        "+ TIMER BONUS = EVERY POINT REMAINING\n"
        "MAXIMUM SCORE = 9999", width=54, color=WHITE, spacing=24)
    return image


def page_tips() -> Image.Image:
    image, draw = new_page(6, "Survival Tips")
    tips = [
        "Release the joystick before every red light.",
        "Plan a clear path before moving around obstacles.",
        "Short taps provide better control than long holds.",
        "Move quickly to preserve more timer bonus points.",
        "Expect faster light changes on later levels.",
    ]
    y = 245
    for index, tip in enumerate(tips, start=1):
        draw.rectangle((115, y, 175, y + 60), fill=CORAL)
        draw.text((132, y + 10), str(index), font=SMALL, fill=BLACK)
        paragraph(draw, 215, y + 5, tip, width=49)
        y += 150
    octopus(draw, 555, 1070, 18)
    centered(draw, 1290, "CAN YOU SURVIVE ALL NINE LEVELS?", SUBHEAD, YELLOW)
    centered(draw, 1410, "DESIGNED AND PROGRAMMED BY", SMALL, WHITE)
    centered(draw, 1450, "AARON NEWCOMB  |  2026", SMALL, CORAL)
    return image


def main() -> int:
    PAGES.mkdir(parents=True, exist_ok=True)
    pages = [page_cover(), page_challenge(), page_controls(), page_lights(),
             page_scoring(), page_tips()]
    names = ["01-cover.png", "02-challenge.png", "03-controls.png",
             "04-lights.png", "05-scoring.png", "06-tips.png"]
    for image, name in zip(pages, names):
        image.save(PAGES / name, optimize=True)
    pages[0].save(PDF, "PDF", resolution=150.0, save_all=True,
                  append_images=pages[1:])
    print(f"generated {len(pages)} manual pages and {PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
