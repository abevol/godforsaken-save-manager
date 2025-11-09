# 《神弃之地》存档备份管理器

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/abevol/godforsaken-save-manager?style=for-the-badge)](https://github.com/abevol/godforsaken-save-manager/releases/latest)
[![Build Status](https://img.shields.io/github/actions/workflow/status/abevol/godforsaken-save-manager/release.yml?style=for-the-badge)](https://github.com/abevol/godforsaken-save-manager/actions/workflows/release.yml)

**支持语言：** 简体中文, English

---

## 📖 简介

**《神弃之地》存档备份管理器** 是一款专为游戏《神弃之地》(GodForsaken) 设计的图形化存档管理工具。通过本工具，玩家可以轻松、安全地备份、恢复和管理多个游戏存档。

本工具是早期 `备份/恢复存档.bat` 脚本的升级版，提供了更强大、更安全、更直观的功能。

## ✨ 主要功能

- **一键备份**：快速将当前游戏进度创建一个安全的备份。
- **存档恢复**：从历史备份列表中轻松选择并恢复任意存档。
- **自动备份**：在执行恢复操作前，自动为当前存档创建备份，防止误操作导致进度丢失。
- **可视化管理**：清晰的列表展示所有历史备份，可为每个备份添加备注，方便识别。
- **安全保护机制**：
  - **进程检测**：在操作前自动检测游戏是否正在运行，避免存档损坏。
  - **恢复确认**：当恢复的存档与当前进度时间跨度较大时，会弹出二次确认，防止恢复到意料之外的旧存档。
- **自动更新**：程序启动时自动检查新版本，并可一键下载更新，始终保持最佳体验。
- **多语言支持**：支持简体中文和英文，可自动检测系统语言或在设置中手动切换。
- **高度可配置**：
  - 自定义游戏存档与备份路径。
  - 设定最大备份数量，自动清理旧备份。
  - 恢复后可选择是否自动启动游戏。

## 🚀 如何使用

### 1. 下载

前往本项目的 [**Releases 页面**](https://github.com/abevol/godforsaken-save-manager/releases/latest)下载最新的 `GodForsakenSaveManager.exe` 文件。

### 2. 准备工作：关闭 Steam 云同步

为确保本工具能正常管理本地存档，必须关闭《神弃之地》的 Steam 云同步功能。

1. 在 Steam 游戏库中右键点击《神弃之地》。
2. 选择 **“属性”** -> **“通用”**。
3. 关闭 **“将游戏存档保存于 Steam 云”** 选项。

### 3. 首次运行与配置

1. 将下载的 `.exe` 文件放置在任意位置并运行。
2. 首次运行时，工具会尝试自动查找游戏存档路径。如果未找到，请点击 **“设置”** 按钮。
3. 在设置界面中，手动指定 **“游戏存档路径”** 和 **“备份存储路径”**。
    - 默认存档路径通常位于：`C:\Users\<你的用户名>\AppData\LocalLow\InsightStudio\GodForsakenRelease\game_save`
4. 根据需要调整其他设置，如语言、最大备份数等，然后点击 **“保存”**。

### 4. 日常操作

> **⚠️ 重要提示：在执行任何备份或恢复操作前，请务必先退出游戏！**

- **备份存档**：在游戏退出后，点击主界面的 **“备份当前存档”** 按钮。你可以在弹出的对话框中为这次备份添加备注（例如：“腐化前”、“领取装备奖励前”）。
- **恢复存档**：
    1. 直接点击主界面的 **“恢复最近存档”** 按钮；或者在历史存档列表中，找到你想要恢复的存档点，点击对应条目右侧的 **“恢复”** 按钮。
    2. 根据提示确认操作，工具会自动完成存档覆盖。
    3. 如果设置中开启了“恢复后自动启动游戏”，游戏将会自动运行。

## 👨‍💻 面向开发者

如果你希望参与开发或自行构建，请遵循以下步骤。

### 1. 环境准备

- [Python 3.11+](https://www.python.org/)
- [Poetry](https://python-poetry.org/) (包管理工具)

### 2. 安装依赖

克隆本仓库，然后在项目根目录下运行：

```bash
poetry install
```

### 3. 运行程序

```bash
poetry run godforsaken-save-manager
```

### 4. 构建可执行文件

本项目使用 [Nuitka](https://nuitka.net/) 进行编译，以生成单文件 `.exe`。

运行根目录下的 `build.bat` 脚本即可：

```bash
.\build.bat
```

构建成功后，`GodForsakenSaveManager.exe` 文件会出现在 `build` 目录下。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。
