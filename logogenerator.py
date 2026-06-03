from PIL import Image

# 打开你的 PNG 图片
img = Image.open("PKU food recommender 正方形logo生成.png")

# 自动生成包含多尺寸的标准 ICO 图标
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save("my_logo.ico", sizes=icon_sizes)
print("ICO 图标制作成功！")