from nonebot import require

require("nonebot_plugin_apscheduler")
from nonebot.log import logger
from .database import get_subscriptions, update_last_video, get_subscription_by_uid
from .api import get_user_videos
from datetime import datetime

from nonebot_plugin_apscheduler import scheduler


# ————————————————————————————
# 存储待发送的通知（由init注册回调）
# ————————————————————————————

_notify_callbacks = []


def register_notify_callback(callback):
    """注册通知回调函数，由init调用"""
    if callback not in _notify_callbacks:
        _notify_callbacks.append(callback)


async def check_subscriptions():
    """定时任务：检查所有订阅用户是否有新视频"""
    subscriptions = await get_subscriptions()
    if not subscriptions:
        return
    
    for group_id, uid in subscriptions:
        try:
            videos = await get_user_videos(uid, ps=1)
            if not videos:
                continue
            
            latest = videos[0]
            bvid = latest.get('bvid')
            created = latest.get('created')
            
            if not bvid or not created:
                continue
            
            timestamp = int(created.timestamp())
            
            # 查询该订阅的最新记录
            sub_info = await get_subscription_by_uid(uid)
            last_bvid = sub_info[2] if sub_info else None
            
            if last_bvid is None or last_bvid != bvid:
                await update_last_video(uid, bvid, timestamp)
                
                # 发送通知
                for callback in _notify_callbacks:
                    try:
                        await callback(group_id, uid, latest)
                    except Exception as e:
                        logger.error(f"发送通知失败: {e}")
                        
        except Exception as e:
            logger.error(f"检查订阅 {uid} 失败: {e}")


def init_scheduler():
    """初始化定时任务"""
    # 5分钟检查一次
    scheduler.add_job(
        check_subscriptions,
        'interval',
        minutes=5,
        id='bili_query_check',
        replace_existing=True,
    )
    logger.info("B站订阅检查定时任务已启动🌟")