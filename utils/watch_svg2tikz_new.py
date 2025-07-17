from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from pathlib import Path
import subprocess
import time
import os

SVG_DIR = Path("svg_src")
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
        tmp_figonly = OUT_DIR / (svg_path.stem + "_tmp_figonly.tex")
        tmp_codeonly = OUT_DIR / (svg_path.stem + "_tmp_codeonly.tex")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] svg2tikz: Converting {svg_path} -> {out_path}")

        try:
            # Run svg2tikz with --figonly
            subprocess.run([
                "svg2tikz",
                str(svg_path),
                "--output", str(tmp_figonly),
                "-t", "raw",
                "--markings", "interpret",
                "--arrow", "stealth",
                "--codeoutput", "figonly"
            ], check=True)

            # Run svg2tikz with --codeonly
            subprocess.run([
                "svg2tikz",
                str(svg_path),
                "--output", str(tmp_codeonly),
                "-t", "raw",
                "--markings", "interpret",
                "--arrow", "stealth",
                "--codeoutput", "codeonly"
            ], check=True)

            # Extract color definitions
            with open(tmp_figonly, "r") as f:
                fig_lines = f.readlines()
            color_defs = [line for line in fig_lines if line.strip().startswith(r"\definecolor")]

            # Combine with codeonly output
            with open(tmp_codeonly, "r") as f:
                code_lines = f.readlines()

            with open(out_path, "w") as f:
                f.writelines(color_defs + ["\n"] + code_lines)

        except subprocess.CalledProcessError as e:
            print(f"[svg2tikz] Error: {e}")

        finally:
            # Clean up temporary files
            if tmp_figonly.exists():
                tmp_figonly.unlink()
            if tmp_codeonly.exists():
                tmp_codeonly.unlink()

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
