import os
import time
from typing import Any, Dict, List, Optional
import traceback

import psutil
from llama_cpp import Llama


class ChatBot:
    """
    A thin wrapper around llama.cpp that:
      - Supports multi-turn chat with context.
      - Auto-selects the best prompting strategy based on the model file name.
      - Falls back gracefully if a path produces an empty reply.
    """

    def __init__(
        self,
        model_path: str,
        sys_prompt: str = "You are a helpful, concise assistant.",
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = 20,
        verbose: bool = False,
    ) -> None:
        self.model_path = model_path
        self.sys_prompt = sys_prompt
        self.config = dict(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=verbose,
        )
        self.llm: Optional[Llama] = None
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.sys_prompt}
        ]
        self.mode: str = "base"
        self.load_model()

    # ---------- Model management ----------
    def _guess_mode(self, filename: str) -> str:
        """
        Heuristic:
          - use Chat API if file name clearly indicates an instruct/chat model,
        """
        name = os.path.basename(filename).lower()
        looks_chat = any(k in name for k in ["chat", "instruct", "assistant", "alpaca", "vicuna", "zephyr", "openhermes", "orca"])
        if looks_chat:
            return "chat"
        return "base"

    def load_model(self) -> None:
        self.llm = Llama(**self.config)
        self.mode = self._guess_mode(self.model_path)
        print(f"[Backend] Loaded: {self.model_path}  (mode={self.mode})")

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.sys_prompt}]

    # ---------- Helpers ----------
    def _extract_text(self, out: Dict[str, Any]) -> str:
        """
        Robustly extract text from llama.cpp outputs (chat or text completion).
        """
        try:
            choices = out.get("choices", [])
            if not choices:
                return ""
            ch0 = choices[0]
            # Chat format
            if isinstance(ch0, dict) and "message" in ch0 and isinstance(ch0["message"], dict):
                content = ch0["message"].get("content", "")
                if content:
                    return content
            # Text format
            if "text" in ch0:
                txt = ch0.get("text", "")
                if txt:
                    return txt
        except Exception as e:
            print(f"[Backend] _extract_text error: {e}")
        return ""

    def _build_inst_prompt(self, user_input: str, history_max_pairs: int = 5) -> str:
        """
        Build a single [INST] prompt that contains a compact conversation summary.
        This is forgiving across many 'base' style instruct models.
        """
        # Collect last history pairs (user, assistant) ignoring the system message
        pairs: List[tuple[str, str]] = []
        last_user: Optional[str] = None
        for m in self.messages:
            if m["role"] == "user":
                last_user = m["content"]
            elif m["role"] == "assistant" and last_user is not None:
                pairs.append((last_user, m["content"]))
                last_user = None
        pairs = pairs[-history_max_pairs:]

        header = f"<<SYS>>\n{self.sys_prompt}\n<</SYS>>\n"
        conv = []
        for u, a in pairs:
            conv.append(f"User: {u}\nAssistant: {a}\n")
        conv.append(f"User: {user_input}\nAssistant:")
        body = header + "".join(conv)
        prompt = f"[INST] {body} [/INST]"
        return prompt

    # ---------- Chat ----------
    def chat(self, user_input: str, temperature: float = 0.8, top_p: float = 0.95, max_tokens: int = 512):
        """
        Generate a reply. Always returns (reply, dt_seconds, rss_mem_mb).
        """
        t0 = time.time()
        reply = ""
        try:
            if self.mode == "chat":
                # Full multi-turn context via Chat API
                self.messages.append({"role": "user", "content": user_input})
                out = self.llm.create_chat_completion(
                    messages=self.messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    repeat_penalty=1.1,
                )
                reply = self._extract_text(out).strip()

                # If some instruct models still give empty content under Chat API, try INST fallback
                if not reply:
                    prompt = self._build_inst_prompt(user_input)
                    out = self.llm(
                        prompt,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                        repeat_penalty=1.1,
                    )
                    reply = self._extract_text(out).strip()

                if reply:
                    self.messages.append({"role": "assistant", "content": reply})

            else:
                # Base-style prompt using [INST] with a compact history
                prompt = self._build_inst_prompt(user_input)
                out = self.llm(
                    prompt,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    repeat_penalty=1.1,
                )
                reply = self._extract_text(out).strip()
                self.messages.append({"role": "user", "content": user_input})
                self.messages.append({"role": "assistant", "content": reply or ""})

        except Exception as e:
            reply = f"[系统错误] {e}"
            print(f"[Backend] Exception: {e}")

        if not reply:
            reply = "(模型没有返回内容)"

        dt = time.time() - t0
        mem = psutil.Process().memory_info().rss / (1024 ** 2)
        return reply, dt, mem
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

