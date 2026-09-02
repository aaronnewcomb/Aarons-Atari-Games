# Octo Game Instruction Manual

[Download the complete PDF manual](manual.pdf)

The manual is presented below one page at a time. Each page image and the PDF
are generated from the same artwork by `scripts/build_manual.py`.

The cover uses the verified v0.3.0 title-screen capture stored in
`docs/assets/title-screen.png`.

## Page 1: Cover

![Octo Game manual cover](manual-pages/01-cover.png)

## Page 2: The Challenge

![The Octo Game challenge](manual-pages/02-challenge.png)

## Page 3: Controller

![Controller instructions](manual-pages/03-controls.png)

## Page 4: Red Light, Green Light

![Red and green light rules](manual-pages/04-lights.png)

## Page 5: Obstacles and Scoring

![Obstacle and scoring instructions](manual-pages/05-scoring.png)

## Page 6: Survival Tips and Credits

![Survival tips and credits](manual-pages/06-tips.png)

## Rebuilding the manual

Install Pillow and run:

```sh
python3 -m pip install -r requirements-manual.txt
make manual
```
