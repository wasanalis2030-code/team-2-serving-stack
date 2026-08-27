import os
import time
import uuid

import torch
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_ID = os.environ.get(
    "MODEL_ID",
    "Qwen/Qwen2.5-0.5B-Instruct",
)
API_KEY = os.environ.get("API_KEY", "")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "256"))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"loading {MODEL_ID} on {DEVICE} ...", flush=True)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
model = model.to(DEVICE)
model.eval()

print("model ready", flush=True)


app = FastAPI(title="AIDC Serving API")


class ChatMessage(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    max_tokens: int = 64


def require_api_key(
    authorization: str | None = Header(default=None),
):
    if not API_KEY:
        return

    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_ID,
    }


@app.get(
    "/v1/models",
    dependencies=[Depends(require_api_key)],
)
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ID,
                "object": "model",
                "owned_by": "aidc",
            }
        ],
    }


@app.post(
    "/v1/chat/completions",
    dependencies=[Depends(require_api_key)],
)
def chat_completions(req: CompletionRequest):
    effective_max_tokens = min(
        max(req.max_tokens, 1),
        MAX_TOKENS,
    )

    messages = [
        message.model_dump()
        for message in req.messages
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
    ).to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=effective_max_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    prompt_tokens = inputs["input_ids"].shape[1]
    generated_tokens = outputs[0][prompt_tokens:]
    completion_tokens = generated_tokens.shape[0]

    content = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    ).strip()

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": MODEL_ID,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }