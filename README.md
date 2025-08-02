# Aria2 BT Tracker 自动更新工具

一个用于自动更新 Aria2 BT Tracker 列表的 Python 脚本，帮助保持 Aria2 的 BT Tracker 始终最新，提升下载的连通性和速度。

## 功能特性

- 🔄 从多个公开的 Tracker 列表源获取最新的 BT Tracker 地址
- 🔗 自动合并现有配置和新获取的 Tracker，智能去重
- 💾 修改配置前自动备份原文件，保障安全
- 📝 完善的日志记录和异常处理
- ⚙️ 支持配置文件自定义设置
- 🔁 支持重试机制，提高获取成功率
- ✅ Tracker 格式验证，确保有效性

## 安装和配置

### 1. 环境要求

- Python 3.6+
- requests 库

```bash
pip3 install requests
```

### 2. 下载和配置

```bash
# 创建工作目录
sudo mkdir -p /opt/bt-tracker-updater
cd /opt/bt-tracker-updater

# 下载脚本文件
# 将 update_bt_trackers.py 和 config.json 放到此目录

# 设置权限
sudo chown -R aria2:aria2 /opt/bt-tracker-updater
sudo chmod +x update_bt_trackers.py
```

### 3. 配置文件说明

编辑 `config.json` 文件来自定义设置：

```json
{
  "aria2_conf_path": "/opt/aria2/aria2.conf",     // Aria2 配置文件路径
  "backup_enabled": true,                          // 是否启用备份
  "backup_suffix": ".bak",                         // 备份文件后缀
  "tracker_sources": [                             // Tracker 源列表
    "https://trackerslist.com/all.txt",
    "https://ngosang.github.io/trackerslist/trackers_all.txt",
    "https://raw.githubusercontent.com/XIU2/TrackersListCollection/master/all.txt"
  ],
  "request_timeout": 10,                           // 请求超时时间（秒）
  "max_retries": 3,                               // 最大重试次数
  "log_level": "INFO",                            // 日志级别
  "log_file": "bt_tracker_update.log"             // 日志文件路径
}
```

## 使用方法

### 快速安装

```bash
# 下载所有文件到当前目录后运行
sudo ./install.sh
```

### 手动运行

```bash
# 基本用法
bt-tracker-update

# 或者直接运行脚本
cd /opt/bt-tracker-updater
python3 update_bt_trackers.py
```

### 命令行选项

```bash
# 查看帮助
bt-tracker-update --help

# 使用自定义配置文件
bt-tracker-update -c /path/to/custom.json

# 预览模式（不实际修改文件）
bt-tracker-update --dry-run

# 指定 aria2 配置文件路径
bt-tracker-update --aria2-conf /path/to/aria2.conf

# 详细输出模式
bt-tracker-update -v

# 列出所有 tracker 源
bt-tracker-update --list-sources

# 禁用备份功能
bt-tracker-update --no-backup

# 指定日志文件
bt-tracker-update --log-file /path/to/logfile.log
```

### 设置定时任务

#### 自动设置 (推荐)

安装脚本会自动设置 cron 定时任务，每天凌晨2点执行更新。

```bash
# 查看已设置的定时任务
sudo crontab -u aria2 -l

# 查看定时任务日志
tail -f /opt/bt-tracker-updater/bt_tracker_update.log
```

#### 手动设置 cron

如果需要自定义定时任务：

```bash
# 编辑 aria2 用户的 crontab
sudo crontab -u aria2 -e

# 添加以下行（每天凌晨2点执行）
0 2 * * * /opt/bt-tracker-updater/run_update.sh

# 或者每6小时执行一次
0 */6 * * * /opt/bt-tracker-updater/run_update.sh
```

#### 常用 cron 时间设置

```bash
# 每天凌晨2点
0 2 * * *

# 每6小时
0 */6 * * *

# 每天上午8点和晚上8点
0 8,20 * * *

# 每周日凌晨3点
0 3 * * 0
```

## 日志查看

```bash
# 查看日志文件
tail -f /opt/bt-tracker-updater/bt_tracker_update.log

# 查看最近的日志
tail -n 50 /opt/bt-tracker-updater/bt_tracker_update.log

# 实时监控日志
watch -n 5 tail -n 20 /opt/bt-tracker-updater/bt_tracker_update.log
```

## 故障排除

### 常见问题

1. **权限问题**
   ```bash
   sudo chown -R aria2:aria2 /opt/bt-tracker-updater
   sudo chmod 644 /opt/aria2/aria2.conf
   ```

2. **网络问题**
   - 检查服务器网络连接
   - 确认防火墙设置
   - 可以在配置文件中增加 `max_retries` 值

3. **配置文件格式错误**
   - 使用 JSON 验证工具检查 config.json 格式
   - 确保路径使用正确的斜杠

### 测试运行

```bash
# 测试配置文件
python3 -c "import json; print(json.load(open('config.json')))"

# 干运行（不实际修改文件）
python3 update_bt_trackers.py --dry-run  # 待实现
```

## 更新日志

- v1.0: 基础功能实现
- v1.1: 添加配置文件支持和增强日志系统
- v1.2: 添加重试机制和 Tracker 验证

## 许可证

MIT License