# from chat_backend import ChatBot

# ========== Config ==========
MODEL_PATHS = {
    "Orca-Mini-3B": "./models/orca-mini-3b.Q4_0.gguf",
    "Mistral-7B-Instruct": "./models/mistral-7b-instruct.Q4_K_M.gguf",
}

root = tk.Tk()
root.title("本地 LLaMA 聊天机器人")
root.geometry("950x750")

# Create first bot
bot = ChatBot(MODEL_PATHS["Mistral-7B-Instruct"])

def set_busy(is_busy: bool):
    state = "disabled" if is_busy else "normal"
    entry.configure(state=state)
    send_button.configure(state=state)
    clear_button.configure(state=state)
    model_dropdown.configure(state="disabled" if is_busy else "readonly")
    temperature_slider.configure(state=state)
    top_p_slider.configure(state=state)
    max_tokens_slider.configure(state=state)
    if is_busy:
        progress_bar.grid()
        progress_bar.start()
    else:
        progress_bar.stop()
        progress_bar.grid_remove()

def do_send():
    user_input = entry.get("1.0", "end-1c").strip()
    if not user_input:
        return
    entry.delete("1.0", "end")
    append(f"用户: {user_input}", "user")

    def worker():
        set_busy(True)
        try:
            reply, dt, mem = bot.chat(user_input, temperature=temperature_var.get(), top_p=top_p_var.get(), max_tokens=max_tokens_var.get())
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f"[Backend] Exception in chat: {tb_str}")
            reply = f"[系统错误] {e}"
            dt = 0.0
            mem = psutil.Process().memory_info().rss / (1024 ** 2)
        finally:
            def done():
                append(f"助手: {reply}", "assistant")
                append(f"(延迟 {dt:.2f}s | 内存 {mem:.1f} MB)", "system")
                set_busy(False)
            root.after(0, done)

    threading.Thread(target=worker, daemon=True).start()

def on_return(event):
    do_send()

def do_clear():
    bot.reset()
    for w in chat_frame.winfo_children():
        w.destroy()
    append("[系统] 对话已清空。", "system")

def on_switch_model(event=None):
    model_name = model_var.get()
    new_path = MODEL_PATHS[model_name]
    append(f"[系统] 正在切换到 {model_name}...", "system")

    def worker():
        set_busy(True)
        global bot
        bot = ChatBot(new_path)
        def done():
            append(f"[系统] 模型 {model_name} 已加载完成。", "system")
            set_busy(False)
        root.after(0, done)

    threading.Thread(target=worker, daemon=True).start()

