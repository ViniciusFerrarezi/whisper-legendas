import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from processing import legenda_video

# Classe para tooltips
class CreateToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
        
    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "12", "normal"))
        label.pack(ipadx=1)
        
    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

root = tk.Tk()
root.iconbitmap('icon.ico')
root.title("Legenda Vídeo com Whisper")
root.geometry("800x600")
root.configure(bg="#000000")

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TLabel", background="#000000", foreground="white")
style.configure("TFrame", background="#000000")
style.configure("TButton", background="#3e3e3e", foreground="white")
style.configure("TCombobox", fieldbackground="#4b0082", background="#4b0082", foreground="#4b0082")
style.map("TCombobox", background="#333333")
style.configure("TCheckbutton", background="#000000", foreground="white")
style.map("TCheckbutton", background="#333333")  # Cinza escuro quando pressionado

# Variáveis da interface
formato_var = tk.StringVar(value="mp4")
language_var = tk.StringVar(value="Português")
model_var = tk.StringVar(value="small")
text_color_var = tk.StringVar(value="white")
outline_color_var = tk.StringVar(value="black")
use_gpu_var = tk.BooleanVar(value=False)

frame_opts = ttk.Frame(root)
frame_opts.pack(pady=10, padx=10, anchor="nw")

# Formato do vídeo
lbl_formato = ttk.Label(frame_opts, text="Formato do vídeo:")
lbl_formato.grid(row=0, column=0, padx=5, sticky="w")
formato_opcoes = ttk.Combobox(frame_opts, textvariable=formato_var,
                              values=["mp4", "avi", "mov", "mkv", "flv", "wmv"],
                              state="readonly", width=10)
formato_opcoes.grid(row=0, column=1, padx=5)
formato_opcoes.current(0)
CreateToolTip(lbl_formato, "Selecione o formato de saída do vídeo.")

# Idioma
lbl_idioma = ttk.Label(frame_opts, text="Idioma:")
lbl_idioma.grid(row=0, column=2, padx=5, sticky="w")
lang_opcoes = ttk.Combobox(frame_opts, textvariable=language_var,
                           values=["Inglês", "Português"],
                           state="readonly", width=10)
lang_opcoes.grid(row=0, column=3, padx=5)
lang_opcoes.current(1)
CreateToolTip(lbl_idioma, "Selecione 'Inglês' para manter legendas originais ou 'Português' para traduzir.")

# Modelo Whisper
lbl_model = ttk.Label(frame_opts, text="Modelo Whisper:")
lbl_model.grid(row=1, column=0, padx=5, sticky="w")
model_opcoes = ttk.Combobox(frame_opts, textvariable=model_var,
                            values=["tiny", "base", "small", "medium", "large"],
                            state="readonly", width=10)
model_opcoes.grid(row=1, column=1, padx=5)
model_opcoes.current(2)
CreateToolTip(lbl_model, "Modelos maiores são mais precisos, mas mais lentos.")

# Cor do texto
lbl_text_color = ttk.Label(frame_opts, text="Cor do texto:")
lbl_text_color.grid(row=1, column=2, padx=5, sticky="w")
text_color_opcoes = ttk.Combobox(frame_opts, textvariable=text_color_var,
                                 values=["white", "yellow", "cyan", "magenta", "red", "green", "blue"],
                                 state="readonly", width=10)
text_color_opcoes.grid(row=1, column=3, padx=5)
text_color_opcoes.current(0)
CreateToolTip(lbl_text_color, "Selecione a cor do texto da legenda.")

# Cor do contorno
lbl_outline_color = ttk.Label(frame_opts, text="Cor do contorno:")
lbl_outline_color.grid(row=1, column=4, padx=5, sticky="w")
outline_color_opcoes = ttk.Combobox(frame_opts, textvariable=outline_color_var,
                                    values=["black", "white", "yellow", "cyan", "magenta", "red", "green", "blue"],
                                    state="readonly", width=10)
outline_color_opcoes.grid(row=1, column=5, padx=5)
outline_color_opcoes.current(0)
CreateToolTip(lbl_outline_color, "Selecione a cor do contorno da legenda.")

# Usar GPU
lbl_gpu = ttk.Label(frame_opts, text="Usar GPU:")
lbl_gpu.grid(row=0, column=4, padx=5, sticky="w")
gpu_chk = ttk.Checkbutton(frame_opts, variable=use_gpu_var)
gpu_chk.grid(row=0, column=5, padx=5, sticky="w")
CreateToolTip(lbl_gpu, "Marque se seu PC possui GPU compatível (CUDA) para acelerar a transcrição.")

terminal = scrolledtext.ScrolledText(root, bg="#000000", fg="#00FF00", font=("Consolas", ))
terminal.pack(fill="both", expand=True, padx=10, pady=10)
terminal.config(state=tk.DISABLED)

def log_message(message):
    terminal.config(state=tk.NORMAL)
    terminal.insert(tk.END, message + "\n")
    terminal.see(tk.END)
    terminal.config(state=tk.DISABLED)

def selecionar_video():
    formato = formato_var.get().lower()
    if formato == "mp4":
        tipos_arquivo = [("Vídeos MP4", "*.mp4")]
    else:
        tipos_arquivo = [("Todos os Vídeos", "*.*")]
    caminho_video = filedialog.askopenfilename(filetypes=tipos_arquivo)
    if not caminho_video:
        tk.messagebox.showerror("Erro", "Nenhum arquivo foi selecionado.")
        return
    caminho_video = os.path.abspath(caminho_video)
    if not os.path.exists(caminho_video):
        tk.messagebox.showerror("Erro", f"O arquivo não existe:\n{caminho_video}")
        return
    if not os.access(caminho_video, os.R_OK):
        tk.messagebox.showerror("Erro", f"Sem permissão para ler o arquivo:\n{caminho_video}")
        return
    
    log_message("Iniciando processamento...")
    threading.Thread(
        target=legenda_video,
        args=(
            caminho_video,
            formato,
            language_var.get(),
            model_var.get(),
            log_message,
            text_color_var.get(),
            outline_color_var.get(),
            use_gpu_var.get()
        ),
        daemon=True
    ).start()

btn_selecionar = ttk.Button(root, text="Selecionar Vídeo", command=selecionar_video)
btn_selecionar.pack(pady=5, anchor="nw", padx=10)

if __name__ == "__main__":
    root.mainloop()
