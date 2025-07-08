import os
import yt_dlp
from gtts import gTTS
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import whisper
import cohere

# --- CONFIG ---
UPLOADS_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- API KEYS ---
COHERE_API_KEY = "zop45SFS5C3oPdfyaw66M5Oulfbw4XfcMm17ff8R"
IMAGEKIT_PUBLIC_KEY = "public_e4raMCNmvMxlmjemKgFIPgS5r0I="
IMAGEKIT_PRIVATE_KEY = "private_G6o+/DejZdAWQQlkrqZJsMI+4X8="
IMAGEKIT_ENDPOINT = "https://ik.imagekit.io/oqib51dib"


# --- SETUP COHERE & IMAGEKIT ---
co = cohere.Client(COHERE_API_KEY)
imagekit = ImageKit(
    public_key=IMAGEKIT_PUBLIC_KEY,
    private_key=IMAGEKIT_PRIVATE_KEY,
    url_endpoint=IMAGEKIT_ENDPOINT
)

def download_audio_from_youtube(youtube_url, output_audio_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_audio_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    transcript = result['text']
    transcript_path = os.path.join(OUTPUT_DIR, "transcript.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    return transcript, transcript_path

def summarize_text_with_cohere(text):
    prompt = f"""
    Summarize the following lecture transcript in 3 sections. Each section should explain key concepts clearly using simple language. Use concise bullet points.

    Transcript:
    {text}
    """
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=800,
        temperature=0.5
    )
    summary = response.generations[0].text.strip()
    summary_path = os.path.join(OUTPUT_DIR, "conceptual_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    return summary, summary_path

def generate_mcqs_with_cohere(summary):
    prompt = f"""
    You are an AI education assistant. Based on the following summary, create 5 multiple choice questions (MCQs). Each MCQ should:

    - Be relevant to the summary content
    - Have 4 options (a, b, c, d)
    - Include plausible distractors (not obviously wrong)
    - Clearly mark the correct answer (e.g., Correct Answer: b)
    - Provide a short explanation ONLY for the correct answer

    Summary:
    {summary}
    """
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=1000,
        temperature=0.6
    )
    mcqs = response.generations[0].text.strip()
    mcq_path = os.path.join(OUTPUT_DIR, "mcqs.txt")
    with open(mcq_path, "w", encoding="utf-8") as f:
        f.write(mcqs)
    return mcqs, mcq_path

def generate_audio(summary):
    tts = gTTS(summary)
    audio_path = os.path.join(OUTPUT_DIR, "summary_audio.mp3")
    tts.save(audio_path)
    return audio_path

def upload_to_imagekit(file_path, file_name):
    with open(file_path, "rb") as file:
        upload = imagekit.upload_file(
            file=file,
            file_name=file_name,
            options=UploadFileRequestOptions(folder="/greenbasket_hackathon/")
        )
        return upload.url

def process_video_from_youtube(youtube_url):
    base_name = "lecture_audio"
    audio_path = os.path.join(OUTPUT_DIR, f"{base_name}.mp3")
    print("🔻 Downloading audio from YouTube...")
    download_audio_from_youtube(youtube_url, os.path.join(OUTPUT_DIR, f"{base_name}.%(ext)s"))
    print("📝 Transcribing...")
    transcript, transcript_path = transcribe_audio(audio_path)
    print("📚 Summarizing...")
    summary, summary_path = summarize_text_with_cohere(transcript)
    print("🧠 Generating MCQs...")
    mcqs, mcq_path = generate_mcqs_with_cohere(summary)
    print("🎧 Generating summary audio...")
    summary_audio_path = generate_audio(summary)
    print("☁ Uploading files to ImageKit...")
    links = {
        "transcript": upload_to_imagekit(transcript_path, f"{base_name}_transcript.txt"),
        "summary": upload_to_imagekit(summary_path, f"{base_name}_summary.txt"),
        "summary_audio": upload_to_imagekit(summary_audio_path, f"{base_name}_summary_audio.mp3"),
        "mcqs": upload_to_imagekit(mcq_path, f"{base_name}_mcqs.txt"),
    }
    return links
