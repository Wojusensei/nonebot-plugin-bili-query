from nonebot import require

# ====== require 放在所有 import 之前 ======
require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")

import re
from datetime import datetime
from nonebot import on_command, get_plugin_config, get_driver
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

from .config import Config
from .parser import parse_uid, parse_bv, parse_video_url
from .api import get_user_info, get_video_info, resolve_b23_url
from .database import init_db, add_subscription, remove_subscription
from .scheduler import init_scheduler, register_notify_callback

import nonebot_plugin_localstore as store

# ————————————————————————————
# 插件元数据
# ————————————————————————————

__plugin_meta__ = PluginMetadata(
    name="B站查询与提醒",
    description="B站用户与视频查询插件，支持订阅用户更新提醒",
    usage=(
        "/help - 显示所有指令\n"
        "/用户查询 [UID/链接] - 查询B站用户信息\n"
        "/视频查询 [BV号/链接] - 查询B站视频信息\n"
        "/订阅 [UID/链接] - 订阅用户更新提醒\n"
        "/取消订阅 [UID/链接] - 取消订阅"
    ),
    type="application",
    homepage="https://github.com/Wojusensei/nonebot-plugin-bili-query",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

# ————————————————————————————
# 读取配置
# ————————————————————————————

config = get_plugin_config(Config)

# ————————————————————————————
# 命令注册
# ————————————————————————————

help_cmd = on_command("/help", aliases={"help", "帮助"}, priority=10, block=True)
user_cmd = on_command("/用户查询", aliases={"用户查询"}, priority=10, block=True)
video_cmd = on_command("/视频查询", aliases={"视频查询"}, priority=10, block=True)
subscribe_cmd = on_command("/订阅", aliases={"订阅"}, priority=10, block=True)
unsubscribe_cmd = on_command("/取消订阅", aliases={"取消订阅"}, priority=10, block=True)

# ————————————————————————————
# 通知回调（由 scheduler 调用）
# ————————————————————————————

async def send_notification(group_id: str, uid: str, video_info: dict):
    """向群组发送视频更新通知"""
    title = video_info.get('title', '无标题')
    bvid = video_info.get('bvid', '')
    created = video_info.get('created')
    time_str = created.strftime("%Y-%m-%d %H:%M") if created else "未知"
    msg = (
        f"📢 您订阅的UP主 {uid} 发布了新视频！\n"
        f"标题：{title}\n"
        f"BV号：{bvid}\n"
        f"发布时间：{time_str}\n"
        f"链接：https://www.bilibili.com/video/{bvid}"
    )
    # 这里需要 bot 实例，通过 get_bot 获取
    from nonebot import get_bot
    try:
        bot = get_bot()
        await bot.send_group_msg(group_id=int(group_id), message=msg)
    except Exception as e:
        logger.error(f"发送通知失败: {e}")

# 注册通知回调
register_notify_callback(send_notification)

# ————————————————————————————
# /help
# ————————————————————————————

@help_cmd.handle()
async def handle_help():
    help_text = (
        "📖 B站查询与提醒 插件指令：\n"
        "1. /用户查询 [UID/链接] - 查询B站用户信息（粉丝、投稿数等）\n"
        "2. /视频查询 [BV号/链接] - 查询B站视频信息（播放量、点赞等）\n"
        "3. /订阅 [UID/链接] - 订阅用户，有新视频时自动提醒\n"
        "4. /取消订阅 [UID/链接] - 取消订阅\n"
        "5. /help - 显示本帮助"
    )
    await help_cmd.finish(help_text)

# ————————————————————————————
# /用户查询 命令
# ————————————————————————————

@user_cmd.handle()
async def handle_user_query(args: str = CommandArg()):
    raw = args.extract_plain_text().strip()
    if not raw:
        await user_cmd.finish("请提供要查询的 UID 或空间链接，例如：/用户查询 123456")
    
    uid = parse_uid(raw)
    if not uid:
        await user_cmd.finish("未能识别 UID，请提供 B站 UID 或空间链接")
    
    info = await get_user_info(uid)
    if not info:
        await user_cmd.finish("查询失败，请检查 UID 是否正确或稍后再试")
    
    last_video = info.get('last_video_time')
    last_video_str = last_video.strftime("%Y-%m-%d %H:%M") if last_video else "暂无"
    
    reply = (
        f"📊 用户信息：{info['name']}\n"
        f"UID：{info['uid']}\n"
        f"粉丝：{info['fans']}\n"
        f"关注：{info['following']}\n"
        f"投稿数：{info['videos']}\n"
        f"获赞数：{info['likes']}\n"
        f"专栏数：{info['article']}\n"
        f"动态数：{info['dynamic_count']}\n"
        f"最近视频：{last_video_str}"
    )
    await user_cmd.finish(reply)

# ————————————————————————————
# /视频查询 命令
# ————————————————————————————

@video_cmd.handle()
async def handle_video_query(args: str = CommandArg()):
    raw = args.extract_plain_text().strip()
    if not raw:
        await video_cmd.finish("请提供要查询的 BV 号或视频链接，例如：/视频查询 BV1xx411c7mD")
    
    # 解析 BV
    bv = parse_bv(raw)
    # 解析完整 URL
    if not bv:
        url = parse_video_url(raw)
        if url:
            bv = parse_bv(url)
    # 短链接解析
    if not bv and 'b23.tv' in raw:
        bv = await resolve_b23_url(raw)
    
    if not bv:
        await video_cmd.finish("未能识别 BV 号，请提供正确的 BV 号或视频链接")
    
    info = await get_video_info(bv)
    if not info:
        await video_cmd.finish("查询失败，请检查 BV 号是否正确或稍后再试")
    
    duration = info.get('duration', 0)
    minutes = duration // 60
    seconds = duration % 60
    duration_str = f"{minutes}分{seconds}秒"
    
    reply = (
        f"🎬 视频信息：{info['title']}\n"
        f"BV号：{info['bvid']}\n"
        f"UP主：{info['uploader']}\n"
        f"时长：{duration_str}\n"
        f"播放量：{info['play']}\n"
        f"点赞：{info['like']}\n"
        f"投币：{info['coin']}\n"
        f"收藏：{info['favorite']}\n"
        f"转发：{info['share']}\n"
        f"发布时间：{info['pubdate'].strftime('%Y-%m-%d %H:%M')}\n"
        f"简介：{info['desc'][:100]}..."
    )
    await video_cmd.finish(reply)

# ————————————————————————————
# /订阅 命令 修正了 event 参数。。
# ————————————————————————————

@subscribe_cmd.handle()
async def handle_subscribe(event: GroupMessageEvent, args: str = CommandArg()):
    raw = args.extract_plain_text().strip()
    if not raw:
        await subscribe_cmd.finish("请提供要订阅的 UID 或空间链接，例如：/订阅 123456")
    
    uid = parse_uid(raw)
    if not uid:
        await subscribe_cmd.finish("未能识别 UID，请提供 B站 UID 或空间链接")
    
    group_id = str(event.group_id)
    success = await add_subscription(group_id, uid)
    if success:
        await subscribe_cmd.finish(f"✅ 订阅成功！已订阅 UID：{uid}")
    else:
        await subscribe_cmd.finish(f"⚠️ 该 UID 已被本群订阅")

# ————————————————————————————
# /取消订阅 命令 修正 event 版
# ————————————————————————————

@unsubscribe_cmd.handle()
async def handle_unsubscribe(event: GroupMessageEvent, args: str = CommandArg()):
    raw = args.extract_plain_text().strip()
    if not raw:
        await unsubscribe_cmd.finish("请提供要取消订阅的 UID 或空间链接，例如：/取消订阅 123456")
    
    uid = parse_uid(raw)
    if not uid:
        await unsubscribe_cmd.finish("未能识别 UID，请提供 B站 UID 或空间链接")
    
    group_id = str(event.group_id)
    success = await remove_subscription(group_id, uid)
    if success:
        await unsubscribe_cmd.finish(f"✅ 取消订阅成功！已取消 UID：{uid}")
    else:
        await unsubscribe_cmd.finish(f"⚠️ 未找到该 UID 的订阅记录")

# ————————————————————————————
# 启动时初始化数据库和定时器
# ————————————————————————————

driver = get_driver()

@driver.on_startup
async def startup():
    await init_db()
    init_scheduler()
    logger.info("B站查询与提醒插件已启动")