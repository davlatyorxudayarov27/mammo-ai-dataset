# GPU Acceleration Setup

YOLO inference jarayonini **10-20x tezroq** qilish uchun NVIDIA GPU + CUDA torch
o'rnatiladi. CPU'da bitta mammografiya ~6s, GPU'da <0.5s.

---

## 1. Talablar

- **NVIDIA GPU** (Compute Capability ≥ 6.0 — RTX 20/30/40 seriyasi, GTX 1060+, Tesla T4/V100/A100)
- **NVIDIA drayveri** (Studio yoki Game Ready, ≥ 535)
- Diskda kamida **3-4 GB bo'sh joy** (CUDA torch wheel'lari katta)

NVIDIA kartangizni tekshirish:

```cmd
nvidia-smi
```

Drayver versiyasi va CUDA version ko'rinadi (e.g. `CUDA Version: 12.4`).
**12.x bo'lsa → cu121 ishlatamiz. 11.8 bo'lsa → cu118.**

---

## 2. CPU torchni o'chirib, CUDA torch o'rnatish

`run.bat` allaqachon CPU torch o'rnatgan. Almashtirish uchun:

```cmd
cd d:\Project_MAMOGRAF\plan_project
.venv\Scripts\activate.bat

REM Eski CPU torchni olib tashlash
pip uninstall -y torch torchvision

REM CUDA 12.1 uchun
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

REM Yoki CUDA 11.8 uchun
REM pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

Yuklab olish ~2.5 GB. Bir necha daqiqa kutiladi.

---

## 3. Tekshirish

```cmd
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Kutilgan natija:

```
CUDA available: True
Device: NVIDIA GeForce RTX 4070
```

Yoki viewer brauzerda ochilganda **🤖 AI tahlil** tugmasi tooltip'ida
`AI tahlil (NVIDIA GeForce RTX 4070)` ko'rinadi. `(CPU)` bo'lsa CUDA
ishlamayapti.

---

## 4. Inference benchmark

Bir xil DICOM ustida yolo11_l modelini ishga tushirib solishtiring:

| Qurilma | Birinchi (cold) | Keyingi (warm) |
|---|---:|---:|
| CPU (Ryzen/i7) | 6-12 s | 5-8 s |
| GPU (RTX 3060) | 1.5-3 s | 0.3-0.6 s |
| GPU (RTX 4090) | 0.8-1.5 s | 0.15-0.3 s |

Cold = model birinchi marta yuklanmoqda. Warm = keyingi inference (model
xotirada).

---

## 5. GPU memory cheklovi

`yolo11_x.pt` (109MB) yuklash ~2 GB VRAM ishlatadi. Agar `CUDA out of memory`
xato chiqsa:

1. Brauzer + boshqa GPU dasturlarini yoping
2. `imgsz` ni kamaytiring: `1024 → 832 → 640`
3. Kichikroq modelga o'ting: `yolo11_x → yolo11_l → yolo11_m`

---

## 6. Jamoa muhitida (production)

Server CPU bilan ishlasa, GPU'li alohida machine'da inference worker
ko'tarib, `/api/inference/run` ni shu workerga proxy qilish mumkin
(Caddy/nginx). Kichik shifoxonalar uchun bitta GPU'li server
(50-200 inference/kun) bemalol etarli.

---

## 7. Troubleshooting

| Xato | Sabab + yechim |
|---|---|
| `CUDA driver version is insufficient` | Drayverni yangilang (≥ 535) |
| `CUDA capability sm_XX is not supported` | Eskiroq GPU — eskiroq torch versiyasi (`pip install "torch<2.0"`) |
| `cuDNN error` | `pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu121` |
| `OutOfMemoryError` | Yuqoridagi 5-bo'limni ko'ring |

---

## 8. CPU rejimga qaytish

```cmd
pip uninstall -y torch torchvision
pip install -r requirements.txt
```

Server qayta ishga tushiriladi, `/api/inference/status` `device: cpu` ni
qaytaradi.
