# TIF 转 MP4 工具

## 功能
将图像序列（如 tif、png、jpg 等）组合成 MP4 视频文件。

## 使用方法

### 基本用法
```bash
python3 convert.py --input /path/to/images
```

### 指定帧率
```bash
python3 convert.py --input /path/to/images --fps 10
```

### 指定输出文件名
```bash
python3 convert.py --input /path/to/images --output my_video.mp4
```

## 输出

- 视频格式：MP4
- 默认输出路径：`output/` 目录
- 默认文件名：`YYYYMMDDhhmmss.mp4`（时间戳格式）

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input`, `-i` | 输入图像目录（必需） | - |
| `--output`, `-o` | 输出视频路径 | `output/YYYYMMDDhhmmss.mp4` |
| `--fps` | 帧率 | 10 |
| `--pattern` | 图像文件名模式 | `t*.tif` |

## 示例

```bash
# 转换指定目录的图片
python3 convert.py --input /path/to/images

# 设置帧率为 15
python3 convert.py --input /path/to/images --fps 15

# 转换 PNG 图片
python3 convert.py --input /path/to/images --pattern "*.png"
```

## 注意事项

- 图片文件名必须能按字母顺序排序
- 所有图片应具有相同的分辨率
- 需要安装 OpenCV：`pip install opencv-python`