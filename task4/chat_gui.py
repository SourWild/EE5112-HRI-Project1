import time
import traceback

import psutil

from chat_backend import ChatBot
import threading
import tkinter as tk
from tkinter import ttk

# ========== Config ==========
SYSTEM_PROMPT = "You are a helpful, concise assistant."
PROCESS = psutil.Process()

PRIMARY_BG = "#f5f6fa"
CARD_BG = "#ffffff"
ACCENT_COLOR = "#4c6ef5"
ACCENT_HOVER = "#3b5bdb"
TEXT_COLOR = "#1f2937"
MUTED_TEXT = "#6b7280"
USER_BG = ACCENT_COLOR
ASSISTANT_BG = "#ffffff"
SYSTEM_BG = "#eef2fb"

MODEL_PATHS = {
    "Orca-Mini-3B": "./models/orca-mini-3b.Q4_0.gguf",
    "Mistral-7B-Instruct": "./models/mistral-7b-instruct.Q4_K_M.gguf",
}

root = tk.Tk()
root.title("本地 LLaMA 聊天机器人")
root.geometry("950x750")
root.configure(bg=PRIMARY_BG)

style = ttk.Style()
style.theme_use("clam")
style.configure("Background.TFrame", background=PRIMARY_BG)
style.configure("Card.TFrame", background=CARD_BG)
style.configure("Header.TLabel", background=PRIMARY_BG, foreground=TEXT_COLOR, font=("Arial", 18, "bold"))
style.configure("SubHeader.TLabel", background=PRIMARY_BG, foreground=MUTED_TEXT, font=("Arial", 11))
style.configure("SliderTitle.TLabel", background=CARD_BG, foreground=TEXT_COLOR, font=("Arial", 11, "bold"))
style.configure("SliderValue.TLabel", background=CARD_BG, foreground=ACCENT_COLOR, font=("Arial", 11))
style.configure("Accent.TButton", background=ACCENT_COLOR, foreground="white", font=("Arial", 12, "bold"), padding=(14, 8), borderwidth=0, focusthickness=0)
style.map("Accent.TButton", background=[("active", ACCENT_HOVER), ("disabled", "#d8ddf7")], foreground=[("disabled", "#f1f4ff")])
style.configure("Secondary.TButton", background="#e9ecf5", foreground=TEXT_COLOR, font=("Arial", 11), padding=(12, 6), borderwidth=0)
style.map("Secondary.TButton", background=[("active", "#dde3f9"), ("disabled", "#f0f2f9")], foreground=[("disabled", "#9da3b5")])
style.configure("TCombobox", fieldbackground=CARD_BG, background=CARD_BG, foreground=TEXT_COLOR, padding=6)
style.map("TCombobox", fieldbackground=[("readonly", CARD_BG)], selectbackground=[("readonly", CARD_BG)])
style.configure("Minimal.Vertical.TScrollbar", background="#c3c8d9", troughcolor=CARD_BG, bordercolor=CARD_BG, arrowcolor=MUTED_TEXT, gripcount=0)
style.map("Minimal.Vertical.TScrollbar", background=[("active", "#b0b9d3")])
style.configure("Metric.Horizontal.TScale", troughcolor="#d8dce7", background=ACCENT_COLOR)
style.map("Metric.Horizontal.TScale", background=[("active", ACCENT_HOVER)])
style.configure("Accent.Horizontal.TProgressbar", troughcolor=CARD_BG, background=ACCENT_COLOR)

# Create first bot
bot = ChatBot(MODEL_PATHS["Mistral-7B-Instruct"], system_prompt=SYSTEM_PROMPT)

# Layout containers
main_frame = ttk.Frame(root, style="Background.TFrame", padding=(24, 24, 24, 20))
main_frame.grid(row=0, column=0, sticky="nsew")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(1, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

header_frame = ttk.Frame(main_frame, style="Background.TFrame")
header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 18))

