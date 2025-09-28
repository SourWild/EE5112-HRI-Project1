from gpt4all import GPT4All

# 推荐：Orca-mini-3B，Q4 量化版（约 3.6GB）
model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")

# 进入交互模式
with model.chat_session() as session:
    print("已进入 GPT4All 交互模式，输入 exit 或 quit 退出。\n")
    while True:
        user_input = input("你：")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("已退出 GPT4All 交互模式。")
            break
        response = session.generate(user_input, max_tokens=200)
        print("AI：", response)