# ========== GUI Helpers ==========
def add_bubble(text: str, sender: str):
    # sender in {"user","assistant","system"}
    if sender == "user":
        bg = "#DCF2FF"   # light blue
        anchor = "e"
        justify = "left"
    elif sender == "assistant":
        bg = "#F1F3F5"   # light gray
        anchor = "w"
        justify = "left"
    else:
        bg = "#EEEEEE"
        anchor = "center"
        justify = "center"

    frame = tk.Frame(chat_frame, bg=bg, padx=8, pady=6)
    lbl = tk.Label(
        frame,
        text=text,
        bg=bg,
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
    ts_lbl = tk.Label(frame, text=ts, bg=bg, fg="#777", font=("Arial", 9))
    ts_lbl.pack(anchor="e")
    # pack bubble to left/right
    if anchor == "center":
        frame.pack(anchor="center", pady=6, padx=10, fill="x")
    else:
        frame.pack(anchor=anchor, pady=6, padx=10, fill="x")

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

def append(text: str, tag: str = None):
    # tag: "user" | "assistant" | "system"
    sender = tag if tag in {"user","assistant","system"} else "assistant"
    add_bubble(text, sender)

# Chat area: Canvas + inner Frame + Scrollbar (for bubble layout)
chat_canvas = tk.Canvas(root, highlightthickness=0)
chat_scrollbar = ttk.Scrollbar(root, orient="vertical", command=chat_canvas.yview)
chat_frame = tk.Frame(chat_canvas)

# attach frame to canvas
chat_window = chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw", width=chat_canvas.winfo_width())
chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
chat_scrollbar.config(command=chat_canvas.yview)

def _on_frame_config(event=None):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
    chat_canvas.yview_moveto(1.0)

chat_frame.bind("<Configure>", _on_frame_config)

def _on_canvas_config(event):
    chat_canvas.itemconfig(chat_window, width=event.width)

chat_canvas.bind("<Configure>", _on_canvas_config)

# mouse wheel scroll with enable/disable on enter/leave
def _on_mousewheel(event):
    scroll_units = int(-1 * (event.delta / 120))
    chat_canvas.yview_scroll(scroll_units, "units")

def _bind_mousewheel(event):
    chat_canvas.bind_all("<MouseWheel>", _on_mousewheel)

def _unbind_mousewheel(event):
    chat_canvas.unbind_all("<MouseWheel>")

chat_canvas.bind("<Enter>", _bind_mousewheel)
chat_canvas.bind("<Leave>", _unbind_mousewheel)

chat_canvas.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
chat_scrollbar.grid(row=0, column=4, padx=(0,10), pady=10, sticky="ns")

entry = tk.Text(root, font=("Arial", 12), height=3)
entry.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
entry.bind("<Return>", on_return)            # Enter 发送
entry.bind("<Shift-Return>", lambda e: entry.insert("insert", "\n"))  # Shift+Enter 换行

send_button = tk.Button(root, text="发送", width=10, command=do_send)
send_button.grid(row=1, column=3, padx=10, pady=(5, 2), sticky="ew")

clear_button = tk.Button(root, text="清空", width=10, command=do_clear)
clear_button.grid(row=2, column=3, padx=10, pady=(2, 5), sticky="ew")

model_var = tk.StringVar(value="Mistral-7B-Instruct")
model_dropdown = ttk.Combobox(root, textvariable=model_var, values=["Orca-Mini-3B", "Mistral-7B-Instruct"], state="readonly")
model_dropdown.bind("<<ComboboxSelected>>", on_switch_model)
model_dropdown.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

progress_bar = ttk.Progressbar(root, mode="indeterminate")
progress_bar.grid(row=2, column=4, padx=10, pady=10, sticky="e")
progress_bar.grid_remove()

# Add sliders for temperature, top_p, max_tokens in a dedicated frame
slider_frame = tk.Frame(root)
slider_frame.grid(row=3, column=0, columnspan=5, padx=10, pady=10, sticky="ew")

slider_frame.grid_columnconfigure(0, weight=1)
slider_frame.grid_columnconfigure(1, weight=1)
slider_frame.grid_columnconfigure(2, weight=1)

temperature_var = tk.DoubleVar(value=0.8)
top_p_var = tk.DoubleVar(value=0.95)
max_tokens_var = tk.IntVar(value=512)

temperature_label = tk.Label(slider_frame, text="Temperature")
temperature_label.grid(row=0, column=0, padx=10, pady=(0, 2), sticky="w")
temperature_slider = tk.Scale(slider_frame, variable=temperature_var, from_=0.0, to=2.0, resolution=0.01, orient="horizontal")
temperature_slider.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")

top_p_label = tk.Label(slider_frame, text="Top-p")
top_p_label.grid(row=0, column=1, padx=10, pady=(0, 2), sticky="w")
top_p_slider = tk.Scale(slider_frame, variable=top_p_var, from_=0.0, to=1.0, resolution=0.01, orient="horizontal")
top_p_slider.grid(row=1, column=1, padx=10, pady=(0, 5), sticky="ew")

max_tokens_label = tk.Label(slider_frame, text="Max Tokens")
max_tokens_label.grid(row=0, column=2, padx=10, pady=(0, 2), sticky="w")
max_tokens_slider = tk.Scale(slider_frame, variable=max_tokens_var, from_=1, to=2048, orient="horizontal")
max_tokens_slider.grid(row=1, column=2, padx=10, pady=(0, 5), sticky="ew")

# Make layout flexible
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

append("[系统] 界面已就绪。按 Enter 发送消息；下拉框可切换模型。", "system")

root.mainloop()