title_label = ttk.Label(header_frame, text="本地 LLaMA 聊天机器人", style="Header.TLabel")
title_label.pack(anchor="w")
subtitle_label = ttk.Label(
    header_frame,
    text="在本地实验对话模型 · 调整参数探索不同响应",
    style="SubHeader.TLabel",
)
subtitle_label.pack(anchor="w", pady=(4, 0))

chat_container = ttk.Frame(main_frame, style="Card.TFrame", padding=18)
chat_container.grid(row=1, column=0, sticky="nsew")
chat_container.grid_rowconfigure(0, weight=1)
chat_container.grid_columnconfigure(0, weight=1)

controls_container = ttk.Frame(main_frame, style="Background.TFrame", padding=(0, 18, 0, 0))
controls_container.grid(row=2, column=0, sticky="ew")
controls_container.grid_columnconfigure(0, weight=1)

def set_busy(is_busy: bool):
    entry.configure(state="disabled" if is_busy else "normal")
    if is_busy:
        send_button.state(["disabled"])
        clear_button.state(["disabled"])
        model_dropdown.configure(state="disabled")
        temperature_slider.state(["disabled"])
        top_p_slider.state(["disabled"])
        max_tokens_slider.state(["disabled"])
        progress_bar.grid()
        progress_bar.start()
    else:
        send_button.state(["!disabled"])
        clear_button.state(["!disabled"])
        model_dropdown.configure(state="readonly")
        temperature_slider.state(["!disabled"])
        top_p_slider.state(["!disabled"])
        max_tokens_slider.state(["!disabled"])
        progress_bar.stop()
        progress_bar.grid_remove()

def do_send():
    user_input = entry.get("1.0", "end-1c").strip()
    if not user_input:
        return
    entry.delete("1.0", "end")
    append(f"用户: {user_input}", "user")
    set_busy(True)

    def worker():
        try:
            reply, dt, mem = bot.chat(
                user_input,
                temperature=temperature_var.get(),
                top_p=top_p_var.get(),
                max_tokens=int(max_tokens_var.get()),
            )
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f"[Backend] Exception in chat: {tb_str}")
            reply = f"[系统错误] {e}"
            dt = 0.0
            mem = PROCESS.memory_info().rss / (1024 ** 2)
        finally:
            def done():
                append(f"助手: {reply}", "assistant")
                append(f"(延迟 {dt:.2f}s | 内存 {mem:.1f} MB)", "system")
                set_busy(False)
            root.after(0, done)

    threading.Thread(target=worker, daemon=True).start()

def on_return(event):
    do_send()
    return "break"

def do_clear():
    bot.reset()
    for w in chat_frame.winfo_children():
        w.destroy()
    append("[系统] 对话已清空。", "system")

def on_switch_model(event=None):
    model_name = model_var.get()
    new_path = MODEL_PATHS[model_name]
    append(f"[系统] 正在切换到 {model_name}...", "system")
    set_busy(True)

    def worker():
        global bot
        try:
            new_bot = ChatBot(new_path, system_prompt=SYSTEM_PROMPT)
        except Exception as err:
            tb_str = traceback.format_exc()
            print(f"[Backend] Failed to load model: {tb_str}")

            def done_error():
                append(f"[系统错误] 模型加载失败: {err}", "system")
                set_busy(False)

            root.after(0, done_error)
            return

        def done_success():
            global bot
            bot = new_bot
            append(f"[系统] 模型 {model_name} 已加载完成。", "system")
            set_busy(False)

        root.after(0, done_success)

    threading.Thread(target=worker, daemon=True).start()

