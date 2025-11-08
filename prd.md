# 🧭 产品文档

## 一、产品概述

**名称：** 神弃之地存档备份管理器（GodForsaken Save Backup Manager）
**版本：** v1.0
**目标用户：** 《神弃之地》正式版玩家
**目标：**

* 提供高安全性、高效率的本地存档备份与恢复系统
* 可视化管理历史存档
* 预防误操作（尤其是误恢复）带来的存档丢失问题

---

## 二、主要功能

| 功能            | 说明                                                                |
| ------------- | ----------------------------------------------------------------- |
| **手动备份**      | 将当前存档复制为 `game_save_my_bak\manual\YYYY-MM-DD_HH-MM-SS` 格式目录。             |
| **自动备份（恢复前）** | 恢复存档时，若当前存档未存在备份，则自动创建于 `game_save_my_bak\auto\YYYY-MM-DD_HH-MM-SS`。 |
| **备注系统**      | 用户可在历史存档列表中为备份添加/修改备注。自动备份将自动标注 `[自动备份]`。                                |
| **历史存档列表**    | 显示所有备份（含自动备份），按存档修改时间倒序排列。备注栏即用于区分手动/自动备份。                        |
| **最大历史数限制**   | 超过配置上限时，自动删除最早的备份。                                                |
| **恢复保护**      | 恢复前自动检测当前游戏进程状态、执行必要的保护性自动备份。                                     |
| **意外恢复保护**      | 恢复前检测目标备份与当前存档的文件修改时间差值，如果超过恢复确认阈值，则提醒用户确认，以防止进行了意料之外的存档恢复    |
| **配置系统**      | 可设置路径、最大数量、恢复确认阈值、自动启动游戏等选项；所有配置与备注持久化。                                  |
| **自动启动游戏**    | 恢复完成后可选自动执行 `steam://rungameid/3419290`。                          |

---

## 三、UI 设计

### 主界面布局

```
+-------------------------------------------------------------+
| [备份存档] [恢复存档] [设置]            |
|-------------------------------------------------------------|
| 历史存档列表（按修改时间倒序）                             |
|-------------------------------------------------------------|
| 时间              | 备注                     | 操作           |
|-------------------------------------------------------------|
| 2025-11-06_20-05-15 | [自动备份] 恢复前自动生成 | [恢复] [删除] |
| 2025-11-06_18-55-22 | 腐化前备份               | [恢复] [删除] |
| 2025-11-06_18-30-47 | 首次备份                 | [恢复] [删除] |
+-------------------------------------------------------------+
```

---

### 设置界面

```
+------------------------------------------+
| 存档路径: [_________________________] [选择] |
| 备份路径: [_________________________] [选择] |
| 最大历史数量: [ 20 ]                       |
| 恢复确认阈值(分钟): [ 20 ]                 |
| 自动启动游戏 [√]                           |
|------------------------------------------|
| [保存设置] [取消]                         |
+------------------------------------------+
```

---

## 四、配置文件设计

路径：
`{backup_root_path}\backup_manager_config.json`
（默认位置：`%USERPROFILE%\AppData\LocalLow\InsightStudio\GodForsakenRelease\game_save_my_bak\backup_manager_config.json`）

### JSON 示例

```json
{
  "game_save_path": "C:\\Users\\User\\AppData\\LocalLow\\InsightStudio\\GodForsakenRelease\\game_save",
  "backup_root_path": "C:\\Users\\User\\AppData\\LocalLow\\InsightStudio\\GodForsakenRelease\\game_save_my_bak",
  "last_backup": "",
  "max_history": 20,
  "restore_confirm_threshold_minutes": 20,
  "auto_launch_game": true,
  "notes": {
    "2025-11-06_18-30-47": "腐化前备份",
    "2025-11-06_19-10-03": "[自动备份] 恢复前自动生成"
  }
}
```

---

## 五、逻辑流程

### 手动备份

```
→ 检测 GodForsaken.exe 是否运行
→ 读取 ProfileBrief.ssp 修改时间
→ 比较是否已存在相同时间戳的备份
→ 若无重复：
     创建目录 YYYY-MM-DD_HH-MM-SS
     复制文件
     更新 last_backup
→ 根据设置是否启动游戏
→ 刷新 UI 列表
```

### 恢复存档

```
→ 检测 GodForsaken.exe 是否运行
→ 读取当前 ProfileBrief.ssp 修改时间
→ 计算目标备份存档的修改时间与当前存档修改时间的差值（分钟）
→ 如果差值超过配置的阈值（restore_confirm_threshold_minutes），则弹出确认对话框，用户确认后才继续，否则中止
→ 若未存在对应备份：
     自动执行一次自动备份（备注 [自动备份]）
→ 执行恢复操作（覆盖 game_save）
→ 更新 last_backup
→ 根据设置是否启动游戏
→ 刷新 UI 列表
```

---

# 🧱 架构文档（分层版）

## 一、项目目录结构

