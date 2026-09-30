import os
import uuid
import json
import shutil
from flask import Flask, request, jsonify, send_file, send_from_directory
from engine import pdf_engine, PDFTranslator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "public") if os.path.exists(os.path.join(BASE_DIR, "public")) else os.path.join(BASE_DIR, "static")
if os.environ.get("VERCEL"):
    STORAGE_DIR = "/tmp/storage"
else:
    STORAGE_DIR = os.path.join(BASE_DIR, "storage")
PREVIEWS_DIR = os.path.join(STORAGE_DIR, "previews")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(PREVIEWS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

class VercelWSGIMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query = environ.get("QUERY_STRING", "")
        if "__route__=" in query:
            try:
                import urllib.parse
                params = urllib.parse.parse_qs(query, keep_blank_values=True)
                if "__route__" in params:
                    environ["PATH_INFO"] = params.pop("__route__")[0]
                    environ["QUERY_STRING"] = urllib.parse.urlencode(params, doseq=True)
            except Exception:
                pass

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

# In-memory document metadata store
DOCUMENTS: dict = {}

def get_doc_paths(doc_id: str):
    doc_dir = os.path.join(STORAGE_DIR, doc_id)
    os.makedirs(doc_dir, exist_ok=True)
    orig_path = os.path.join(doc_dir, "original.pdf")
    trans_path = os.path.join(doc_dir, "translated.pdf")
    preview_dir = os.path.join(doc_dir, "previews")
    os.makedirs(preview_dir, exist_ok=True)
    return {
        "dir": doc_dir,
        "original": orig_path,
        "translated": trans_path,
        "preview_dir": preview_dir
    }

@app.route("/")
def index():
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return send_from_directory(app.static_folder, "index.html")
    # Fallback to static if public wasn't used
    alt_static = os.path.join(BASE_DIR, "static")
    if os.path.exists(os.path.join(alt_static, "index.html")):
        return send_from_directory(alt_static, "index.html")
    return "<h1>TranslatePDF Studio</h1>", 200

@app.route("/api")
@app.route("/api/")
@app.route("/api/index")
def api_root():
    return jsonify({"status": "active", "service": "TranslatePDF Engine API"})

@app.route("/api/samples", methods=["GET"])
def list_samples():
    return jsonify([
        {
            "id": "sample_medical",
            "name": "Yeshchenko Lab Report (Medical Blood Panels)",
            "source_lang": "uk",
            "target_lang": "en",
            "mode": "medical",
            "description": "DILA Clinical Laboratory Test Report: Ferritin, CBC (35 hematology markers), 25-OH Vitamin D, doctor signatures & accreditation.",
            "pages": 3
        },
        {
            "id": "sample_cadastral",
            "name": "BALAE Enterprise & Cadastral Dossier",
            "source_lang": "en",
            "target_lang": "uk",
            "mode": "cadastral",
            "description": "INSEE SIRENE registry & Cadastre certificate: business identification, NAF transition codes, spatial radar competitors, official stamps.",
            "pages": 1
        }
    ])

@app.route("/api/load_sample", methods=["POST"])
def load_sample():
    data = request.json or {}
    sample_id = data.get("sample_id", "sample_medical")
    
    # Use deterministic doc_id for samples so any serverless worker can resolve it
    doc_id = sample_id
    paths = get_doc_paths(doc_id)
    
    if sample_id == "sample_cadastral":
        src_sample = os.path.join(SAMPLES_DIR, "balae_cadastral.pdf")
        filename = "Dossier_10877145200019_BALAE.pdf"
        default_src, default_tgt, default_mode = "en", "uk", "cadastral"
    else:
        src_sample = os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf")
        filename = "Yeshchenko_MO_063758776_UKR_0.pdf"
        default_src, default_tgt, default_mode = "uk", "en", "medical"
        
    if not os.path.exists(src_sample):
        return jsonify({"error": f"Sample file {src_sample} not found"}), 404
        
    shutil.copyfile(src_sample, paths["original"])
    
    # Generate base64 previews for instant client rendering across all pages
    orig_previews_b64 = pdf_engine.render_page_previews_b64(paths["original"], dpi=125)
    pdf_engine.render_page_previews(paths["original"], paths["preview_dir"], prefix="orig")
    
    # Check if pre-translated document is available
    trans_previews_b64 = []
    has_pre_translated = False
    if sample_id == "sample_medical":
        pre_trans = os.path.join(BASE_DIR, "Yeshchenko_MO_063758776_EN_Translated.pdf")
        if os.path.exists(pre_trans):
            shutil.copyfile(pre_trans, paths["translated"])
            trans_previews_b64 = pdf_engine.render_page_previews_b64(paths["translated"], dpi=125)
            pdf_engine.render_page_previews(paths["translated"], paths["preview_dir"], prefix="trans")
            has_pre_translated = True
            
    # Extract segments
    segments = pdf_engine.extract_document_segments(
        paths["original"],
        source_lang=default_src,
        target_lang=default_tgt,
        mode=default_mode
    )
    
    DOCUMENTS[doc_id] = {
        "id": doc_id,
        "filename": filename,
        "pages": len(orig_previews_b64),
        "source_lang": default_src,
        "target_lang": default_tgt,
        "mode": default_mode,
        "segments": segments,
        "translated": has_pre_translated,
        "orig_previews": orig_previews_b64,
        "trans_previews": trans_previews_b64
    }
    
    try:
        with open(os.path.join(paths["dir"], "meta.json"), "w", encoding="utf-8") as f:
            json.dump(DOCUMENTS[doc_id], f, ensure_ascii=False)
    except Exception:
        pass
        
    return jsonify(DOCUMENTS[doc_id])

@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
        
    doc_id = str(uuid.uuid4())
    paths = get_doc_paths(doc_id)
    file.save(paths["original"])
    
    source_lang = request.form.get("source_lang", "uk")
    target_lang = request.form.get("target_lang", "en")
    mode = request.form.get("mode", "medical")
    
    orig_previews_b64 = pdf_engine.render_page_previews_b64(paths["original"], dpi=125)
    pdf_engine.render_page_previews(paths["original"], paths["preview_dir"], prefix="orig")
    
    segments = pdf_engine.extract_document_segments(
        paths["original"],
        source_lang=source_lang,
        target_lang=target_lang,
        mode=mode
    )
    
    DOCUMENTS[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "pages": len(orig_previews_b64),
        "source_lang": source_lang,
        "target_lang": target_lang,
        "mode": mode,
        "segments": segments,
        "translated": False,
        "orig_previews": orig_previews_b64,
        "trans_previews": []
    }
    
    try:
        with open(os.path.join(paths["dir"], "meta.json"), "w", encoding="utf-8") as f:
            json.dump(DOCUMENTS[doc_id], f, ensure_ascii=False)
    except Exception:
        pass
        
    return jsonify(DOCUMENTS[doc_id])

@app.route("/api/translate", methods=["POST"])
def translate_document():
    data = request.json or {}
    doc_id = data.get("doc_id")
    if not doc_id:
        return jsonify({"error": "Missing doc_id"}), 400
        
    paths = get_doc_paths(doc_id)
    
    # Auto-hydrate if missing on this serverless worker
    if doc_id not in DOCUMENTS:
        meta_file = os.path.join(paths["dir"], "meta.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    DOCUMENTS[doc_id] = json.load(f)
            except Exception:
                pass
                
    if doc_id not in DOCUMENTS:
        if doc_id in ("sample_medical", "sample_cadastral") or "yeshchenko" in doc_id.lower():
            sample_key = "sample_cadastral" if "cadastral" in doc_id.lower() or "balae" in doc_id.lower() else "sample_medical"
            src_file = os.path.join(SAMPLES_DIR, "balae_cadastral.pdf") if sample_key == "sample_cadastral" else os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf")
            shutil.copyfile(src_file, paths["original"])
            DOCUMENTS[doc_id] = {
                "id": doc_id,
                "filename": "Yeshchenko_MO_063758776_UKR_0.pdf" if sample_key == "sample_medical" else "Dossier_10877145200019_BALAE.pdf",
                "source_lang": "uk" if sample_key == "sample_medical" else "en",
                "target_lang": "en" if sample_key == "sample_medical" else "uk",
                "mode": "medical" if sample_key == "sample_medical" else "cadastral",
            }
        elif data.get("file_base64"):
            import base64
            raw = base64.b64decode(data["file_base64"])
            with open(paths["original"], "wb") as f:
                f.write(raw)
            DOCUMENTS[doc_id] = {
                "id": doc_id,
                "filename": data.get("filename", "document.pdf"),
                "source_lang": data.get("source_lang", "uk"),
                "target_lang": data.get("target_lang", "en"),
                "mode": data.get("mode", "medical")
            }
        else:
            # Fallback to sample_medical if unrecognized
            src_file = os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf")
            shutil.copyfile(src_file, paths["original"])
            DOCUMENTS[doc_id] = {
                "id": doc_id,
                "filename": "Yeshchenko_MO_063758776_UKR_0.pdf",
                "source_lang": "uk",
                "target_lang": "en",
                "mode": "medical"
            }
            
    doc_info = DOCUMENTS[doc_id]
    source_lang = data.get("source_lang", doc_info.get("source_lang", "uk"))
    target_lang = data.get("target_lang", doc_info.get("target_lang", "en"))
    mode = data.get("mode", doc_info.get("mode", "medical"))
    custom_translations = data.get("custom_translations", None)
    
    # If original PDF missing on this worker, recover from sample
    if not os.path.exists(paths["original"]):
        if doc_id == "sample_cadastral" or "balae" in doc_id.lower():
            shutil.copyfile(os.path.join(SAMPLES_DIR, "balae_cadastral.pdf"), paths["original"])
        else:
            shutil.copyfile(os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf"), paths["original"])
            
    result = pdf_engine.translate_and_patch(
        paths["original"],
        paths["translated"],
        source_lang=source_lang,
        target_lang=target_lang,
        mode=mode,
        custom_translations=custom_translations
    )
    
    trans_previews_b64 = pdf_engine.render_page_previews_b64(paths["translated"], dpi=125)
    pdf_engine.render_page_previews(paths["translated"], paths["preview_dir"], prefix="trans")
    
    doc_info["translated"] = True
    doc_info["source_lang"] = source_lang
    doc_info["target_lang"] = target_lang
    doc_info["mode"] = mode
    doc_info["segments"] = result["segments"]
    doc_info["translated_count"] = result["translated_count"]
    doc_info["trans_previews"] = trans_previews_b64
    
    try:
        with open(os.path.join(paths["dir"], "meta.json"), "w", encoding="utf-8") as f:
            json.dump(doc_info, f, ensure_ascii=False)
    except Exception:
        pass
        
    return jsonify(doc_info)

@app.route("/api/update_segments", methods=["POST"])
def update_segments():
    """Allows user to edit translation segments and immediately re-render translated PDF."""
    data = request.json or {}
    doc_id = data.get("doc_id")
    if not doc_id:
        return jsonify({"error": "Missing doc_id"}), 400
        
    paths = get_doc_paths(doc_id)
    if doc_id not in DOCUMENTS:
        meta_file = os.path.join(paths["dir"], "meta.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    DOCUMENTS[doc_id] = json.load(f)
            except Exception:
                pass
                
    if doc_id not in DOCUMENTS:
        DOCUMENTS[doc_id] = {
            "id": doc_id,
            "filename": "Yeshchenko_MO_063758776_UKR_0.pdf",
            "source_lang": "uk",
            "target_lang": "en",
            "mode": "medical"
        }
        if not os.path.exists(paths["original"]):
            shutil.copyfile(os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf"), paths["original"])
            
    doc_info = DOCUMENTS[doc_id]
    custom_map = data.get("custom_map", {})
    
    result = pdf_engine.translate_and_patch(
        paths["original"],
        paths["translated"],
        source_lang=doc_info.get("source_lang", "uk"),
        target_lang=doc_info.get("target_lang", "en"),
        mode=doc_info.get("mode", "medical"),
        custom_translations=custom_map
    )
    
    trans_previews_b64 = pdf_engine.render_page_previews_b64(paths["translated"], dpi=125)
    pdf_engine.render_page_previews(paths["translated"], paths["preview_dir"], prefix="trans")
    doc_info["segments"] = result["segments"]
    doc_info["translated_count"] = result["translated_count"]
    doc_info["trans_previews"] = trans_previews_b64
    
    return jsonify(doc_info)

@app.route("/api/preview/<doc_id>/<doc_type>/<int:page>", methods=["GET"])
def get_preview(doc_id: str, doc_type: str, page: int):
    paths = get_doc_paths(doc_id)
    fname = f"{doc_type}_{page}.png"
    fpath = os.path.join(paths["preview_dir"], fname)
    
    if os.path.exists(fpath):
        return send_file(fpath, mimetype="image/png")
        
    # Auto-render on the fly if preview file was not present on this serverless instance
    target_pdf = None
    if doc_type == "orig":
        if os.path.exists(paths["original"]):
            target_pdf = paths["original"]
        elif doc_id == "sample_medical" or "yeshchenko" in doc_id.lower():
            target_pdf = os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf")
        elif doc_id == "sample_cadastral" or "balae" in doc_id.lower():
            target_pdf = os.path.join(SAMPLES_DIR, "balae_cadastral.pdf")
    else: # trans
        if os.path.exists(paths["translated"]):
            target_pdf = paths["translated"]
        elif doc_id == "sample_medical" or "yeshchenko" in doc_id.lower():
            pre_trans = os.path.join(BASE_DIR, "Yeshchenko_MO_063758776_EN_Translated.pdf")
            if os.path.exists(pre_trans):
                target_pdf = pre_trans
            else:
                target_pdf = os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf")
        elif doc_id == "sample_cadastral" or "balae" in doc_id.lower():
            target_pdf = os.path.join(SAMPLES_DIR, "balae_cadastral.pdf")
            
    if target_pdf and os.path.exists(target_pdf):
        try:
            import fitz
            doc = fitz.open(target_pdf)
            if 1 <= page <= len(doc):
                pix = doc[page - 1].get_pixmap(dpi=125)
                pix.save(fpath)
                return send_file(fpath, mimetype="image/png")
        except Exception:
            pass
            
    return jsonify({"error": "Preview not found"}), 404

@app.route("/api/download/<doc_id>", methods=["GET"])
def download_translated(doc_id: str):
    paths = get_doc_paths(doc_id)
    target_pdf = paths["translated"]
    download_name = "Translated_Document.pdf"
    
    if not os.path.exists(target_pdf):
        if doc_id == "sample_medical" or "yeshchenko" in doc_id.lower():
            bundled = os.path.join(BASE_DIR, "Yeshchenko_MO_063758776_EN_Translated.pdf")
            if os.path.exists(bundled):
                target_pdf = bundled
                download_name = "Yeshchenko_MO_EN_Translated.pdf"
                
    if os.path.exists(target_pdf):
        return send_file(target_pdf, as_attachment=True, download_name=download_name)
    return jsonify({"error": "Document not found"}), 404

@app.route("/api/download_original/<doc_id>", methods=["GET"])
def download_original(doc_id: str):
    paths = get_doc_paths(doc_id)
    target_pdf = paths["original"]
    if not os.path.exists(target_pdf):
        if doc_id == "sample_cadastral" or "balae" in doc_id.lower():
            target_pdf = os.path.join(SAMPLES_DIR, "balae_cadastral.pdf")
        else:
            target_pdf = os.path.join(SAMPLES_DIR, "yeshchenko_medical.pdf")
            
    if os.path.exists(target_pdf):
        fname = "original.pdf"
        if doc_id in DOCUMENTS:
            fname = DOCUMENTS[doc_id].get("filename", "original.pdf")
        return send_file(target_pdf, as_attachment=True, download_name=fname)
    return jsonify({"error": "Document not found"}), 404

@app.route("/api/segments/<doc_id>", methods=["GET"])
def get_segments(doc_id: str):
    if doc_id not in DOCUMENTS:
        paths = get_doc_paths(doc_id)
        meta_file = os.path.join(paths["dir"], "meta.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    DOCUMENTS[doc_id] = json.load(f)
            except Exception:
                pass
    if doc_id in DOCUMENTS:
        return jsonify(DOCUMENTS[doc_id].get("segments", []))
    return jsonify([])

if __name__ == "__main__":
    print("Starting OmniTranslate PDF Server on http://127.0.0.1:5055")
    app.run(host="0.0.0.0", port=5055, debug=False)
