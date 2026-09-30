# ReviseTranslate • Precision Medical PDF Translation Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-slate.svg)](https://www.python.org/)
[![Engine: PyMuPDF](https://img.shields.io/badge/Engine-PyMuPDF-059669.svg)](https://pymupdf.readthedocs.io/)
[![LLM: Together AI](https://img.shields.io/badge/AI-Llama--3.3--70B-1e293b.svg)](https://www.together.ai/)
[![Design: Nordic Slate](https://img.shields.io/badge/Design-Nordic%20Slate-0f172a.svg)](https://github.com/artemhrebeniuk)

An autonomous, layout-preserving clinical and laboratory PDF translation engine with a synchronized dual-source spatial inspector. Built with PyMuPDF and powered by **Together AI** (`meta-llama/Llama-3.3-70B-Instruct-Turbo`).

---

## Key Features

- **Non-Destructive Layer Inscription**: Replaces textual content while preserving 100% of underlying raster graphics, vector paths, laboratory tables, and official stamps.
- **Doctor Signatures & Official Seals Intact**: Selective redaction masking (`PDF_REDACT_IMAGE_NONE`) guarantees that blue-ink doctor signatures and accreditation stamps are never erased or compromised.
- **Autonomous Clinical AI Translation**: Integrated with **Together AI** utilizing `meta-llama/Llama-3.3-70B-Instruct-Turbo` for context-aware medical and biochemical laboratory terminology.
- **Dual-Source Synchronized Spatial Inspector**: Side-by-side comparison of baseline original (Doc A) and candidate translation (Doc B) with synchronous pan and zoom.
- **Parallel Document Rotation (0°, 90°, 180°, 270°)**: Simultaneously rotates both documents to allow effortless horizontal reading and cross-inspection of vertical margin text (e.g. MOH licenses, laboratory accreditations, and clinical advisories).
- **Nordic Slate & Forest Emerald Design System**: Clean, zero-emoji, Scandinavian minimalist interface with Gabarito & Hanken Grotesk typography and subtle dot-matrix background.

---

## Architecture Overview

```
ReviseTranslate
├── app.py                     # Flask web server & REST endpoints
├── engine.py                  # PyMuPDF non-destructive engine + Together AI LLM
├── samples/                   # Reference clinical documents (DILA Lab Report)
├── static/
│   ├── index.html             # Minimalist dual-inspector interface
│   ├── style.css              # Nordic Slate & Forest Emerald design tokens
│   └── app.js                 # Synchronous canvas rotation & viewer controller
├── requirements.txt           # Python dependencies
└── .env.example               # Environment variables template
```

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/artemhrebeniuk/TranslatePDF.git
cd TranslatePDF
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and insert your Together AI key:
```bash
cp .env.example .env
```

```ini
TOGETHER_API_KEY=your_together_ai_api_key_here
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
PORT=5055
HOST=0.0.0.0
```

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5055/
```

---

## Supported Workflows

- **Ukrainian Medical Lab Reports (UKR ➔ EN)**: Complete blood panels (CBC 35 parameters), ferritin, vitamin D (25-OH), biochemical indices, reference intervals, units of measurement, clinical notes, and physician authorizations.
- **Dynamic Bounding Box Scaling**: Automatic shrink-to-fit font scaling prevents text overflow or truncation within strict table cell boundaries.
- **Direct PDF Export**: Immediate download of the publication-ready, translated vector PDF.

---

## Author

**Artem Hrebeniuk**  
GitHub: [@artemhrebeniuk](https://github.com/artemhrebeniuk)

---

## License

This project is licensed under the MIT License.