# ========== GUI Helpers ==========
def add_bubble(text: str, sender: str):
    # sender in {"user","assistant","system"}
    auto_scroll = True
    try:
        _, y_max = chat_canvas.yview()
        auto_scroll = y_max >= 0.999
    except tk.TclError:
        auto_scroll = True

    if sender == "user":
        bg = USER_BG
        fg = "#ffffff"
        anchor = "e"
        justify = "left"
    elif sender == "assistant":
        bg = ASSISTANT_BG
        fg = TEXT_COLOR
        anchor = "w"
        justify = "left"
    else:
        bg = SYSTEM_BG
        fg = MUTED_TEXT
        anchor = "center"
        justify = "center"

    frame = tk.Frame(chat_frame, bg=bg, padx=12, pady=8)
    lbl = tk.Label(
        frame,
        text=text,
        bg=bg,
        fg=fg,
        justify=justify,
        wraplength=max(300, chat_canvas.winfo_width() - 140),
        font=("Arial", 12),
    )
    if sender == "user":
        lbl.pack(anchor="e", fill="x")
    elif sender == "assistant":
        lbl.pack(anchor="w", fill="x")
    else:
        lbl.pack(fill="both", expand=True)
    ts = time.strftime("%H:%M")
    ts_color = "#dbe4ff" if sender == "user" else MUTED_TEXT
    ts_lbl = tk.Label(frame, text=ts, bg=bg, fg=ts_color, font=("Arial", 9))
    ts_lbl.pack(anchor="e")
    # pack bubble to left/right
    if anchor == "center":
        frame.pack(anchor="center", pady=6, padx=10, fill="x")
    else:
        frame.pack(anchor=anchor, pady=6, padx=10, fill="x")

    chat_canvas.update_idletasks()
    if auto_scroll:
        chat_canvas.yview_moveto(1.0)

def append(text: str, tag: str = None):
    # tag: "user" | "assistant" | "system"
    sender = tag if tag in {"user","assistant","system"} else "assistant"
    add_bubble(text, sender)

# Chat area: Canvas + inner Frame + Scrollbar (for bubble layout)
chat_canvas = tk.Canvas(
    chat_container,
    highlightthickness=0,
    bd=0,
    relief="flat",
    background=CARD_BG,
)
chat_scrollbar = ttk.Scrollbar(
    chat_container,
    orient="vertical",
    command=chat_canvas.yview,
    style="Minimal.Vertical.TScrollbar",
)
chat_frame = tk.Frame(chat_canvas, bg=CARD_BG)

# attach frame to canvas
chat_window = chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw")
chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
chat_scrollbar.config(command=chat_canvas.yview)

def _on_frame_config(event=None):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))

chat_frame.bind("<Configure>", _on_frame_config)

def _on_canvas_config(event):
    chat_canvas.itemconfig(chat_window, width=event.width)

chat_canvas.bind("<Configure>", _on_canvas_config)

# mouse wheel scroll with enable/disable on enter/leave
def _on_mousewheel(event):
    if event.delta:
        if abs(event.delta) < 120:
            step = -1 if event.delta > 0 else 1
        else:
            step = int(-event.delta / 120)
        chat_canvas.yview_scroll(step, "units")


def _on_linux_scroll(event):
    step = -1 if event.num == 4 else 1
    chat_canvas.yview_scroll(step, "units")


def _bind_mousewheel(event):
    chat_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    chat_canvas.bind_all("<Button-4>", _on_linux_scroll)
    chat_canvas.bind_all("<Button-5>", _on_linux_scroll)


def _unbind_mousewheel(event):
    chat_canvas.unbind_all("<MouseWheel>")
    chat_canvas.unbind_all("<Button-4>")
    chat_canvas.unbind_all("<Button-5>")


chat_canvas.bind("<Enter>", _bind_mousewheel)
chat_canvas.bind("<Leave>", _unbind_mousewheel)

chat_canvas.grid(row=0, column=0, sticky="nsew")
chat_scrollbar.grid(row=0, column=1, padx=(12, 0), sticky="ns")

# Input card with message box and actions
input_card = ttk.Frame(controls_container, style="Card.TFrame", padding=(16, 14))
input_card.grid(row=0, column=0, sticky="ew")
input_card.grid_columnconfigure(0, weight=1)

