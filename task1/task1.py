#!/usr/bin/env python3
from llama_cpp import Llama

MODEL_PATH = "./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

def main():
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,
        n_threads=8,
        n_gpu_layers=20,
        verbose=False
    )

    # 可调整的生成参数
    generation_params = {
        "temperature": 0.5,      # 控制随机性 (0.0-1.0)
        "top_p": 0.9,           # 核采样 (0.0-1.0)
        "top_k": 40,            # 保留前k个最可能的token
        "repeat_penalty": 1.1,   # 重复惩罚 (1.0=无惩罚)
        "max_tokens": 200,       # 最大生成token数
        "stop": ["Customer:", "Human:"]  # 停止词
    }

    print("🛍️ Shop Receptionist (Mistral-7B-Instruct)")
    print("Type 'clear' to reset, 'quit' to exit.")
    print("Type 'params' to adjust generation parameters.\n")

    instruction = (
        "You are a professional and helpful shop receptionist in a clothing & accessories store. "
        "Always answer politely and professionally. "
        "Always provide concrete and specific answers, avoid vague phrases like 'it depends' or 'it might vary'. "
        "If unsure, invent a reasonable price range to simulate a real shop receptionist. "
        "When asked about prices, always provide an estimated price range (e.g., jeans $40–$60, jackets $70–$120). "
        "If the customer asks about stock and the item is unavailable, politely explain and suggest alternatives. "
        "If asked about returns or exchanges, clearly explain the policy (e.g., within 14 days with receipt). "
        "Offer product recommendations based on the customer’s budget and preferences. "
        "Never talk about your own personal experiences, only store-related information."
    )

    # Message history for llama-cpp chat API
    messages = [{"role": "system", "content": instruction}]

    def show_params():
        print("\n📊 Current generated parameter:")
        for key, value in generation_params.items():
            print(f"  {key}: {value}")
        print()

    def adjust_params():
        print("\n🔧 Parameter adjustment (enter 'done' to complete):")
        show_params()
        while True:
            param = input("The name of the parameter to be adjusted (or 'done'): ").strip()
            if param.lower() == 'done':
                break
            if param in generation_params:
                try:
                    if param == "stop":
                        new_value = input(f"The new {param} value (separated by commas): ").strip()
                        generation_params[param] = [s.strip() for s in new_value.split(',') if s.strip()]
                    else:
                        new_value = float(input(f"The new {param} value: "))
                        generation_params[param] = new_value
                    print(f"✅ {param} has been updated to: {generation_params[param]}")
                except ValueError:
                    print("❌ Invalid value, please try again")
            else:
                print("❌ Unknown parameter, available parameters:", list(generation_params.keys()))
        show_params()

    while True:
        user = input("Customer: ").strip()
        if not user:
            continue
        if user.lower() in {"quit", "exit"}:
            break
        if user.lower() in {"clear", "reset"}:
            messages = [{"role": "system", "content": instruction}]
            print("Receptionist: I've reset our conversation. How can I help you today?\n")
            continue
        if user.lower() == "params":
            adjust_params()
            continue

        messages.append({"role": "user", "content": user})
        try:
            response = llm.create_chat_completion(
                messages=messages, 
                **generation_params  # 使用参数字典
            )
            reply = response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            reply = "Sorry, something went wrong. Please try again."

        if not reply:
            reply = "Sorry, could you rephrase that? I can help with sizes, prices, availability and returns."
        print(f"Receptionist: {reply}\n")
        messages.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    main()