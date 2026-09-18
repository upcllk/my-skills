---
name: gif-transparent-background
description: 使用 Pillow 和 rembg 逐帧去除现有 GIF 的背景，输出透明 GIF 或 WebP；保留原角色、画布和动画时序，不用于 AI 重绘。
---

# GIF 背景透明化

当用户要把已有 GIF 的背景变透明时使用本 skill。目标是保留原始动画内容并逐帧生成 Alpha 遮罩，不是重新生成或重绘图片。

## 原理

对话中确认的处理流程是：

1. 用 `Pillow` 打开 GIF，通过 `ImageSequence.Iterator` 逐帧读取。
2. 每帧转换为 `RGBA`，编码成 PNG bytes，交给 `rembg.remove()` 做前景分割。
3. 将返回的 PNG 解码为 `RGBA`，收集所有处理后的帧。
4. 使用原始帧时长、循环次数和固定画布重新编码为 GIF 或 WebP。

该流程会改变每帧的透明遮罩，但不会让 AI 重新绘制角色。逐帧分割可能造成边缘轻微闪烁，应检查结果。

## Skill 内的可执行入口

稳定入口是：

```text
bin/remove-gif-background
```

它不是第三方包，也不是平台专用的原生二进制，而是一个随 skill 分发的可执行 Python launcher。它通过自身位置解析 skill 根目录，再调用：

```text
scripts/remove_gif_background.py
```

这样调用者不需要把当前工作目录切换到 skill 目录。入口源码如下，文件本身也保存在 `bin/remove-gif-background`：

```python
#!/usr/bin/env python3
"""Portable skill entry point; locate the bundled implementation by path."""

from pathlib import Path
import subprocess
import sys


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "remove_gif_background.py"

raise SystemExit(subprocess.call([sys.executable, str(SCRIPT), *sys.argv[1:]]))
```

真正的图片转换逻辑位于 `scripts/remove_gif_background.py`。入口使用当前调用它的 Python 解释器，因此可以配合虚拟环境使用。

## 依赖和配置

依赖清单在：

```text
requirements.txt
```

当前依赖为：

```text
Pillow>=10.0
rembg[cpu]>=2.0.50
```

- `Pillow`：读取 GIF、迭代帧、保留时长并输出 GIF/WebP。
- `rembg[cpu]`：提供前景分割逻辑和 CPU 版 `onnxruntime` 后端。GPU 环境可以按目标平台替换为合适的 `rembg` extra。
- 默认模型：`u2netp`，内存和下载体积较小；需要更高质量时传入 `--model u2net`。
- 第一次运行会按需下载模型。模型权重不提交进 skill，因为它们较大，并且和运行平台、模型版本有关。
- 默认模型缓存由 `rembg` 管理。可用 `REMBG_HOME` 指定缓存根目录；兼容旧配置时也可用 `U2NET_HOME`。如果没有设置，当前版本通常使用用户目录下的 `.rembg/models/<model>`。

## 没有依赖时的安装

推荐在 skill 外部创建虚拟环境，不把虚拟环境目录提交到 skill：

macOS/Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r /path/to/gif-transparent-background/requirements.txt
```

Windows PowerShell：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r C:\path\to\gif-transparent-background\requirements.txt
```

如果出现 `No onnxruntime backend found`，说明没有安装带后端的 extra，应重新执行：

```bash
python3 -m pip install "rembg[cpu]"
```

如果模型下载失败，可以先设置模型缓存目录并重试：

```bash
export REMBG_HOME=/path/to/rembg-cache
```

Windows PowerShell 对应：

```powershell
$env:REMBG_HOME = "C:\path\to\rembg-cache"
```

## 使用方式

```bash
.venv/bin/python /path/to/gif-transparent-background/bin/remove-gif-background \
  input.gif --output transparent.gif

.venv/bin/python /path/to/gif-transparent-background/bin/remove-gif-background \
  input.gif --output transparent.webp
```

也可以指定模型：

```bash
.venv/bin/python /path/to/gif-transparent-background/bin/remove-gif-background \
  input.gif --output transparent.webp --model u2net
```

处理时应保持原始画布尺寸、帧顺序、帧时长和循环行为，除非用户明确要求改变。脚本会复用同一个 `rembg` model session；不能为每一帧重新创建 session，否则会显著增加内存占用。

GIF 的透明度通常只有透明/不透明两档，边缘可能锯齿；目标环境支持时优先输出 animated WebP，以保留更平滑的 Alpha。

不要为此任务调用 image-generation 工具，也不要把“去背景”误做成重新绘图。

## 随 skill 保存的示例

`assets/examples/` 包含原始附件和通过本 skill 入口生成的结果：

- `original.gif`：108×144，原始 86 帧 GIF。
- `transparent.gif`：透明 GIF 结果。
- `transparent.webp`：无损 animated WebP 结果。

GIF/WebP 编码器可能合并内容完全相同的相邻帧，因此编码后的帧数可能低于原始帧数，但帧时长和循环信息会保留。

对话中没有保存原始执行脚本文件；当前实现是依据对话中可见代码路径重建并增强后的版本。
