import os

from openai import AsyncOpenAI

import httpx
import socksio

# response = OpenAI(api_key =  'XXX',
# http_client=httpx.Client(
#         proxies="socks5://prod:31egbedof@80.209.240.32:1080"))

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PROXY_URL = os.getenv('PROXY_URL')


openai_client = AsyncOpenAI(
    http_client=httpx.AsyncClient(
        proxies=PROXY_URL))