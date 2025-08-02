#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import re
import os

ARIA2_CONF = "/opt/aria2/aria2.conf"
BACKUP_PATH = ARIA2_CONF + ".bak"
TRACKER_SOURCES = [
    "https://trackerslist.com/all.txt",
    "https://ngosang.github.io/trackerslist/trackers_all.txt"
]

def fetch_trackers():
    trackers = set()
    for url in TRACKER_SOURCES:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                lines = res.text.strip().splitlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        trackers.add(line)
        except Exception as e:
            print(f"[WARN] 无法获取 {url}: {e}")
    return sorted(trackers)

def extract_current_bt_trackers(config_lines):
    for line in config_lines:
        if line.strip().startswith("bt-tracker="):
            return re.split(r"[,\s]+", line.strip()[11:].strip())
    return []

def update_bt_trackers(conf_path):
    if not os.path.exists(conf_path):
        print(f"[ERROR] 未找到配置文件: {conf_path}")
        return

    os.system(f"cp '{conf_path}' '{BACKUP_PATH}'")
    print(f"[INFO] 已备份原始配置至 {BACKUP_PATH}")

    with open(conf_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    old_trackers = extract_current_bt_trackers(lines)
    old_set = set(old_trackers)

    new_trackers = fetch_trackers()
    combined_set = old_set.union(set(new_trackers))
    combined_list = sorted(combined_set)

    tracker_line = "bt-tracker=" + ",".join(combined_list) + "\n"

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("bt-tracker="):
            new_lines.append(tracker_line)
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(tracker_line)

    with open(conf_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"[INFO] 已更新 bt-tracker，共 {len(combined_list)} 个")
    added = set(combined_list) - old_set
    if added:
        print(f"[INFO] 新增 {len(added)} 个 tracker:")
        for t in sorted(added):
            print(f"  + {t}")
    else:
        print("[INFO] 没有新增 tracker")

if __name__ == "__main__":
    update_bt_trackers(ARIA2_CONF)
