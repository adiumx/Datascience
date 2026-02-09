import os
import ffmpeg
import whisper
from whisper.utils import get_writer
import pysrt 
from pathlib import Path

# --- CONFIGURATION ---
# 1. INPUT/OUTPUT FILES
VIDEO_FILE = "Somos Ajenos.MP4"  # <-- **CHANGE THIS TO YOUR VIDEO FILENAME**
OUTPUT_VIDEO_FILE = "output_video_hardcoded.mp4"
EDITED_SRT_FILE = "final_subtitles_edited.srt" 

# 2. WHISPER SETTINGS
WHISPER_MODEL = "medium"  # Options: tiny, base, small, medium, large
WHISPER_TASK = "transcribe" # or 'translate'
TARGET_LANGUAGE = "es" 

# --- FUNCTIONS ---

def step_1_generate_srt():
    """Generates the initial SRT file using OpenAI Whisper."""
    if os.path.exists(EDITED_SRT_FILE):
        print(f"✅ Edited SRT file already exists: {EDITED_SRT_FILE}. Skipping transcription.")
        return

    if not os.path.exists(VIDEO_FILE):
        raise FileNotFoundError(f"Video file not found: {VIDEO_FILE}. Please check the filename.")

    print(f"--- 1. Generating Subtitles with Whisper ({WHISPER_MODEL} model) ---")
    
    try:
        model = whisper.load_model(WHISPER_MODEL)
        result = model.transcribe(
            VIDEO_FILE,
            task=WHISPER_TASK,
            language=TARGET_LANGUAGE,
            verbose=True
        )
        
        # Save SRT
        srt_writer = get_writer("srt", ".") 
        srt_writer(result, EDITED_SRT_FILE)
        print(f"✅ Initial SRT file created: {EDITED_SRT_FILE}. Ready for editing.")

    except Exception as e:
        print(f"❌ An error occurred during transcription: {e}")
        if os.path.exists(EDITED_SRT_FILE):
             os.remove(EDITED_SRT_FILE)
        raise

def step_2_review_and_edit_srt():
    """Prompts the user to review the generated SRT file."""
    if not os.path.exists(EDITED_SRT_FILE):
        return

    print("\n--- 2. Subtitle Review and Editing ---")
    print("\n*************************************************************")
    print(f"ACTION REQUIRED: Please open '{EDITED_SRT_FILE}'")
    print("  Correct any text errors, save, and then close the file.")
    print("*************************************************************\n")
    
    input("Press Enter to continue after editing...")
    print("Continuing...")

def step_3_hardcode_subtitles():
    """Burns the edited SRT file into the video using FFmpeg."""
    if not os.path.exists(EDITED_SRT_FILE):
        print(f"❌ Cannot hardcode: Edited SRT file not found.")
        return

    print(f"\n--- 3. Hardcoding Subtitles (Burning into Video) ---")
    
    # 1. Prepare Paths
    # We use .as_posix() or replace to ensure forward slashes, which FFmpeg prefers even on Windows
    absolute_srt_path = Path(EDITED_SRT_FILE).resolve().as_posix()
    # Windows FFmpeg sometimes has trouble with drive letters (C:) in filter strings. 
    # Escaping the colon can help, but forward slashes usually fix it.
    
    # 2. Define Style
    subtitle_style = "FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=2"

    try:
        # 3. Build Stream
        input_stream = ffmpeg.input(VIDEO_FILE)
        
        video_with_subs = input_stream.video.filter(
            'subtitles', 
            absolute_srt_path, 
            force_style=subtitle_style
        )
        
        stream = ffmpeg.output(
            video_with_subs,
            input_stream.audio,
            OUTPUT_VIDEO_FILE,
            vcodec='libx264',
            acodec='aac',
            strict='experimental',
            preset='medium'
            # NOTE: overwrite_output=True removed from here
        )
        
        # 4. Run (overwrite_output goes here!)
        print("Processing video... this may take a moment.")
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        print(f"✅ Success! Final video saved to: {OUTPUT_VIDEO_FILE}")

    except ffmpeg.Error as e:
        print(f"❌ An FFmpeg error occurred.")
        # Check if stderr exists before decoding
        if e.stderr:
            print(f"FFmpeg Error Details:\n{e.stderr.decode('utf8')}")
        else:
            print("No detailed error message returned by FFmpeg. Check file paths and permissions.")
        
def main():
    print("--- Video Subtitle Automation Script ---")
    try:
        step_1_generate_srt()
        step_2_review_and_edit_srt()
        step_3_hardcode_subtitles()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()