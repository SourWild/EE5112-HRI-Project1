import os, requests, time, psutil, argparse
from rich.console import Console
from rich.prompt import Prompt
from llama_cpp import Llama

console = Console()

# ---------- Step 1: 下载模型 ----------
def download_model(url, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if not os.path.exists(save_path):
        console.print(f"[yellow]Downloading model from {url} ... (~2GB, may take a while)")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        console.print(f"[green]Model downloaded and saved to {save_path}")
    else:
        console.print(f"[cyan]Model already exists at {save_path}")

# 默认模型（Mistral-7B-Instruct Q4_K_M）
MODEL_URL = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
MODEL_PATH = "./models/mistral-7b-instruct.Q4_K_M.gguf"

# ---------- Step 2: 主函数 ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=str, default=MODEL_PATH, help="Path to .gguf model")
    ap.add_argument("--ctx", type=int, default=2048)
    ap.add_argument("--n-gpu-layers", type=int, default=20, help="Apple Silicon: set >0 for Metal accel")
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--temp", type=float, default=0.7)
    ap.add_argument("--top-p", type=float, default=0.9)
    ap.add_argument("--system", type=str, default="You are a helpful assistant.")
    ap.add_argument("--log", type=str, default="runs/session_llama.txt")
    args = ap.parse_args()

    # 下载模型（如果不存在）
    download_model(MODEL_URL, args.model)

    os.makedirs("runs", exist_ok=True)

    # 初始化模型
    console.print(f"[blue]Loading model from {args.model} ...")
    llm = Llama(
        model_path=args.model,
        n_ctx=args.ctx,
        n_threads=args.threads,
        n_gpu_layers=args.n_gpu_layers,
        verbose=False
    )

    console.rule("[bold cyan]LLaMA Chat (llama-cpp-python)")
    console.print("[dim]Commands: /reset /exit /save\n")

    messages = [{"role":"system","content":args.system}]
    with open(args.log, "w", encoding="utf-8") as f:
        while True:
            user = Prompt.ask("[bold green]You")
            if user.strip() == "/exit":
                console.print("[yellow]Bye!")
                break
            if user.strip() == "/reset":
                messages = [{"role":"system","content":args.system}]
                console.print("[yellow]Session reset.")
                continue
            if user.strip() == "/save":
                console.print(f"[cyan]Saved to {args.log}")
                continue

            messages.append({"role":"user","content":user})
            t0 = time.time()
            out = llm.create_chat_completion(
                messages=messages,
                temperature=args.temp,
                top_p=args.top_p,
                max_tokens=args.max_tokens,
            )
            dt = time.time() - t0
            reply = out["choices"][0]["message"]["content"]
            # 清理掉模型输出里的特殊符号
            safe_reply = reply.replace("[/INST]", "").replace("[INST]", "").replace("<<SYS>>", "").strip()

            mem = psutil.Process().memory_info().rss / (1024**2)
            console.print(f"[bold blue]Assistant:[/bold blue] {safe_reply}", markup=True)
            console.print(f"[dim]Latency: {dt:.2f}s | RAM: {mem:.1f} MB[/]\n")

            messages.append({"role":"assistant","content":reply})
            f.write(f"USER: {user}\nASSISTANT: {reply}\n-- {dt:.2f}s, {mem:.1f}MB --\n\n")
            f.flush()

if __name__ == "__main__":
    main()