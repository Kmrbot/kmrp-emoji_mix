import aiohttp
from typing import Union, Tuple
from emoji import is_emoji
from nonebot.matcher import Matcher
from protocol_adapter.protocol_adapter import ProtocolAdapter
from protocol_adapter.adapter_type import AdapterGroupMessageEvent, AdapterPrivateMessageEvent
from nonebot import on_regex
from utils.permission import white_list_handle
from . import data

emoji_mix = on_regex(
    pattern=r"^.+(\+|\＋).+$",
    priority=5,
    block=False,
)

emoji_mix.__doc__ = """emoji_mix"""
emoji_mix.__help_type__ = None

emoji_mix.handle()(white_list_handle("emoji_mix"))


def split_emoji(event) -> Tuple[bool, str, str]:
    if len(event.message) != 1 or event.message[0].type != "text":
        return False, "", ""
    emoji_data = event.message[0].data.get("text", "").split("+")
    if len(emoji_data) != 2:
        return False, "", ""
    for emoji_index in range(len(emoji_data)):
        emoji_data[emoji_index] = emoji_data[emoji_index].replace("\u202a", "").replace("\u202c", "")
        if not is_emoji(emoji_data[emoji_index]):
            return False, "", ""
    return True, emoji_data[0], emoji_data[1]


@emoji_mix.handle()
async def _(
        matcher: Matcher,
        event: Union[AdapterGroupMessageEvent, AdapterPrivateMessageEvent]
):
    result = split_emoji(event)
    if not result[0]:
        await emoji_mix.finish()

    # 仅当符合emoji要求才阻断
    matcher.stop_propagation()
    url = data.get_emoji_url(result[1], result[2])
    if url is None:
        msg = ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("未找到以上两种emoji的mix表情")
        return await emoji_mix.finish(msg)

    header = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    async with aiohttp.ClientSession() as session:
        # 遍历所有时间
        resp = await session.get(url, headers=header)
        if resp.status == 200:
            image_data = await resp.read()
            msg = ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.image(image_data)
            await emoji_mix.finish(msg)
        msg = ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("未找到以上两种emoji的mix表情\n拉取失败")
        await emoji_mix.finish(msg)
