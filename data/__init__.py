import json
import os.path
from typing import Optional
from nonebot.log import logger

# emoji_key_data的数据是字典嵌套字典，每一层字典的key都可能是左emojiCode或右emojiCode
emoji_key_data = {}
emoji_count = 0


def _init_emoji_data(emoji_data_str: str) -> (bool, int, int):
    tmp_emoji_key_data = {}
    cur_emoji_count = 0
    try:
        for _, data in json.loads(emoji_data_str)["data"].items():
            first_emoji = data["emoji"]
            tmp_emoji_key_data[first_emoji] = {}
            for _, all_combination in data["combinations"].items():
                for combination in all_combination:
                    l_emoji = combination["leftEmoji"]
                    r_emoji = combination["rightEmoji"]
                    # 保证first_emoji和second_emoji是不一样的
                    second_emoji = r_emoji if l_emoji == first_emoji else l_emoji
                    tmp_emoji_key_data[first_emoji][second_emoji] = {
                        "url": combination["gStaticUrl"]
                    }
                cur_emoji_count += len(all_combination)
        global emoji_key_data, emoji_count
        emoji_key_data = tmp_emoji_key_data
        pre_emoji_count = emoji_count
        emoji_count = cur_emoji_count
        logger.info(f"init_emoji_data finish. pre_emoji_count = {pre_emoji_count} cur_emoji_count = {cur_emoji_count}")
        return True, pre_emoji_count, cur_emoji_count
    except json.JSONDecodeError:
        logger.error("init_emoji_data json decode fail !")
        return False, 0, 0


# https://github.com/xsalazar/emoji-kitchen
# curl -L --compressed https://raw.githubusercontent.com/xsalazar/emoji-kitchen-backend/main/app/metadata.json -o metadata.json
def init_emoji_data() -> (bool, int, int):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata.json"), "r", encoding="utf-8") as f:
        return _init_emoji_data(f.read())


def reload_emoji_data(emoji_data: str):
    is_success, pre_count, cur_count = _init_emoji_data(emoji_data)
    if not is_success:
        return is_success, pre_count, cur_count
    # 成功的话重写文件
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "metadata.json"), "w", encoding="utf-8") as f:
        f.write(emoji_data)
        return is_success, pre_count, cur_count


def get_emoji_url(left_emoji, right_emoji) -> str | None:
    emoji_data = emoji_key_data.get(left_emoji, {}).get(right_emoji)
    if emoji_data is None:
        left_emoji, right_emoji = right_emoji, left_emoji

    emoji_data = emoji_key_data.get(left_emoji, {}).get(right_emoji)
    if emoji_data is None:
        return None
    return emoji_key_data[left_emoji][right_emoji]["url"]


init_emoji_data()
