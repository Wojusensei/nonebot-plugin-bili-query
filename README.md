# nonebot-plugin-bili-query

✨ B站查询与提醒插件 for NoneBot2 ✨

## 功能

- `/用户查询` - 查询B站用户信息（粉丝数、投稿数、最近视频等数据）
- `/视频查询` - 查询B站视频信息（播放量、点赞、投币、收藏等数据）
- `/订阅` - 订阅UP主，新视频发布时自动在群里提醒
- `/取消订阅` - 取消订阅
- `/help` - 显示所有指令

## 安装，指令二选一

```bash
nb plugin install nonebot-plugin-bili-query
pip install nonebot-plugin-bili-query
```


## 使用
在群聊中 @机器人 并输入以下命令：

指令	     参数	               说明
/help	     无	                  显示所有指令
/用户查询	  UID或空间链接	         查询用户信息
/视频查询	  BV号或视频链接	     查询视频信息
/订阅	     UID或空间链接	        订阅用户更新
/取消订阅	  UID或空间链接	         取消订阅

## 示例
/用户查询 下面那个神秘数字

/用户查询 https://space.bilibili.com/此处填写几个神秘数字

/视频查询 此处填写BV号

/订阅 那个神秘数字

/取消订阅 那个神秘数字

/help 滚木

对的/help后面啥都没有

## 配置
无需用户配置

## 数据存储
订阅数据：使用 nonebot-plugin-localstore 管理，文件位于插件数据目录下
定时任务：使用 nonebot-plugin-apscheduler，每 5 分钟检查一次订阅用户更新

## 注意事项
1️⃣ 需要机器人有发送群消息的权限
2️⃣ 订阅功能依赖定时任务，需确保机器人持续运行
3️⃣ 首次使用前无需额外配置

## 开源协议
mit
