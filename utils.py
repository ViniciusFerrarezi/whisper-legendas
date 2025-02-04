# utils.py
import re
from moviepy.editor import TextClip, CompositeVideoClip

def fix_spacing(text):
    """
    Corrige o espaçamento: adiciona um espaço após ponto (.) ou interrogação (?) se não houver.
    """
    return re.sub(r'([\.?])(?=\S)', r'\1 ', text)

def create_outlined_text_clip(text, video_width, height, fontsize, font, text_color, outline_color, offset=1):
    """
    Cria um TextClip com contorno manual (outline).
    
    Se outline_color for igual a text_color (ignorando maiúsculas/minúsculas), retorna apenas o clip principal.
    Caso contrário, cria cópias deslocadas do texto com a cor do contorno e compõe com o clip principal.
    """
    main_clip = TextClip(text, fontsize=fontsize, font=font, color=text_color,
                           bg_color="transparent", method="caption", size=(video_width, height))
    if outline_color.lower() == text_color.lower():
        return main_clip
    offsets = [(-offset, -offset), (-offset, 0), (-offset, offset),
               (0, -offset), (0, offset),
               (offset, -offset), (offset, 0), (offset, offset)]
    outline_clips = []
    for dx, dy in offsets:
        clip = TextClip(text, fontsize=fontsize, font=font, color=outline_color,
                        bg_color="transparent", method="caption", size=(video_width, height))
        clip = clip.set_position((dx, dy))
        outline_clips.append(clip)
    composite = CompositeVideoClip(outline_clips + [main_clip])
    return composite
