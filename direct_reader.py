import json
import os
import cv2

# --- 配置你的实际路径 ---
JSON_PATH = r'D:\Download\sdvxbot\music\music_db.json'  # 你的 json 文件路径
JK_DIR = r'D:\Download\sdvxbot\jk'               # 你的封面文件夹路径
# ------------------------

class SDVXDataReader:
    def __init__(self):
        self.music_db = {}
        self._load_json()

    def _load_json(self):
        """一次性加载 JSON 到内存字典"""
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 精确解析嵌套结构：data -> mdb -> music -> [歌曲列表]
            if isinstance(data, dict) and 'mdb' in data and 'music' in data['mdb']:
                song_list = data['mdb']['music']
            elif isinstance(data, list):
                song_list = data
            else:
                song_list = []

            self.music_db = {}
            for song in song_list:
                if isinstance(song, dict) and 'id' in song:
                    try:
                        self.music_db[int(song['id'])] = song
                    except (ValueError, TypeError):
                        continue
    def get_music_info(self, mid):
        """获取曲目名和特殊版本号"""
        song = self.music_db.get(int(mid))
        if not song:
            return "Unknown Song", "2"  # 找不到时返回默认值防崩溃

        title = song['info']['title_name']
        inf_ver = song['info']['inf_ver']
        return title, inf_ver

    def get_difficulty_level(self, mid, diff_index):
        """
        获取定数。
        diff_index 对应: 0=NOV, 1=ADV, 2=EXH, 3=INF/GRV/HVN/VVD, 4=MXM
        """
        song = self.music_db.get(int(mid))
        if not song:
            return 0

        diff_keys = ['novice', 'advanced', 'exhaust', 'infinite', 'maximum']
        try:
            key = diff_keys[diff_index]
            level_str = song['difficulty'][key]
            # 有些定数可能是 "17.5"，先转 float 再转 int 或保留 float 根据画图需求
            return int(float(level_str))
        except (KeyError, IndexError, ValueError):
            return 0

    def get_jacket_image(self, mid, diff_index):
        """读取对应的封面图片"""
        # diff_index 是 0~4，对应的图片后缀是 1~5
        file_diff = diff_index + 1
        jk_filename = f"jk_{int(mid):04d}_{file_diff}_b.png"
        jk_path = os.path.join(JK_DIR, jk_filename)

        # 如果当前难度封面不存在（例如只有 NOV 封面），强制降级找第 1 张图
        if not os.path.exists(jk_path):
            jk_path = os.path.join(JK_DIR, f"jk_{int(mid):04d}_1_b.png")

        if os.path.exists(jk_path):
            return cv2.imread(jk_path, cv2.IMREAD_UNCHANGED)
        else:
            return None # 彻底找不到图，返回 None 交给画图程序处理默认图