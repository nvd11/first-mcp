## Prerequisites

1. Python SDK version 12
2. Configure the Google API_KEY in your environment variables.

   For example:
   ```bash
   export GEMINI_API_KEY="AIzaxxxx...."
   ```

3. 如果你的地区有防火墙， 那么需要在环境变量中配置好科学上网
例如:
```bash
export https_proxy=http://10.0.1.223:7890
export http_proxy=http://10.0.1.223:7890
```

科学上网也可以在src/configs/proxy_config.py 里配置， 两者选一
