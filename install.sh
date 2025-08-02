#!/bin/bash

# Aria2 BT Tracker 更新工具安装脚本

set -e

# 配置变量
INSTALL_DIR="/opt/bt-tracker-updater"
SERVICE_USER="aria2"
SERVICE_GROUP="aria2"

echo "=== Aria2 BT Tracker 更新工具安装脚本 ==="
echo "项目地址: https://github.com/yuanweize/BTtrackers-updater"
echo ""

# 检查是否为 root 用户
if [[ $EUID -ne 0 ]]; then
   echo "错误: 请使用 root 权限运行此脚本"
   echo "请使用: sudo $0"
   exit 1
fi

# 检查系统类型
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "检测到 Linux 系统"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到 macOS 系统"
else
    echo "警告: 未知系统类型，可能需要手动调整"
fi

# 检查 Python3 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.6+"
    exit 1
fi

# 检查 pip3 是否安装
if ! command -v pip3 &> /dev/null; then
    echo "警告: 未找到 pip3，尝试安装..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3-pip
    else
        echo "错误: 无法自动安装 pip3，请手动安装"
        exit 1
    fi
fi

# 安装依赖
echo "安装 Python 依赖..."
pip3 install requests

# 创建安装目录
echo "创建安装目录: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 复制文件
echo "复制程序文件..."

# 检查文件是否存在
if [ ! -f "update_bt_trackers.py" ]; then
    echo "错误: 未找到 update_bt_trackers.py 文件"
    echo "请确保在项目根目录下运行此脚本"
    exit 1
fi

cp update_bt_trackers.py "$INSTALL_DIR/"
cp config.json "$INSTALL_DIR/"
[ -f "README.md" ] && cp README.md "$INSTALL_DIR/"

# 设置权限
chmod +x "$INSTALL_DIR/update_bt_trackers.py"

# 创建用户（如果不存在）
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "创建用户: $SERVICE_USER"
    useradd -r -s /bin/false "$SERVICE_USER"
fi

# 设置目录权限
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

# 设置 cron 定时任务
echo "设置 cron 定时任务..."

# 创建 cron 脚本
CRON_SCRIPT="$INSTALL_DIR/run_update.sh"
cat > "$CRON_SCRIPT" << 'EOF'
#!/bin/bash
# BT Tracker 更新定时任务脚本

# 设置工作目录
cd /opt/bt-tracker-updater

# 运行更新脚本
/usr/bin/python3 update_bt_trackers.py >> bt_tracker_update.log 2>&1

# 记录执行时间
echo "$(date): BT Tracker 更新任务执行完成" >> bt_tracker_update.log
EOF

# 替换安装目录路径
sed -i "s|/opt/bt-tracker-updater|$INSTALL_DIR|g" "$CRON_SCRIPT"

# 设置脚本权限
chmod +x "$CRON_SCRIPT"
chown "$SERVICE_USER:$SERVICE_GROUP" "$CRON_SCRIPT"

# 添加 cron 任务（每天凌晨2点执行）
CRON_JOB="0 2 * * * $CRON_SCRIPT"

# 检查是否已存在相同的 cron 任务
if ! crontab -u "$SERVICE_USER" -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
    # 获取现有的 crontab
    TEMP_CRON=$(mktemp)
    crontab -u "$SERVICE_USER" -l 2>/dev/null > "$TEMP_CRON" || true
    
    # 添加新任务
    echo "$CRON_JOB" >> "$TEMP_CRON"
    
    # 安装新的 crontab
    crontab -u "$SERVICE_USER" "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo "cron 定时任务已安装"
    echo "任务详情: 每天凌晨2点自动更新 BT Tracker"
    echo "执行用户: $SERVICE_USER"
    echo "日志文件: $INSTALL_DIR/bt_tracker_update.log"
else
    echo "cron 任务已存在，跳过安装"
fi

echo ""
echo "管理 cron 任务的命令:"
echo "  查看任务: crontab -u $SERVICE_USER -l"
echo "  编辑任务: crontab -u $SERVICE_USER -e"
echo "  删除任务: crontab -u $SERVICE_USER -r"

# 创建符号链接
ln -sf "$INSTALL_DIR/update_bt_trackers.py" /usr/local/bin/bt-tracker-update

echo ""
echo "=== 安装完成 ==="
echo "安装目录: $INSTALL_DIR"
echo "配置文件: $INSTALL_DIR/config.json"
echo "定时脚本: $INSTALL_DIR/run_update.sh"
echo ""
echo "使用方法:"
echo "  手动运行: bt-tracker-update"
echo "  查看帮助: bt-tracker-update --help"
echo "  预览模式: bt-tracker-update --dry-run"
echo "  手动执行定时脚本: $INSTALL_DIR/run_update.sh"
echo ""
echo "定时任务:"
echo "  已设置每天凌晨2点自动更新"
echo "  查看日志: tail -f $INSTALL_DIR/bt_tracker_update.log"
echo ""
echo "请编辑配置文件 $INSTALL_DIR/config.json 以适应您的环境"
echo "特别是 aria2_conf_path 设置"