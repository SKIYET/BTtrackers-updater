#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import re
import os
import json
import logging
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path

class Config:
    """配置管理类"""
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "aria2_conf_path": "/opt/aria2/aria2.conf",
            "backup_enabled": True,
            "backup_suffix": ".bak",
            "tracker_sources": [
                "https://trackerslist.com/all.txt",
                "https://ngosang.github.io/trackerslist/trackers_all.txt"
            ],
            "request_timeout": 10,
            "max_retries": 3,
            "log_level": "INFO",
            "log_file": "bt_tracker_update.log"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logging.info(f"已加载配置文件: {self.config_file}")
            except Exception as e:
                logging.error(f"配置文件加载失败，使用默认配置: {e}")
        else:
            logging.info("未找到配置文件，使用默认配置")
            # 创建默认配置文件
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                logging.info(f"已创建默认配置文件: {self.config_file}")
            except Exception as e:
                logging.warning(f"无法创建配置文件: {e}")
        
        return default_config
    
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)


def setup_logging(config):
    """设置日志系统"""
    log_level = getattr(logging, config.get('log_level', 'INFO').upper())
    log_file = config.get('log_file')
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logging.warning(f"无法创建日志文件 {log_file}: {e}")


def fetch_trackers(config):
    """从多个源获取 tracker 列表"""
    trackers = set()
    sources = config.get('tracker_sources', [])
    timeout = config.get('request_timeout', 10)
    max_retries = config.get('max_retries', 3)
    
    logging.info(f"开始从 {len(sources)} 个源获取 tracker")
    
    for url in sources:
        success = False
        for attempt in range(max_retries):
            try:
                logging.info(f"正在获取 {url} (尝试 {attempt + 1}/{max_retries})")
                res = requests.get(url, timeout=timeout)
                
                if res.status_code == 200:
                    lines = res.text.strip().splitlines()
                    source_trackers = set()
                    
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # 验证 tracker 格式
                            if is_valid_tracker(line):
                                source_trackers.add(line)
                    
                    trackers.update(source_trackers)
                    logging.info(f"从 {url} 获取到 {len(source_trackers)} 个有效 tracker")
                    success = True
                    break
                else:
                    logging.warning(f"HTTP {res.status_code}: {url}")
                    
            except requests.exceptions.Timeout:
                logging.warning(f"请求超时: {url} (尝试 {attempt + 1}/{max_retries})")
            except requests.exceptions.RequestException as e:
                logging.warning(f"网络请求失败: {url} - {e} (尝试 {attempt + 1}/{max_retries})")
            except Exception as e:
                logging.error(f"未知错误: {url} - {e} (尝试 {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                time.sleep(2)  # 重试前等待
        
        if not success:
            logging.error(f"所有尝试失败，跳过源: {url}")
    
    logging.info(f"总共获取到 {len(trackers)} 个唯一 tracker")
    return sorted(trackers)


def is_valid_tracker(tracker):
    """验证 tracker 格式是否有效"""
    if not tracker:
        return False
    
    # 基本的 URL 格式检查
    valid_protocols = ['http://', 'https://', 'udp://']
    if not any(tracker.startswith(protocol) for protocol in valid_protocols):
        return False
    
    # 检查是否包含端口号
    if '://' in tracker:
        try:
            # 简单的格式验证
            parts = tracker.split('://', 1)
            if len(parts) == 2 and parts[1]:
                return True
        except:
            pass
    
    return False

def extract_current_bt_trackers(config_lines):
    """从配置文件中提取现有的 bt-tracker 列表"""
    for line in config_lines:
        line_stripped = line.strip()
        if line_stripped.startswith("bt-tracker="):
            tracker_str = line_stripped[11:].strip()
            if tracker_str:
                # 支持逗号和换行分隔
                trackers = re.split(r'[,\n]+', tracker_str)
                return [t.strip() for t in trackers if t.strip()]
    return []

def backup_config_file(conf_path, config):
    """备份配置文件"""
    if not config.get('backup_enabled', True):
        logging.info("备份功能已禁用")
        return True
    
    backup_suffix = config.get('backup_suffix', '.bak')
    backup_path = conf_path + backup_suffix
    
    try:
        # 使用 Python 的 shutil 而不是系统命令，更安全
        import shutil
        shutil.copy2(conf_path, backup_path)
        logging.info(f"已备份原始配置至: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"备份失败: {e}")
        return False


def validate_config_file(conf_path):
    """验证配置文件"""
    if not os.path.exists(conf_path):
        logging.error(f"配置文件不存在: {conf_path}")
        return False
    
    if not os.access(conf_path, os.R_OK):
        logging.error(f"配置文件无读取权限: {conf_path}")
        return False
    
    if not os.access(conf_path, os.W_OK):
        logging.error(f"配置文件无写入权限: {conf_path}")
        return False
    
    return True


def update_bt_trackers(config):
    """更新 bt-tracker 配置"""
    conf_path = config.get('aria2_conf_path')
    
    logging.info(f"开始更新 bt-tracker 配置: {conf_path}")
    
    # 验证配置文件
    if not validate_config_file(conf_path):
        return False
    
    # 备份配置文件
    if not backup_config_file(conf_path, config):
        logging.warning("备份失败，但继续执行更新")
    
    try:
        # 读取现有配置
        with open(conf_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        logging.info("已读取现有配置文件")
        
        # 提取现有 tracker
        old_trackers = extract_current_bt_trackers(lines)
        old_set = set(old_trackers)
        logging.info(f"现有 tracker 数量: {len(old_set)}")
        
        # 获取新的 tracker
        new_trackers = fetch_trackers(config)
        if not new_trackers:
            logging.warning("未获取到任何新的 tracker")
            return False
        
        # 合并和去重
        combined_set = old_set.union(set(new_trackers))
        combined_list = sorted(combined_set)
        
        # 生成新的 tracker 行
        tracker_line = "bt-tracker=" + ",".join(combined_list) + "\n"
        
        # 更新配置文件
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().startswith("bt-tracker="):
                new_lines.append(tracker_line)
                updated = True
            else:
                new_lines.append(line)
        
        # 如果没有找到 bt-tracker 行，则添加
        if not updated:
            new_lines.append(tracker_line)
            logging.info("未找到现有 bt-tracker 配置，已添加新配置")
        
        # 写入文件
        with open(conf_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        # 统计和日志
        added = combined_set - old_set
        removed = old_set - combined_set  # 理论上不会有，但记录一下
        
        logging.info(f"bt-tracker 更新完成，总数: {len(combined_list)}")
        
        if added:
            logging.info(f"新增 {len(added)} 个 tracker:")
            for tracker in sorted(added):
                logging.info(f"  + {tracker}")
        else:
            logging.info("没有新增 tracker")
        
        if removed:
            logging.warning(f"移除了 {len(removed)} 个 tracker:")
            for tracker in sorted(removed):
                logging.warning(f"  - {tracker}")
        
        return True
        
    except Exception as e:
        logging.error(f"更新配置文件时发生错误: {e}")
        return False

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Aria2 BT Tracker 自动更新工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                          # 使用默认配置运行
  %(prog)s -c custom.json           # 使用自定义配置文件
  %(prog)s --dry-run                # 预览模式，不实际修改文件
  %(prog)s --aria2-conf /path/to/aria2.conf  # 指定 aria2 配置文件路径
  %(prog)s -v                       # 详细输出模式
  %(prog)s --list-sources           # 列出所有 tracker 源
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='配置文件路径 (默认: config.json)'
    )
    
    parser.add_argument(
        '--aria2-conf',
        help='Aria2 配置文件路径 (覆盖配置文件中的设置)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，显示将要进行的更改但不实际修改文件'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出模式'
    )
    
    parser.add_argument(
        '--list-sources',
        action='store_true',
        help='列出所有配置的 tracker 源并退出'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='禁用备份功能'
    )
    
    parser.add_argument(
        '--log-file',
        help='日志文件路径 (覆盖配置文件中的设置)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.2.0'
    )
    
    return parser.parse_args()


def list_tracker_sources(config):
    """列出所有 tracker 源"""
    sources = config.get('tracker_sources', [])
    print(f"配置的 Tracker 源 ({len(sources)} 个):")
    print("-" * 50)
    for i, source in enumerate(sources, 1):
        print(f"{i:2d}. {source}")
    print("-" * 50)


def dry_run_update(config):
    """预览模式 - 显示将要进行的更改但不实际修改"""
    conf_path = config.get('aria2_conf_path')
    
    logging.info("=== 预览模式 - 不会实际修改文件 ===")
    
    if not os.path.exists(conf_path):
        logging.error(f"配置文件不存在: {conf_path}")
        return False
    
    try:
        # 读取现有配置
        with open(conf_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 提取现有 tracker
        old_trackers = extract_current_bt_trackers(lines)
        old_set = set(old_trackers)
        
        logging.info(f"当前配置文件: {conf_path}")
        logging.info(f"现有 tracker 数量: {len(old_set)}")
        
        # 获取新的 tracker
        new_trackers = fetch_trackers(config)
        if not new_trackers:
            logging.warning("未获取到任何新的 tracker")
            return False
        
        # 计算变更
        combined_set = old_set.union(set(new_trackers))
        added = combined_set - old_set
        
        logging.info(f"将要添加的 tracker 数量: {len(added)}")
        logging.info(f"更新后总 tracker 数量: {len(combined_set)}")
        
        if added:
            logging.info("将要添加的 tracker:")
            for tracker in sorted(added):
                logging.info(f"  + {tracker}")
        else:
            logging.info("没有新的 tracker 需要添加")
        
        return True
        
    except Exception as e:
        logging.error(f"预览时发生错误: {e}")
        return False


def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 加载配置
        config = Config(args.config)
        
        # 应用命令行参数覆盖
        if args.aria2_conf:
            config.config['aria2_conf_path'] = args.aria2_conf
        
        if args.no_backup:
            config.config['backup_enabled'] = False
        
        if args.verbose:
            config.config['log_level'] = 'DEBUG'
        
        if args.log_file:
            config.config['log_file'] = args.log_file
        
        # 设置日志
        setup_logging(config)
        
        # 处理特殊命令
        if args.list_sources:
            list_tracker_sources(config)
            return
        
        logging.info("=" * 50)
        logging.info("Aria2 BT Tracker 更新工具启动")
        logging.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"配置文件: {args.config}")
        logging.info(f"Aria2 配置: {config.get('aria2_conf_path')}")
        if args.dry_run:
            logging.info("运行模式: 预览模式")
        logging.info("=" * 50)
        
        # 执行更新
        if args.dry_run:
            success = dry_run_update(config)
        else:
            success = update_bt_trackers(config)
        
        if success:
            if args.dry_run:
                logging.info("预览完成")
            else:
                logging.info("bt-tracker 更新成功完成")
        else:
            logging.error("操作失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logging.error(f"程序执行出现未预期错误: {e}")
        sys.exit(1)
    finally:
        logging.info("程序执行结束")


if __name__ == "__main__":
    main()
