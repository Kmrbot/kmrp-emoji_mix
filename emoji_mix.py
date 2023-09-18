import aiohttp
from typing import Union
from emoji import is_emoji
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot import on_regex
from plugins.common_plugins_function import while_list_handle

emoji_mix = on_regex(
    pattern=r"^.+\+.+",
    priority=5
)

emoji_mix.__doc__ = """emoji_mix"""
emoji_mix.__help_type__ = None

emoji_mix.handle()(while_list_handle("emoji_mix"))

# emoji前面的时间
dates = [
    "20201001",
    "20210218",
    "20210521",
    "20210831",
    "20211115",
    "20220110",
    "20220203",
    "20220406",
    "20220506",
    "20230126",
]


def split_emoji(event):
    if len(event.message) != 1 or event.message[0].type != "text":
        return False, "", ""
    emoji_data = event.message[0].data.get("text", "").split("+")
    if len(emoji_data) != 2:
        return False, "", ""
    if not is_emoji(emoji_data[0]) or len(emoji_data[0]) != 1 or \
            not is_emoji(emoji_data[1]) or len(emoji_data[1]) != 1:
        return False, "", ""
    return True, emoji_data[0], emoji_data[1]


@emoji_mix.handle()
async def _(
        event: Union[GroupMessageEvent, PrivateMessageEvent]
):
    result = split_emoji(event)
    if not result[0]:
        await emoji_mix.finish()
    emoji_left = "u" + hex(ord(result[1]))[2:]
    emoji_right = "u" + hex(ord(result[2]))[2:]

    header = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    async with aiohttp.ClientSession() as session:
        # 遍历所有时间
        for date in dates:
            resp = await session.get(
                f"https://www.gstatic.com/android/keyboard/emojikitchen/{date}/"
                f"{emoji_left}/{emoji_left}_{emoji_right}.png",
                headers=header)
            if resp.status != 200:
                resp = await session.get(
                    f"https://www.gstatic.com/android/keyboard/emojikitchen/{date}/"
                    f"{emoji_right}/{emoji_right}_{emoji_left}.png",
                    headers=header)
            if resp.status == 200:
                image_data = await resp.read()
                msg = Message(f"[CQ:reply,id={event.message_id}]") + Message(MessageSegment.image(image_data))
                await emoji_mix.finish(msg)
        msg = Message(f"[CQ:reply,id={event.message_id}]") + Message("不存在以上两种emoji的mix表情")
        await emoji_mix.finish(msg)
