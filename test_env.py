import os
from dotenv import load_dotenv

# 加载 .env
load_dotenv()


print("API地址:", os.getenv("ASPHYXIA_API_URL"))
print("玩家卡号:", os.getenv("SDVX_REFID"))
print("玩家昵称:", os.getenv("SDVX_USER_NAME"))