entry = tk.Text(
    input_card,
    font=("Arial", 12),
    height=3,
    wrap="word",
    relief="flat",
    bd=0,
    highlightthickness=0,
)
entry.configure(bg=CARD_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
entry.grid(row=0, column=0, rowspan=2, padx=(0, 16), sticky="nsew")
entry.bind("<Return>", on_return)            # Enter 发送
entry.bind("<Shift-Return>", lambda e: entry.insert("insert", "\n"))  # Shift+Enter 换行

send_button = ttk.Button(input_card, text="发送", command=do_send, style="Accent.TButton")
send_button.grid(row=0, column=1, sticky="ew")

clear_button = ttk.Button(input_card, text="清空", command=do_clear, style="Secondary.TButton")
clear_button.grid(row=1, column=1, sticky="ew", pady=(8, 0))

# Model selector row
model_row = ttk.Frame(controls_container, style="Background.TFrame")
model_row.grid(row=1, column=0, sticky="ew", pady=(16, 0))
model_row.grid_columnconfigure(0, weight=1)

model_var = tk.StringVar(value="Mistral-7B-Instruct")
model_dropdown = ttk.Combobox(
    model_row,
    textvariable=model_var,
    values=["Orca-Mini-3B", "Mistral-7B-Instruct"],
    state="readonly",
)
model_dropdown.bind("<<ComboboxSelected>>", on_switch_model)
model_dropdown.grid(row=0, column=0, sticky="ew")

progress_bar = ttk.Progressbar(
    model_row,
    mode="indeterminate",
    style="Accent.Horizontal.TProgressbar",
    length=160,
)
progress_bar.grid(row=0, column=1, padx=(16, 0))
progress_bar.grid_remove()

# Slider card for parameters
slider_card = ttk.Frame(controls_container, style="Card.TFrame", padding=(16, 14))
slider_card.grid(row=2, column=0, sticky="ew", pady=(16, 0))
slider_card.grid_columnconfigure(0, weight=1, uniform="slider")
slider_card.grid_columnconfigure(1, weight=1, uniform="slider")
slider_card.grid_columnconfigure(2, weight=1, uniform="slider")

temperature_var = tk.DoubleVar(value=0.8)
top_p_var = tk.DoubleVar(value=0.95)
max_tokens_var = tk.DoubleVar(value=512)


def _build_slider(parent, column, title, variable, minimum, maximum, formatter):
    container = ttk.Frame(parent, style="Card.TFrame")
    container.grid(row=0, column=column, sticky="ew", padx=4)
    container.grid_columnconfigure(0, weight=1)
    container.grid_columnconfigure(1, weight=0)

    title_label = ttk.Label(container, text=title, style="SliderTitle.TLabel")
    title_label.grid(row=0, column=0, sticky="w")

    value_label = ttk.Label(container, text=formatter(variable.get()), style="SliderValue.TLabel")
    value_label.grid(row=0, column=1, sticky="e")

    scale = ttk.Scale(
        container,
        variable=variable,
        from_=minimum,
        to=maximum,
        orient="horizontal",
        style="Metric.Horizontal.TScale",
    )

    def _update(value):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = variable.get()
        value_label.configure(text=formatter(numeric))

    scale.configure(command=_update)
    scale.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    return scale


temperature_slider = _build_slider(
    slider_card,
    0,
    "Temperature",
    temperature_var,
    0.0,
    2.0,
    lambda v: f"{float(v):.2f}",
)

top_p_slider = _build_slider(
    slider_card,
    1,
    "Top-p",
    top_p_var,
    0.0,
    1.0,
    lambda v: f"{float(v):.2f}",
)

max_tokens_slider = _build_slider(
    slider_card,
    2,
    "Max Tokens",
    max_tokens_var,
    1,
    2048,
    lambda v: str(int(float(v))),
)

append("[系统] 界面已就绪。按 Enter 发送消息；下拉框可切换模型。", "system")

root.mainloop()
