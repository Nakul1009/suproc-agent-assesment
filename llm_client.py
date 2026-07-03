import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
load_dotenv()
def llm_call(input: str):
    client = InferenceClient(
        api_key=os.getenv("HF_TOKEN"),
    )

    completion = client.chat.completions.create(
        model="Qwen/Qwen3-4B-Instruct-2507:nscale",
        messages=[
            {
                "role": "user",
                "content": input
            }
        ],
    )

    print(completion.choices[0].message)