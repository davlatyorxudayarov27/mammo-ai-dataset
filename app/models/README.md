# AI Model weights

Place YOLOv8 / YOLOv11 mammography weight files (`.pt`) in this directory.
The viewer auto-detects them at startup and exposes them in the **🤖 AI tahlil**
toolbar dropdown.

## digitaleye-mammography (cbddobvyz)

Source: https://github.com/cbddobvyz/digitaleye-mammography
License: **GPL v3** — read carefully before commercial use.

The project ships pre-trained YOLOv8 and YOLOv11 mass-detection weights via
GitHub Releases. Download the `.pt` file you want and drop it here, e.g.:

```
app/models/yolov8x_mass.pt
app/models/yolov11x_mass.pt
```

Restart the server after adding/removing weights.

## Custom weights

Any Ultralytics-compatible YOLO `.pt` file works. Class names are read from
the model itself (`model.names`). For binary mass classifiers, classes
typically map to `BI-RADS 1-2` (benign) and `BI-RADS 4-5` (suspicious).

## Inference parameters

The `/api/inference/run` endpoint accepts:
- `conf` — confidence threshold (default 0.25)
- `iou` — NMS IoU threshold (default 0.5)
- `imgsz` — input image size (default 1024)

DICOM is rendered to a max-2048px PNG with the current Window/Level applied
before inference.
