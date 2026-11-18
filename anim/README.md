# 2D Animation Studio

Programmatic 2D animation in Python: draw frames with Pillow, encode to MP4 with ffmpeg.

## Install

```bash
pip install pillow imageio-ffmpeg
```

## Render the demo

```bash
python3 anim/render.py demo_scene -o out/demo.mp4
```

## CLI

```bash
python3 anim/render.py <scene_name> [-o out/file.mp4] [--crf 18]
```

Code lives in `anim/engine.py` (Scene class, easing, helpers),
`anim/demo_scene.py` (fully rendered demo: bouncing ball, sun, clouds, animated
title), and `anim/render.py` (CLI).
