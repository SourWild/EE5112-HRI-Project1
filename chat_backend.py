"""Backend helpers for running local llama.cpp models in a chat loop."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import psutil
from llama_cpp import Llama

DEFAULT_MODEL = "./models/orca-mini-3b.Q4_0.gguf"
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
_CHAT_MODEL_KEYWORDS = (
    "chat",
    "instruct",
    "assistant",
    "alpaca",
    "vicuna",
    "zephyr",
    "openhermes",
    "orca",
)


class ChatBot:
    """High-level helper that wraps llama.cpp for interactive chatting."""

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL,
        *,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        history_pairs: int = 8,
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = 20,
        verbose: bool = False,
        llm_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.model_path = model_path
        self.system_prompt = system_prompt
        self.history_pairs = max(history_pairs, 0)
        self._process = psutil.Process()
        base_config: Dict[str, Any] = dict(
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=verbose,
        )
        if llm_kwargs:
            base_config.update(llm_kwargs)
        self._llm_config = base_config
        self.llm: Optional[Llama] = None
        self.mode: str = "base"
        self.messages: List[Dict[str, str]] = []
        self.load_model()

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------
    def _guess_mode(self, filename: str) -> str:
        name = os.path.basename(filename).lower()
        if any(keyword in name for keyword in _CHAT_MODEL_KEYWORDS):
            return "chat"
        return "base"

    def load_model(self) -> None:
        config = dict(self._llm_config)
        config["model_path"] = self.model_path
        self.llm = Llama(**config)
        self.mode = self._guess_mode(self.model_path)
        self.reset()

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _extract_text(self, output: Dict[str, Any]) -> str:
        try:
            choices = output.get("choices", [])
            if not choices:
                return ""
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content", "")
                    if content:
                        return content
                text = first.get("text", "")
                if text:
                    return text
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[ChatBot] Failed to extract text: {exc}")
        return ""

    def _build_inst_prompt(self, user_input: str, history_limit: Optional[int] = None) -> str:
        limit = self.history_pairs if history_limit is None else max(history_limit, 0)
        dialog = []
        user_buffer: Optional[str] = None
        for msg in self.messages[1:]:
            role, content = msg.get("role"), msg.get("content", "")
            if role == "user":
                user_buffer = content
            elif role == "assistant" and user_buffer is not None:
                dialog.append((user_buffer, content))
                user_buffer = None
        dialog = dialog[-limit:]
        header = f"<<SYS>>\n{self.system_prompt}\n<</SYS>>\n"
        body_lines = ["User: {}\nAssistant: {}\n".format(u, a) for u, a in dialog]
        body_lines.append(f"User: {user_input}\nAssistant:")
        return f"[INST] {header}{''.join(body_lines)} [/INST]"

    def _trim_history(self) -> None:
        if self.history_pairs <= 0:
            return
        # Keep last N user/assistant pairs plus potential trailing user message
        keep = [self.messages[0]]
        convo = self.messages[1:]
        max_messages = self.history_pairs * 2
        if len(convo) <= max_messages:
            self.messages = keep + convo
            return
        self.messages = keep + convo[-max_messages:]

    def _call_text_completion(
        self,
        user_input: str,
        *,
        temperature: float,
        top_p: float,
        max_tokens: int,
        repeat_penalty: float,
        record_user: bool = True,
    ) -> str:
        assert self.llm is not None, "Model not loaded"
        prompt = self._build_inst_prompt(user_input)
        output = self.llm(
            prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            repeat_penalty=repeat_penalty,
        )
        reply = self._extract_text(output).strip()
        if record_user:
            self.messages.append({"role": "user", "content": user_input})
        self.messages.append({"role": "assistant", "content": reply})
        self._trim_history()
        return reply

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def chat(
        self,
        user_input: str,
        *,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512,
        repeat_penalty: float = 1.1,
    ):
        assert self.llm is not None, "Model not loaded"
        start = time.time()
        reply = ""
        try:
            if self.mode == "chat":
                self.messages.append({"role": "user", "content": user_input})
                output = self.llm.create_chat_completion(
                    messages=self.messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    repeat_penalty=repeat_penalty,
                )
                reply = self._extract_text(output).strip()
                if not reply:
                    reply = self._call_text_completion(
                        user_input,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                        repeat_penalty=repeat_penalty,
                        record_user=False,
                    )
                else:
                    self.messages.append({"role": "assistant", "content": reply})
                    self._trim_history()
            else:
                reply = self._call_text_completion(
                    user_input,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    repeat_penalty=repeat_penalty,
                )
        except Exception as exc:
            reply = f"(模型调用异常: {exc})"

        if not reply:
            reply = "(模型没有返回内容)"

        elapsed = time.time() - start
        mem_mb = self._process.memory_info().rss / (1024 ** 2)
        return reply, elapsed, mem_mb
