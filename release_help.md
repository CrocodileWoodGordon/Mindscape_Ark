这是一个非常明智的决定。对于包含资源文件（图片、音频）的游戏或应用，使用 **“文件夹模式” (Onedir)** 并打包成压缩包发布，通常比“单文件模式”更好，原因如下：

1. **启动速度更快**：单文件模式每次运行都要解压临时文件，文件夹模式则是直接运行。
2. **避免杀毒软件误杀**：单文件 exe 经常被 Windows Defender 拦截，文件夹模式这种情况少得多。
3. **方便调试**：用户如果遇到问题，可以看到资源文件夹是否存在。

以下是实现方案，分为 **代码调整** 和 **自动化工作流配置** 两部分。

---

### 第一步：代码调整（关键）

在使用 `PyInstaller --onedir` 模式打包后，你的文件结构会发生变化。你需要确保代码能正确找到 `assets` 文件夹。

请在你的 `src/core/settings.py` 或类似的配置工具文件中，使用以下代码来定位资源根目录：

```python
import sys
import os

def get_base_path():
    """
    获取项目根目录路径
    兼容：开发环境 (直接运行 python) 和 打包环境 (PyInstaller --onedir)
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境，sys.executable 指向 exe 文件
        # 资源文件夹就在 exe 所在的目录中
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，假设从项目根目录运行 (即包含 .git, src, assets 的目录)
        # 如果你是从 src/main.py 运行的，通常 os.getcwd() 就是项目根目录
        return os.path.abspath(".")

# 使用示例：
# BASE_PATH = get_base_path()
# IMAGE_PATH = os.path.join(BASE_PATH, "assets", "images", "player.png")

```

---

### 第二步：配置 GitHub Actions (自动打包并压缩)

你需要更新（或创建）`.github/workflows/build.yml` 文件。

这个配置会自动完成以下动作：

1. 安装环境。
2. 使用 PyInstaller 打包成**文件夹**。
3. 把文件夹**压缩**成 `.zip` (Windows/Mac) 或 `.tar.gz` (Linux)。
4. 发布到 GitHub Release。

请复制以下内容到 `.github/workflows/build.yml`：

```yaml
name: Build and Release Game

on:
  push:
    tags:
      - 'v*' # 仅当推送 v1.0, v0.0.1 等标签时触发

permissions:
  contents: write

jobs:
  build:
    name: Build for ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            platform_name: windows
            archive_ext: .zip
          - os: ubuntu-latest
            platform_name: linux
            archive_ext: .tar.gz
          - os: macos-latest
            platform_name: macos
            archive_ext: .zip

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11' # 保持跟你本地开发版本一致

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          # 如果你有 requirements.txt，请取消下面这行的注释
          # pip install -r requirements.txt
          # 临时演示，假设你需要 pygame 之类的，请务必生成 requirements.txt
          pip install pyinstaller

      # --- Windows 构建步骤 ---
      - name: Build (Windows)
        if: runner.os == 'Windows'
        run: |
          # --onedir: 打包成文件夹 (默认就是这个，写出来为了明确)
          # --noconsole: 游戏通常不需要黑框，如果是命令行工具去掉这个
          # --add-data: 把 assets 拷贝进去，格式是 "源路径;目标路径"
          pyinstaller --name MyGame --onedir --windowed --clean --noconfirm --add-data "assets;assets" src/main.py
          
          # 重命名 dist 下的文件夹，方便识别
          Rename-Item -Path "dist\MyGame" -NewName "MyGame-Windows"
          
          # 压缩文件夹
          Compress-Archive -Path "dist\MyGame-Windows" -DestinationPath "MyGame-Windows.zip"

      # --- Linux 构建步骤 ---
      - name: Build (Linux)
        if: runner.os == 'Linux'
        run: |
          # Linux 下分隔符是冒号 :
          pyinstaller --name MyGame --onedir --windowed --clean --noconfirm --add-data "assets:assets" src/main.py
          
          mv dist/MyGame dist/MyGame-Linux
          # 打包成 tar.gz
          cd dist
          tar -czvf ../MyGame-Linux.tar.gz MyGame-Linux/

      # --- macOS 构建步骤 ---
      - name: Build (macOS)
        if: runner.os == 'macOS'
        run: |
          # Mac 下分隔符是冒号 :
          pyinstaller --name MyGame --onedir --windowed --clean --noconfirm --add-data "assets:assets" src/main.py
          
          # Mac 下 --windowed 会生成 .app 包 (dist/MyGame.app)
          # 我们把这个 .app 放入一个文件夹再压缩，或者直接压缩
          cd dist
          zip -r ../MyGame-MacOS.zip MyGame.app

      # --- 上传构建产物到 Release ---
      - name: Upload to Release
        uses: softprops/action-gh-release@v1
        if: startsWith(github.ref, 'refs/tags/')
        with:
          files: |
            MyGame-Windows.zip
            MyGame-Linux.tar.gz
            MyGame-MacOS.zip
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

```

---

### 这里的关键配置说明

1. **`--onedir`**:
脚本中使用了 `--onedir` 参数。这会在 `dist/` 目录下生成一个文件夹（而不是一个文件）。
2. **`--add-data`**:
* Windows 写法: `"assets;assets"` (中间是分号)
* Linux/Mac 写法: `"assets:assets"` (中间是冒号)
* 这一步非常重要，它会把你的 `assets` 文件夹完整拷贝到生成的程序文件夹内部。


3. **压缩命令**:
* **Windows**: 使用了 PowerShell 自带的 `Compress-Archive`。
* **Linux**: 使用了标准的 `tar -czvf`。
* **Mac**: 使用了 `zip -r` (注意 Mac 上生成的是 `.app` 这是一个特殊的文件夹，看起来像文件，其实是文件夹)。



### 下一步操作

1. **生成 requirements.txt**:
GitHub 的机器上是干净的，不知道你用了什么库。如果你在本地用 `uv`，请运行：
```bash
uv pip freeze > requirements.txt

```


并把这个文件提交到仓库。
2. **提交并打标签发布**:
```bash
git add .
git commit -m "Add build workflow"
git push

# 打标签触发发布
git tag v1.0.0
git push origin v1.0.0

```



稍等几分钟，你就可以在 GitHub 仓库右侧的 **"Releases"** 看到 `v1.0.0`，里面会有三个压缩包，下载解压后即可直接运行！
