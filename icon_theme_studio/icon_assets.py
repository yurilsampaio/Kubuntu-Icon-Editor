import argparse
from pathlib import Path
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

def render_png(source: Path, target: Path):
    image=QImage(QSize(256,256),QImage.Format.Format_ARGB32); image.fill(0)
    painter=QPainter(image); renderer=QSvgRenderer(str(source))
    if renderer.isValid(): renderer.render(painter)
    painter.end(); target.parent.mkdir(parents=True,exist_ok=True)
    if not image.save(str(target),"PNG"): raise OSError(f"Não foi possível salvar {target}")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--output",required=True); args=parser.parse_args()
    render_png(Path(__file__).with_name("icon.svg"),Path(args.output))
