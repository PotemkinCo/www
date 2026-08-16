```bash
curl -fsSL https://ollama.com/install.sh| sh
ollama run llama3.1:405b-instruct-fp16
	/set parameter num_thread 64
/set verbose
curl http://localhost:11434/api/generate -d '{"model": "llama3.1:405b-instruct-fp16", "keep_alive": -1}'
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:405b-instruct-fp16",
  "prompt": "Why 42",
  "stream": true,
  "options": {
    "num_thread": 64,
    "verbose": true
  }
}'
```

## Closing with token auth with Caddy

```Caddyfile
#TODO: try that recipe: https://caddy.community/t/how-to-verify-header-for-getting-successful-response/13066/3  
llama.example.com debug {  
       import logging llama.example.com  
  
       @no_api_token {  
               not {  
                       header Authorization "Bearer <your-api-token>"  
                       header User-Agent ollama-python*  
               }  
       }  
  
       respond @no_api_token "Nop!" 402 {  
               close  
       }  
  
       reverse_proxy 127.0.0.1:11434 {  
               header_up Host localhost:11434  
       }  
  
}
```