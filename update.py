from update.db import update_db
from update.img import update_img

game_path = 'E:/BaiduNetdiskDownload/SDVX7-2026020300'

print("正在强制更新 7 代数据库，请稍候...") 
update_db(game_path, 3000)
print("数据库更新完成！\n")

print("正在提取 7 代图像素材 (这步需要解包 ifs 文件，可能需要几分钟)...")
# 强行更新图像，假设你用的是 6 代(gen6)皮肤模板
update_img(game_path, 'gen6') 
print("图像提取完成！所有更新大功告成！")