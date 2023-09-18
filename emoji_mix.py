import aiohttp
from typing import Union, Tuple
from emoji import is_emoji
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot import on_regex
from plugins.common_plugins_function import while_list_handle
from .emoji_keys_data import emoji_keys_data

emoji_mix = on_regex(
    pattern=r"^.+\+.+",
    priority=5,
    block=True,
)

emoji_mix.__doc__ = """emoji_mix"""
emoji_mix.__help_type__ = None

emoji_mix.handle()(while_list_handle("emoji_mix"))


def split_emoji(event) -> Tuple[bool, list, list]:
    if len(event.message) != 1 or event.message[0].type != "text":
        return False, [], []
    emoji_data = event.message[0].data.get("text", "").split("+")
    emoji_keys = ["", ""]
    if len(emoji_data) != 2:
        return False, [], []
    for emoji_index in range(len(emoji_data)):
        if not is_emoji(emoji_data[emoji_index]):
            return False, [], []
        # 一个emoji表情可能有多个字符，组合成规定的样子
        # emoji_key为不带"u"的emoji内容，用来查询（原生表里就是不带u的，但是发送链接需要带u）
        emoji_str = ""
        emoji_key = ""
        for i in range(len(emoji_data[emoji_index])):
            if i != 0:
                emoji_str += "-"
                emoji_key += "-"
            h_value = hex(ord(emoji_data[emoji_index][i]))[2:]
            emoji_str += "u" + h_value
            emoji_key += h_value
        emoji_data[emoji_index] = emoji_str
        emoji_keys[emoji_index] = emoji_key
    return True, emoji_data, emoji_keys


def get_emoji_keys(emoji_data, emoji_keys) -> Union[None, Tuple[str, str, str]]:
    if emoji_keys_data.get(emoji_keys[0]) is None:
        if emoji_keys_data.get(emoji_keys[1]) is None:
            return None
        else:
            key_first = emoji_keys[1]   # 第一层的key
    else:
        key_first = emoji_keys[0]
    # 判断date_value是否存在
    for single_key in emoji_keys_data[key_first]:
        if emoji_keys[0] == single_key.get("leftEmoji", "") and emoji_keys[1] == single_key.get("rightEmoji", ""):
            return emoji_data[0], emoji_data[1], single_key.get("date", "")
        if emoji_keys[1] == single_key.get("leftEmoji", "") and emoji_keys[0] == single_key.get("rightEmoji", ""):
            return emoji_data[1], emoji_data[0], single_key.get("date", "")
    return None


@emoji_mix.handle()
async def _(
        event: Union[GroupMessageEvent, PrivateMessageEvent]
):
    result = split_emoji(event)
    if not result[0]:
        await emoji_mix.finish()
    result = get_emoji_keys(result[1], result[2])
    if result is None:
        msg = Message(f"[CQ:reply,id={event.message_id}]") + Message("未找到以上两种emoji的mix表情")
        await emoji_mix.finish(msg)
        return
    else:
        emoji_left = result[0]
        emoji_right = result[1]
        emoji_date = result[2]

    header = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    async with aiohttp.ClientSession() as session:
        # 遍历所有时间
        resp = await session.get(
            f"https://www.gstatic.com/android/keyboard/emojikitchen/{emoji_date}/"
            f"{emoji_left}/{emoji_left}_{emoji_right}.png",
            headers=header)
        if resp.status == 200:
            image_data = await resp.read()
            msg = Message(f"[CQ:reply,id={event.message_id}]") + Message(MessageSegment.image(image_data))
            await emoji_mix.finish(msg)
        msg = Message(f"[CQ:reply,id={event.message_id}]") + Message("未找到以上两种emoji的mix表情\n拉取失败")
        await emoji_mix.finish(msg)
