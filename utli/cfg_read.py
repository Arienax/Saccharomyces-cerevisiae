import os
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

class ConfigBridge:
    def __init__(self):
        # 伪装成旧版的 cfg 对象，防止其他模块报错
        self.map_size = 3000
        self.card_num = os.getenv("SDVX_REFID", "")
        self.db_dir = "API_MODE_DISABLED"  # 随意填写，API 模式下已废弃
        self.game_dir = os.getenv("DIR_GAME_PATH", "")
        self.output = os.getenv("DIR_OUTPUT_PATH", "")
        self.skin_name = "gen6"
        self.language = "ZH"
        self.is_init = True
        self.version = 0

# 实例化伪装对象，供外部如 logger 或 draft 导入
cfg = ConfigBridge()