# main.py
import os
from detection import predict_video, predict_image
from decision import get_final_decision_with_prob
from rag_engine import RAGSystem, process_disease
from config import CLASSES, DISEASE_CLASSES, RAG_DATA_PATH


def main():
    # 1. Get input from user
    target_path = input("📸 Please enter the path to the Image or Video: ").strip()
    target_path = target_path.strip('"').strip("'")  # Clean up quotes if drag-and-dropped

    if not os.path.exists(target_path):
        print("❌ Error: The specified file does not exist.")
        return

    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')

    final_results = None

    # 2. Run Image or Video Pipeline
    if target_path.lower().endswith(image_extensions):
        print("🖼️ Image detected. Running image prediction...")
        output_filename = "annotated_" + os.path.basename(target_path)
        final_results = predict_image(target_path, output_path=output_filename)

        if not final_results:
            print("⚠️ No trees detected in the image.")
            return

    elif target_path.lower().endswith(video_extensions):
        print("🎬 Video detected. Running video prediction...")
        track_history, track_history_type = predict_video(target_path)

        print("🧠 Calculating final disease probabilities from video frames...")
        final_results = get_final_decision_with_prob(
            pest_history=track_history,
            type_history=track_history_type,
            pest_classes=CLASSES,
            type_classes=DISEASE_CLASSES
        )
    else:
        print("⚠️ Unsupported file format. Please provide a standard image or video file.")
        return

    # 3. Generate unified crop report via RAG
    if final_results:
        print("📚 Initializing RAG System...")
        rag = RAGSystem(RAG_DATA_PATH)

        print("📝 Generating comprehensive AI reports for all trees...")
        reports, crop_html = process_disease(
            detection_results=final_results,
            rag_system=rag,
            crop_name="النخيل",
            save_individual=False,   # set True to also save per-tree HTML/PDF
        )

        print(f"\n🎉 Processing Complete!")
        print(f"📄 Unified crop report saved → {crop_html}")
        print(f"🌴 Trees processed: {len(reports)}")


if __name__ == "__main__":
    main()