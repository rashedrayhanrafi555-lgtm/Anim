#!/usr/bin/env python3
import argparse
import importlib
import os
import sys


def _import(scene):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    for name in (scene, f"anim.{scene}"):
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError:
            continue
    raise ModuleNotFoundError(f"scene module not found: {scene}")


def main():
    ap = argparse.ArgumentParser(description="Render a Scene to MP4")
    ap.add_argument("scene", help="scene module, e.g. demo_scene")
    ap.add_argument("-o", "--out", default=None, help="output mp4 path")
    ap.add_argument("--crf", type=int, default=18, help="quality (lower=better)")
    args = ap.parse_args()

    name = args.scene[:-3] if args.scene.endswith(".py") else args.scene
    mod = _import(name)
    candidates = [getattr(mod, n) for n in dir(mod)
                  if isinstance(getattr(mod, n), type) and n != "Scene" and hasattr(getattr(mod, n), "draw")]
    scene = candidates[0]()
    scene.setup()
    scene.render(args.out or f"out/{name}.mp4", crf=args.crf)


if __name__ == "__main__":
    main()
