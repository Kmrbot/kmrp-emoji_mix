import json
import os.path
from typing import Optional
from nonebot.log import logger

# emoji_key_data的数据是字典嵌套字典，每一层字典的key都可能是左emojiCode或右emojiCode
emoji_key_data = {}


def init_emoji_data():
    emoji_key_length = 0
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata.json"), encoding="utf-8") as f:
        try:
            for _, data in json.load(f)["data"].items():
                first_emoji = data["emoji"]
                emoji_key_data[first_emoji] = {}
                for _, combination in data["combinations"].items():
                    l_emoji = combination["leftEmoji"]
                    r_emoji = combination["rightEmoji"]
                    # 保证first_emoji和second_emoji是不一样的
                    second_emoji = r_emoji if l_emoji == first_emoji else l_emoji
                    emoji_key_data[first_emoji][second_emoji] = {
                        "url": combination["gStaticUrl"]
                    }
                emoji_key_length += len(data["combinations"])
        except json.JSONDecodeError:
            logger.error("init_emoji_data json decode fail !")
            return None
    logger.info(f"init_emoji_data finish. emoji_key_length = {emoji_key_length}")


def get_emoji_url(left_emoji, right_emoji) -> Optional[str]:
    emoji_data = emoji_key_data.get(left_emoji, {}).get(right_emoji)
    if emoji_data is None:
        left_emoji, right_emoji = right_emoji, left_emoji

    emoji_data = emoji_key_data.get(left_emoji, {}).get(right_emoji)
    if emoji_data is None:
        return None
    return emoji_key_data[left_emoji][right_emoji]["url"]


init_emoji_data()
