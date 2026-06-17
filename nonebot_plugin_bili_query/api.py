import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from nonebot.log import logger
from bilibili_api import video, user


# ————————————————————————————
# B站 API 调用封装♿️
# ————————————————————————————

async def get_user_info(uid: str) -> Optional[Dict[str, Any]]:
    """
    获取 B站用户信息
    返回：uid, name, face, fans, following, videos, likes, article, dynamic_count, last_video_time
    """
    try:
        u = user.User(int(uid))
        info = await u.get_user_info()
        stats = info.get('stat', {})
        # 最近投稿
        videos = await u.get_videos(ps=1)
        last_video_time = None
        if videos.get('list', {}).get('vlist'):
            last_video = videos['list']['vlist'][0]
            last_video_time = datetime.fromtimestamp(last_video['created'])
        return {
            'uid': uid,
            'name': info.get('name', '未知'),
            'face': info.get('face', ''),
            'fans': stats.get('follower', 0),
            'following': stats.get('following', 0),
            'videos': stats.get('video', 0),
            'likes': stats.get('likes', 0),
            'article': stats.get('article', 0),
            'dynamic_count': stats.get('dynamic', 0),
            'last_video_time': last_video_time,
        }
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return None


async def get_video_info(bv: str) -> Optional[Dict[str, Any]]:
    """
    获取 B站视频信息
    返回：title, bvid, aid, pic, duration, play, like, coin, share, favorite, uploader, desc
    """
    try:
        v = video.Video(bvid=bv)
        info = await v.get_info()
        stat = info.get('stat', {})
        owner = info.get('owner', {})
        return {
            'title': info.get('title', '无标题'),
            'bvid': info.get('bvid', bv),
            'aid': info.get('aid', 0),
            'pic': info.get('pic', ''),
            'duration': info.get('duration', 0),
            'play': stat.get('view', 0),
            'like': stat.get('like', 0),
            'coin': stat.get('coin', 0),
            'share': stat.get('share', 0),
            'favorite': stat.get('favorite', 0),
            'uploader': owner.get('name', '未知'),
            'uploader_mid': owner.get('mid', 0),
            'desc': info.get('desc', '无简介'),
            'pubdate': datetime.fromtimestamp(info.get('pubdate', 0)),
        }
    except Exception as e:
        logger.error(f"获取视频信息失败: {e}")
        return None


async def get_user_videos(uid: str, ps: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    获取用户近期投稿视频列表
    """
    try:
        u = user.User(int(uid))
        videos = await u.get_videos(ps=ps)
        result = []
        for v in videos.get('list', {}).get('vlist', []):
            result.append({
                'title': v.get('title', '无标题'),
                'bvid': v.get('bvid', ''),
                'aid': v.get('aid', 0),
                'created': datetime.fromtimestamp(v.get('created', 0)),
                'play': v.get('play', 0),
                'length': v.get('length', '0:00'),
            })
        return result
    except Exception as e:
        logger.error(f"获取用户视频列表失败: {e}")
        return None


async def resolve_b23_url(url: str) -> Optional[str]:
    """
    解析 b23.tv 短链接，返回 BV 号
    """
    try:
        import httpx
        from .parser import parse_bv
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url)
            final_url = str(resp.url)
            return parse_bv(final_url)
    except Exception as e:
        logger.error(f"解析短链接失败: {e}")
        return None