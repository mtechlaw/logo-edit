from pathlib import Path
import argparse

from processor import batch_process, zip_outputs

parser = argparse.ArgumentParser(description="Batch brand logos into white-circle PNG badges.")
parser.add_argument("input_dir", help="Folder containing source logos")
parser.add_argument("output_dir", help="Folder for branded outputs")
parser.add_argument("--threshold", type=int, default=245, help="Threshold for removing near-white background")
parser.add_argument("--logo-scale", type=float, default=0.62, help="Logo size relative to canvas")
parser.add_argument("--circle-margin", type=int, default=12, help="Margin around white circle")
parser.add_argument("--zip", action="store_true", help="Also create a ZIP file of all PNG outputs")

args = parser.parse_args()

outputs = batch_process(
    Path(args.input_dir),
    Path(args.output_dir),
    threshold=args.threshold,
    logo_scale=args.logo_scale,
    circle_margin=args.circle_margin,
)

print(f"Created {len(outputs)} file(s).")
if args.zip:
    zip_path = Path(args.output_dir) / "branded_logos.zip"
    zip_outputs(Path(args.output_dir), zip_path)
    print(f"ZIP created: {zip_path}")