```
godforsaken-save-manager/
│
├─ pyproject.toml
├─ README.md
├─ src/
│  ├─ godforsaken_save_manager/
│  │  ├─ __init__.py
│  │  │
│  │  ├─ core/                    # 业务逻辑核心层
│  │  │  ├─ backup_manager.py     # 备份/恢复/删除逻辑
│  │  │  ├─ config_manager.py     # 配置管理（含默认值逻辑）
│  │  │  ├─ process_checker.py    # 游戏进程检测
│  │  │  ├─ file_operations.py    # 文件复制、比对、清理等操作
│  │  │  └─ backup_entry.py       # 数据结构定义（BackupEntry）
│  │  │
│  │  ├─ ui/                      # 界面层
│  │  │  ├─ main_window.py        # 主窗口（历史列表与按钮）
│  │  │  ├─ settings_window.py    # 设置窗口
│  │  │  ├─ resources.qrc         # 图标资源
│  │  │  └─ style.qss             # 样式表
│  │  │
│  │  ├─ common/                  # 通用支持层
│  │  │  ├─ constants.py          # 常量定义（路径模板、文件名等）
│  │  │  └─ helpers.py            # 公共小函数（时间戳格式化、日志等）
│  │  │
│  │  └─ main.py                  # 程序入口
│  │
│  └─ tests/                      # 单元测试
│     ├─ test_backup_manager.py
│     ├─ test_config_manager.py
│     └─ test_file_operations.py
```

---

## 二、模块说明

### `core/backup_entry.py`

定义数据结构：

```python
@dataclass
class BackupEntry:
    path: Path
    timestamp: str        # "2025-11-06_18-30-47"
    note: str
    profile_mtime: datetime
```

---

### `core/config_manager.py`

负责加载与保存 `backup_manager_config.json`，并填充默认值。

```python
DEFAULTS = {
    "game_save_path": "%USERPROFILE%\\AppData\\LocalLow\\InsightStudio\\GodForsakenRelease\\game_save",
    "backup_root_path": "%USERPROFILE%\\AppData\\LocalLow\\InsightStudio\\GodForsakenRelease\\game_save_my_bak",
    "last_backup": "",
    "max_history": 20,
    "restore_confirm_threshold_minutes": 20,
    "auto_launch_game": True,
    "notes": {}
}
```

提供接口：

```python
def load_config() -> dict
def save_config(config: dict)
def ensure_defaults(config: dict) -> dict
```

---

### `core/backup_manager.py`

核心逻辑类：

```python
class BackupManager:
    def backup(self, note: str = "", auto: bool = False) -> str
    def restore(self, target_path: Path)
    def delete(self, target_path: Path)
    def list_backups(self) -> List[BackupEntry]
    def get_time_diff(self, target_path: Path) -> float  # 返回时间差值（分钟）
```

内部自动：

* 检测游戏进程（`process_checker`）
* 自动调用 `file_operations.copy_directory`
* 更新 `config_manager`
* 维护最大数量限制

---

### `core/process_checker.py`

检测游戏进程：

```python
import psutil

def is_game_running() -> bool:
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == "GodForsaken.exe":
            return True
    return False
```

---

### `core/file_operations.py`

封装文件操作：

```python
def copy_directory(src: Path, dst: Path)
def remove_directory(path: Path)
def get_profile_timestamp(path: Path) -> datetime
```

---

### `ui/main_window.py`

PySide6 主界面逻辑：

* 表格显示历史存档（时间、备注、操作按钮）
* 绑定按钮事件（备份、恢复、删除、设置）
* 恢复前检查时间差值并确认

---

### `ui/settings_window.py`

提供：

* 路径选择（QFileDialog）
* 数值输入（最大历史数量、恢复确认阈值）
* 复选框（自动启动游戏）
* 保存配置并刷新主界面

---

### `common/helpers.py`

常用辅助：

```python
def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d_%H-%M-%S")
```

---

## 三、Poetry + Nuitka

### `pyproject.toml`

```toml
[tool.poetry]
name = "godforsaken-save-manager"
version = "1.0.0"
description = "A save management tool for GodForsaken"
authors = ["七夜听雪 <example@example.com>"]
packages = [{ include = "godforsaken_save_manager", from = "src" }]

[tool.poetry.dependencies]
python = "^3.11"
PySide6 = "^6.7.0"
psutil = "^5.9.8"

[tool.poetry.scripts]
godforsaken-save-manager = "godforsaken_save_manager.main:main"
```

---

### Nuitka 编译命令

```bash
poetry run nuitka \
  --onefile \
  --enable-plugin=pyside6 \
  --include-data-dir=src/godforsaken_save_manager/ui/resources=resources \
  --output-filename=GodForsakenSaveManager.exe \
  src/godforsaken_save_manager/main.py
```

---

## ✅ 特点总结

| 类别   | 优点                                    |
| ---- | ------------------------------------- |
| 架构   | 分层清晰：`core`（业务）、`ui`（界面）、`common`（工具） |
| UI   | 简洁：仅展示时间与备注，避免视觉噪音                    |
| 安全性  | 自动备份保护机制 + 进程检测 + 时间差值确认提醒            |
| 配置   | 自动应用默认值 + 可编辑存储路径 + 可自定义恢复确认阈值       |
| 编译   | 使用 Nuitka 实现高性能单文件可执行产物               |
| 可维护性 | 每个模块职责单一，可独立测试                        |
