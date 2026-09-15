# 北师大空闲教室查询 Skill

让 AI 查询北京师范大学教学楼的空闲教室和课表占用。一个 Python 脚本，仅使用标准库；无需安装 Python 软件包，也无需常驻服务。

**非官方项目，与北京师范大学无隶属关系。** 数据来自学校微信端现有接口；无课不代表教室无人、已开门或允许自习。

## 功能概览

- 按教学楼查询今天、明天、后天的课表占用。
- 筛选多个上课时段全部空闲的教室，例如下午两个时段均空闲。
- 查询指定教室的七天课表，并按空闲时段筛选日期。
- 提供文本与 JSON 输出；两种格式应用相同的筛选。

不支持任意日期的整楼查询、实时在场人数、预约教室、容量或设备查询。当前固定查询参数为 `ca=1`，未实现校区切换；支持范围以 `--list-buildings` 为准。

## 下载与安装

要求：Python 3.9 或更新版本，以及能够连接 `weixin.bnu.edu.cn` 的网络。Windows 可将以下命令中的 `python3` 改为 `py -3`。

### 方式一：让 AI Agent 安装

将下面这段提示词复制给能够访问网络和本地文件、执行命令的 AI Agent：

```text
请帮我安装北师大空闲教室查询 skill：
https://github.com/KawaroX/bnu-classroom-skill

请先阅读仓库的 README.md 和 SKILL.md，识别你当前运行环境的 skills 安装目录，将仓库中的 skill 安装为 bnu-classroom。可以下载最新 Release 压缩包或克隆仓库；安装后确保 bnu-classroom/SKILL.md 与 bnu-classroom/scripts/bnu_classroom.py 都存在，不要额外嵌套一层目录。如果已有安装，请先备份再更新。

检查 Python 版本是否为 3.9 或更新版本。使用安装后的脚本运行 --list-buildings --json，确认脚本可用，再查询教二楼今天的课表，验证网络连接。如果接口查询失败，请区分安装问题和网络或接口问题。

完成后告诉我安装路径、验证结果，以及是否需要重新打开助手或新建会话才能使用。如果无法确定安装目录或缺少执行权限，请说明具体缺少什么。
```

### 方式二：手动下载安装

#### 下载文件

- [下载最新发布的 skill 压缩包](https://github.com/KawaroX/bnu-classroom-skill/releases/latest/download/bnu-classroom-skill.zip)，解压得到 `bnu-classroom/`。
- 或克隆源码：

```sh
git clone https://github.com/KawaroX/bnu-classroom-skill.git bnu-classroom
```

#### 放入 skills 目录

把完整的 `bnu-classroom` 文件夹放进所用助手的 skills 目录，确保结构为：

```text
<skills目录>/bnu-classroom/SKILL.md
<skills目录>/bnu-classroom/scripts/bnu_classroom.py
```

Codex 本地个人 skills 目录通常为 `~/.codex/skills`；如果设置了 `CODEX_HOME`，使用该目录下的 `skills`。例如在下载解压后的父目录执行以下命令（目标文件夹应尚不存在，已有安装请先备份）：

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R bnu-classroom "${CODEX_HOME:-$HOME/.codex}/skills/bnu-classroom"
```

重新打开助手或新建会话后，确认 `bnu-classroom` 已被发现。其他支持 SKILL.md 且能执行 Python 的助手，按各自的 skills 安装方式放置；本项目不依赖 Hermes 或特定绝对路径。

### 使用示例

安装后可以问：

- “用 bnu-classroom 查一下教二楼明天下午都有空的教室。”
- “教四楼 101 这几天晚上什么时候没课？”
- “查询所有支持的教学楼，找今晚两大节都空的教室。”

AI 运行环境仍需具备执行脚本和网络访问权限。

## 直接运行脚本

在 `bnu-classroom` 目录下执行：

```sh
python3 scripts/bnu_classroom.py --help
python3 scripts/bnu_classroom.py --list-buildings
python3 scripts/bnu_classroom.py --building 教二楼 --day today
python3 scripts/bnu_classroom.py --building 教二楼 --day tomorrow --free-slots 5 6 --json
python3 scripts/bnu_classroom.py --building 教四楼 --room 101 --json
```

| 参数 | 含义 |
| --- | --- |
| `--building` | 楼宇，默认教二楼；名称必须在支持列表中 |
| `--day` | `today` 今天、`tomorrow` 明天、`2daysl` 后天；默认今天 |
| `--room` | 指定教室七天课表，与 `--day` 互斥 |
| `--free-slots` | 1–6 中的一个或多个时段编号，要求全部空闲 |
| `--json` | 输出已验证、已筛选的 JSON；可与楼宇列表使用 |
| `--use-proxy` | 使用系统/环境代理；默认直连 |

### 查询时段对照表

课表按小节编号，学校接口每两小节合并为一个查询时段。`--free-slots` 使用表中的查询时段编号（1–6），而非课表节次。例如，查询第 5–8 节全部空闲，应使用 `--free-slots 3 4`。所有时间均为北京时间（Asia/Shanghai）。

| 课表节次 | 上课时间 | 查询时段编号（`--free-slots`） |
| --- | --- | --- |
| 第 1–2 节 | 08:00–09:40 | 1 |
| 第 3–4 节 | 10:00–11:40 | 2 |
| 第 5–6 节 | 13:30–15:10 | 3 |
| 第 7–8 节 | 15:30–17:10 | 4 |
| 第 9–10 节 | 18:00–19:40 | 5 |
| 第 11–12 节 | 19:50–21:30 | 6 |

这些时间段不覆盖课间、午休和深夜；不能据此保证跨间隔的连续自习时间。

### JSON 约定

- `success`：1 为成功，0 为查询失败。
- `building`、`room`、`day`、`query_date`：查询范围；不适用的字段为 `null`。
- `timezone`、`fetched_at`、`source_url`：时区、抓取时间和来源。抓取时间不是学校数据更新时间。
- `slots`：六个上课时段；`free_slots`：本次筛选条件。
- `total_count`：原始记录数；`count`：筛选后记录数。
- `result`：楼宇记录，包含 `room_number`、`status`。
- `detail`：单间记录，包含 `date`、`status`。
- `status`：六个整数，0 为空闲，非 0 为占用。

原始列表为空时，不能推断楼宇全部空闲或教室不存在。格式缺失或损坏会报错，不会冒充零条查询结果。JSON 格式由本脚本组织，不是接口原始响应。

退出码：0 成功，1 网络或数据错误，2 参数错误。查询失败时，JSON 模式的 stdout 输出 `success: 0` 和 `error`，stderr 同时输出错误；参数错误由 argparse 写入 stderr。

## 数据来源与连接问题

脚本只读取以下接口，固定参数 `ca=1`：

- `https://weixin.bnu.edu.cn/classroom/rooms.php`：`b_name`、`time`。
- `https://weixin.bnu.edu.cn/classroom/room-detail.php`：`b_name`、`room`。

2026-09-15 在开发环境实测两个接口均可不携带 Cookie 或微信 User-Agent 读取。其他网络条件及未来接口行为未作保证。项目不附带账号或凭据。

如果直连失败且环境依赖代理，使用 `--use-proxy`。每次请求超时为 20 秒，脚本不会自动重试。服务端调整认证、数据格式或访问规则后可能需要更新脚本。

## 开发验证

离线测试不请求学校接口，也不需要额外依赖：

```sh
python3 -m unittest discover -s tests -v
```

## 许可证

代码和文档采用 [MIT License](LICENSE)。许可证覆盖本项目文件，不授予学校接口或数据的额外使用权。
