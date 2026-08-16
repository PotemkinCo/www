# Build requirements

Linux
```bash
sudo apt-get install libssl-dev libcurl4-openssl-dev
```
Required to get SSL to download models.

## Check properties of the running system

```bash
http://localhost:18880/props
```

Shows templates, thinking, etc.

# Models recipies

## gpt-oss-20b

For NVIDIA RTX 4000 SFF Ada Generation with 20Gb:
``
```bash
/root/llama-server/llama-server -hf unsloth/gpt-oss-20b-GGUF:F16 --jinja -ub 2048 -b 2048 --ctx-size 131000 -fa on
```
## qwen-3-8b

For 13th Gen Intel(R) Core(TM) i5-13500:
```bash
/usr/bin/numactl -C 0-11 /root/llama-server-cpu/llama-server -hf unsloth/Qwen3-8B-GGUF -hff Qwen3-8B-UD-Q2_K_XL.gguf --threads 12 --mlock --no-mmap --ctx-size 32768 --flash-attn on --host 127.0.0.1 --port 18880 --n-gpu-layers 0 --chat-template chatml
```

Tests - at [[2026-02-03]].
Refs: [UnSloth Docs](https://unsloth.ai/docs/models/qwen3-how-to-run-and-fine-tune#llama.cpp-run-qwen3-tutorial), [GGUF repo](https://huggingface.co/unsloth/Qwen3-8B-GGUF/tree/main), [perplexity ref](https://www.perplexity.ai/search/may-i-use-some-bert-models-mod-t68aVKyeT6a5T7AjKbwkPQ).

---

More at: [[2025-08-29]] & [[2025-08-30]]

Quick start:
```bash
sudo apt update
sudo apt install -y gcc g++ make curl git python3-pip python3-venv
wget -O server-llm.sh https://github.com/ggerganov/llama.cpp/blob/master/scripts/server-llm.sh?raw=true && chmod +x server-llm.sh

cd __llama_cpp_port_8888__
make LLAMA_SERVER_SSL=true server

~/__llama_cpp_port_8888__/server -m mistral-7b-v0.1.Q8_0.gguf -c 2048 --host 0.0.0.0 --port 8888 --mlock --threads 12 --api-key <your-api-key>

# from https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/tree/main
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q8_0.gguf?download=true
mv 'mistral-7b-instruct-v0.1.Q8_0.gguf?download=true' mistral-7b-instruct-v0.1.Q8_0.gguf

nohup ~/__llama_cpp_port_8888__/server -m mistral-7b-instruct-v0.1.Q8_0.gguf -c 2048 --host 0.0.0.0 --port 8888 --no-mmap --threads 12 --api-key <your-api-key> &

curl --request POST \
    --url http://localhost:8888/completion \
    --header "Content-Type: application/json" \
    -H 'Authorization: Bearer <your-api-key>' \
    --data '{"prompt": "Tell me a meaning of life"}'
```

=> <server-ip>

```bash
curl --request POST \
    --url http://<server-ip>:8888/completion \
    --header "Content-Type: application/json" \
    -H 'Authorization: Bearer <your-api-key>' \
    --data '{"prompt": "Tell me a meaning of life"}'
```

Memory is barely used for the interference... I shall check if that could be adjusted... 


Ref:
- llama.cpp issue on [memory not fully used](https://github.com/ggerganov/llama.cpp/issues/2589): `--no-mmap` flag comes from there