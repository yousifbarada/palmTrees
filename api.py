import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from detection import predict_video, predict_image
from decision import get_final_decision_with_prob
from rag_engine import RAGSystem, process_disease
from config import CLASSES, DISEASE_CLASSES, RAG_DATA_PATH

# 1. Manage lifespan (Startup and Shutdown)
rag_system = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_system
    print("📚 Initializing RAG System and loading models...")
    if os.path.exists(RAG_DATA_PATH):
        rag_system = RAGSystem(RAG_DATA_PATH)
        print("✅ RAG System loaded successfully.")
    else:
        print(f"⚠️ Warning: RAG_DATA_PATH '{RAG_DATA_PATH}' not found. Text generation will fail.")
    yield
    print("🛑 Shutting down API...")


# 2. Initialize FastAPI
app = FastAPI(title="Palm Tree Disease Detection API", lifespan=lifespan)


# Allow CORS (useful if you are building a React/Vue frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories for temp files and outputs
TEMP_DIR = "temp_uploads"
OUTPUT_DIR = "outputs"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/api/health")
async def health_check():
    """
    Endpoint بسيط عشان الـ UI يتأكد إن السيرفر والـ Models حملت وبقت جاهزة.
    """
    if rag_system is not None:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Starting up...")
@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)):
    """
    Endpoint to upload an image or video, detect palm diseases,
    and generate a comprehensive diagnostic report.
    """
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG System is not initialized. Check your RAG_DATA_PATH.")

    file_ext = os.path.splitext(file.filename)[1].lower()
    temp_file_path = os.path.join(TEMP_DIR, file.filename)

    # Save the uploaded file temporarily
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')

    final_results = None
    output_filename = os.path.join(OUTPUT_DIR, f"annotated_{file.filename}")

    try:
        # --- Image Processing ---
        if file_ext in image_extensions:
            print(f"🖼️ Processing Image: {file.filename}")
            final_results = predict_image(temp_file_path, output_path=output_filename)

            if not final_results:
                return JSONResponse(status_code=400, content={"message": "No trees detected in the image."})

        # --- Video Processing ---
        elif file_ext in video_extensions:
            print(f"🎬 Processing Video: {file.filename}")
            track_history, track_history_type = predict_video(temp_file_path)
            final_results = get_final_decision_with_prob(
                pest_history=track_history,
                type_history=track_history_type,
                pest_classes=CLASSES,
                type_classes=DISEASE_CLASSES
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")

        # --- Report Generation ---
        if final_results:
            print("📝 Generating comprehensive AI reports...")
            reports, crop_html = process_disease(
                detection_results=final_results,
                rag_system=rag_system,
                crop_name="النخيل",
                save_individual=False
            )

            return {
                "status": "success",
                "message": "Analysis completed successfully.",
                "detections": final_results,
                "reports_text": reports,
                "report_html_file": crop_html,
                "annotated_image": output_filename if file_ext in image_extensions else None
            }
        else:
            return JSONResponse(status_code=400, content={"message": "No results could be determined."})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up the original uploaded file to save disk space
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.get("/api/download-report")
async def download_report(filepath: str):
    """
    Endpoint to download the generated HTML or PDF report.
    Pass the filename returned from the /api/analyze endpoint.
    """
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type='application/octet-stream', filename=os.path.basename(filepath))
    raise HTTPException(status_code=404, detail="File not found.")


@app.get("/api/download-image")
async def download_image(filepath: str):
    """
    Endpoint to download the annotated output image.
    """
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type='image/jpeg')
    raise HTTPException(status_code=404, detail="Image not found.")