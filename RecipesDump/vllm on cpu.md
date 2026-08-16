as per [[2025-09-05]]:

Follow [official doc](https://docs.vllm.ai/en/stable/getting_started/installation/cpu.html#build-wheel-from-source)

Changing the following command only:
`uv pip install -r requirements/cpu.txt --torch-backend cpu --index-strategy unsafe-best-match` 
 `vllm serve nanonets/Nanonets-OCR-s --max-model-len=116480`

```start.sh
#!/bin/bash
SCRIPTDIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
cd $SCRIPTDIR

source .venv/bin/activate
vllm serve nanonets/Nanonets-OCR-s --max-model-len=116480 --host 127.0.0.1 --port 8000
```

```vllm_ocr.service
[Unit]
Description=vLLM for Nanonets OCR
After=multi-user.target

[Service]
User=alex
Group=alex
Type=simple
ExecStart=/opt/vllm/start.sh
Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp *.service /etc/systemd/system
sudo systemctl enable vllm_ocr
sudo systemctl start vllm_ocr
sudo systemctl status vllm_ocr
sudo ss -tulnp | grep 8000
```
