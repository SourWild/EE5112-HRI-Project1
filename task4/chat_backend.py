import time, psutil
from llama_cpp import Llama

DEFAULT_MODEL = "./models/orca-mini-3b.Q4_0.gguf"

class ChatBot:
    def __init__(self, model_path=DEFAULT_MODEL):
        self.model_path = model_path
        self.load_model()

    def load_model(self):
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=20,
            verbose=False
        )
        self.reset()

    def reset(self):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    def _extract_text(self, output):
        # Try to extract text from chat completion
        if isinstance(output, dict):
            choices = output.get("choices", [])
            if choices:
                message = choices[0].get("message")
                if message and "content" in message:
                    return message["content"].strip()
                elif "text" in choices[0]:
                    return choices[0]["text"].strip()
        return ""

    def _build_inst_prompt(self, user_input):
        return f"[INST] <<SYS>>\nYou are a helpful assistant.\n<</SYS>>\n{user_input} [/INST]"

    def chat(self, user_input):
        t0 = time.time()
        reply = ""
        mem = 0
        try:
            # Try chat completion mode first
            if "chat" in self.model_path.lower() or "instruct" in self.model_path.lower():
                self.messages.append({"role": "user", "content": user_input})
                out = self.llm.create_chat_completion(
                    messages=self.messages,
                    max_tokens=512,
                    temperature=0.7,
                    top_p=0.9
                )
                reply = self._extract_text(out)
                if not reply:
                    reply = "(模型没有返回内容)"
                else:
                    self.messages.append({"role": "assistant", "content": reply})
            else:
                # Base mode with INST prompt
                prompt = self._build_inst_prompt(user_input)
                out = self.llm(
                    prompt,
                    max_tokens=512,
                    temperature=0.7,
                    top_p=0.9
                )
                reply = self._extract_text(out)
                if not reply:
                    reply = "(模型没有返回内容)"
                else:
                    self.messages.append({"role": "user", "content": user_input})
                    self.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            reply = f"(模型调用异常: {e})"
        dt = time.time() - t0
        mem = psutil.Process().memory_info().rss / (1024**2)
        return reply, dt, mem