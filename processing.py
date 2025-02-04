import os
import subprocess
import textwrap
import time
import concurrent.futures
import whisper
import torch
from moviepy.editor import VideoFileClip, CompositeVideoClip
from moviepy.config import change_settings
from utils import fix_spacing, create_outlined_text_clip

# Diretório base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho do ImageMagick dentro do projeto
IMAGEMAGICK_PATH = os.path.join(BASE_DIR, "imagemagick", "convert.exe")
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

# Caminho do FFmpeg dentro do projeto
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")

# Caminho dos modelos do Whisper
WHISPER_MODELS_DIR = os.path.join(BASE_DIR, "whisper_models")

def legenda_video(video_path, formato, language, model_choice, log_callback, text_color, outline_color, use_gpu):
    """
    Processa o vídeo: extrai áudio, transcreve com Whisper, cria legendas sincronizadas e gera o vídeo final.
    """
    audio_path = os.path.join(BASE_DIR, "temp_audio.wav")
    start_time_total = time.time()

    def log(message):
        """Exibe mensagens no terminal e na GUI."""
        print(message)
        log_callback(message)

    try:
        log("🔹 Iniciando processamento de legendagem...")
        log(f"📂 Vídeo: {video_path}")

        # Verifica se FFmpeg está no projeto
        if not os.path.exists(FFMPEG_PATH):
            raise FileNotFoundError(f"❌ FFmpeg não encontrado em {FFMPEG_PATH}. Adicione-o ao projeto.")
        
        # Verifica se ImageMagick está no projeto
        if not os.path.exists(IMAGEMAGICK_PATH):
            raise FileNotFoundError(f"❌ ImageMagick não encontrado em {IMAGEMAGICK_PATH}. Adicione-o ao projeto.")

        # Verifica se o modelo do Whisper foi baixado
        model_path = os.path.join(WHISPER_MODELS_DIR, f"{model_choice}.pt")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Modelo Whisper '{model_choice}.pt' não encontrado.")
        
        # Define dispositivo de execução
        device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        log(f"🖥️ Usando dispositivo: {device}")

        # Carrega modelo Whisper localmente
        log(f"📥 Carregando modelo Whisper: {model_choice}...")
        modelo = whisper.load_model(model_choice, device=device, download_root=WHISPER_MODELS_DIR)
        log(f"✅ Modelo '{model_choice}' carregado.")

        # Extrai áudio do vídeo usando FFmpeg do projeto
        log("🎵 Extraindo áudio...")
        cmd = [
            FFMPEG_PATH, "-y", "-i", video_path, "-vn",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            audio_path, "-threads", "4", "-preset", "veryfast"
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if not os.path.exists(audio_path):
            raise FileNotFoundError("❌ Falha na extração de áudio!")

        log("✅ Áudio extraído com sucesso.")

        # Transcreve áudio com Whisper
        log("📝 Transcrevendo áudio...")
        resultado = modelo.transcribe(audio_path, language="en", task="transcribe")
        segments = resultado.get("segments")

        if not segments:
            raise RuntimeError("❌ Nenhum segmento encontrado na transcrição.")

        log(f"✅ Transcrição concluída com {len(segments)} segmentos.")

        # Carrega vídeo
        log("📽️ Carregando vídeo...")
        video = VideoFileClip(video_path)

        # Cria legendas sincronizadas
        def process_segment(seg):
            seg_start = seg.get("start")
            seg_end = seg.get("end")
            seg_text = seg.get("text", "").strip()

            if not seg_text:
                return None

            if language == "Português":
                try:
                    from googletrans import Translator
                    translator = Translator()
                    seg_text = translator.translate(seg_text, dest="pt").text
                except Exception as e:
                    log(f"⚠️ Erro na tradução: {e}")
                    return None

            seg_text = fix_spacing(seg_text)
            lines = textwrap.wrap(seg_text, width=60)
            wrapped_text = "\n".join(lines[:2])

            try:
                clip = create_outlined_text_clip(
                    wrapped_text,
                    video_width=int(video.w),
                    height=40,
                    fontsize=18,
                    font='Arial',
                    text_color=text_color,
                    outline_color=outline_color,
                    offset=1
                )
            except Exception as e:
                log(f"⚠️ Erro ao criar legenda: {e}")
                return None

            return clip.set_position(('center', 'bottom')).set_start(seg_start).set_duration(seg_end - seg_start)

        num_segments = len(segments)
        max_workers = min(num_segments, 8)
        log(f"🔄 Criando legendas com {max_workers} threads...")
        start_time_clips = time.time()

        text_clips = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_segment, seg) for seg in segments]
            for future in concurrent.futures.as_completed(futures):
                clip = future.result()
                if clip is not None:
                    text_clips.append(clip)

        elapsed_clips = time.time() - start_time_clips
        log(f"🕒 Tempo para criar legendas: {elapsed_clips:.2f} segundos.")

        if not text_clips:
            raise RuntimeError("❌ Nenhuma legenda foi gerada.")

        log("✅ Legendas criadas.")

        # Adiciona legendas ao vídeo
        log("🎬 Combinando legendas ao vídeo...")
        video_final = CompositeVideoClip([video] + text_clips)
        video_final = video_final.set_audio(video.audio)

        # Salva o vídeo final
        saida_video = os.path.join(BASE_DIR, f"video_legendado.{formato}")
        log(f"💾 Salvando vídeo final: {saida_video}")
        video_final.write_videofile(saida_video, codec="libx264", fps=video.fps, ffmpeg_params=["-preset", "veryfast"])

        total_time = time.time() - start_time_total
        log(f"✅ Vídeo final salvo. Tempo total: {total_time:.2f} segundos.")

    except Exception as e:
        log(f"❌ Erro: {e}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            log("🗑️ Arquivo de áudio temporário removido.")
