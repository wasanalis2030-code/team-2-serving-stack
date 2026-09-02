# Model lock (team record)

## The locked model

- Model id: Qwen/Qwen2.5-1.5B-Instruct-AWQ
- Quantisation: awq
- Why this one: AWQ passed the smoke test with 10/10, maintained acceptable quality, and achieved higher throughput.

## The launch flags

--model Qwen/Qwen2.5-1.5B-Instruct-AWQ --dtype half --max-model-len 4096
--gpu-memory-utilization 0.85 --quantization awq
--enable-auto-tool-choice --tool-call-parser hermes
--disable-frontend-multiprocessing --port 8000

- Tool-call parser: hermes

## The smoke score

- Score (valid behaviours out of 10): 10
- Distractor stayed call-free in the majority: yes
- Passed the gate: yes
- Measured against: AWQ 10/10 and fp16 10/10.

## Quality spot check note

- AWQ produced clear and relevant answers across all five prompts. No meaningful quality degradation was observed.