from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from pathlib import Path
import subprocess
import time
import os

SVG_DIR = Path("svg_src")
print(SVG_DIR)
OUT_DIR = Path("figs")

DEBOUNCE_SECONDS = 1.0  # Minimum delay between repeated processing of the same file

class SVGHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_run = {}

    def should_process(self, svg_path: Path) -> bool:
        now = time.time()
        last = self.last_run.get(svg_path, 0)
        if now - last > DEBOUNCE_SECONDS:
            self.last_run[svg_path] = now
            return True
        return False

    def on_any_event(self, event):
        if event.is_directory or not event.src_path.endswith(".svg"):
            return

        svg_path = Path(event.src_path)
        if self.should_process(svg_path):
            self.convert_svg(svg_path)
    def convert_svg(self, svg_path):
        out_path = OUT_DIR / (svg_path.stem + ".tex")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] svg2tikz: Converting {svg_path} -> {out_path}")
        try:
            subprocess.run([
                "svg2tikz",
                str(svg_path),
                "--output", str(out_path),
                "-t", "raw",
                "--codeoutput", "figonly"
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[svg2tikz] Error: {e}")

if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    observer = Observer()
    handler = SVGHandler()
    observer.schedule(handler, str(SVG_DIR), recursive=False)
    print(f"Watching {SVG_DIR} for .svg changes...")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
