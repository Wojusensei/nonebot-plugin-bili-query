from nonebot import require

require("nonebot_plugin_localstore")

import sqlite3
import asyncio
from typing import List, Tuple, Optional
from pathlib import Path

import nonebot_plugin_localstore as store

# ————————————————————————————
# 数据目录初始化
# ————————————————————————————

DATA_DIR = store.get_plugin_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "subscriptions.db"


# ————————————————————————————
# 同步数据库操作sqlite3
# ————————————————————————————

def _init_db():
    """同步创建订阅表"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            uid TEXT NOT NULL,
            last_video_bvid TEXT,
            last_video_time INTEGER,
            UNIQUE(group_id, uid)
        )
    ''')
    conn.commit()
    conn.close()


def _add_subscription(group_id: str, uid: str) -> bool:
    """同步添加订阅"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO subscriptions (group_id, uid) VALUES (?, ?)',
            (group_id, uid)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def _remove_subscription(group_id: str, uid: str) -> bool:
    """同步取消订阅"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        'DELETE FROM subscriptions WHERE group_id = ? AND uid = ?',
        (group_id, uid)
    )
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def _get_subscriptions() -> List[Tuple[str, str]]:
    """同步获取所有订阅"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT group_id, uid FROM subscriptions')
    rows = c.fetchall()
    conn.close()
    return rows


def _update_last_video(uid: str, bvid: str, timestamp: int) -> None:
    """同步更新用户最新视频记录"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        'UPDATE subscriptions SET last_video_bvid = ?, last_video_time = ? WHERE uid = ?',
        (bvid, timestamp, uid)
    )
    conn.commit()
    conn.close()


def _get_subscription_by_uid(uid: str) -> Optional[Tuple[str, str, str, int]]:
    """同步根据 UID 查询订阅信息"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        'SELECT group_id, uid, last_video_bvid, last_video_time FROM subscriptions WHERE uid = ?',
        (uid,)
    )
    row = c.fetchone()
    conn.close()
    return row


# ————————————————————————————
# 异步包装
# ————————————————————————————

async def init_db():
    """初始化数据库"""
    await asyncio.to_thread(_init_db)


async def add_subscription(group_id: str, uid: str) -> bool:
    """异步添加订阅"""
    return await asyncio.to_thread(_add_subscription, group_id, uid)


async def remove_subscription(group_id: str, uid: str) -> bool:
    """异步取消订阅"""
    return await asyncio.to_thread(_remove_subscription, group_id, uid)


async def get_subscriptions() -> List[Tuple[str, str]]:
    """异步获取所有订阅"""
    return await asyncio.to_thread(_get_subscriptions)


async def update_last_video(uid: str, bvid: str, timestamp: int) -> None:
    """异步更新用户最新视频记录"""
    await asyncio.to_thread(_update_last_video, uid, bvid, timestamp)


async def get_subscription_by_uid(uid: str) -> Optional[Tuple[str, str, str, int]]:
    """异步根据 UID 查询订阅信息"""
    return await asyncio.to_thread(_get_subscription_by_uid, uid)