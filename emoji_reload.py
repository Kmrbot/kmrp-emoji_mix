from typing import Annotated
import requests
from nonebot.log import logger
from nonebot.rule import to_me, Namespace, ArgumentParser
from nonebot.params import ShellCommandArgs
from protocol_adapter.adapter_type import AdapterMessageEvent
from protocol_adapter.protocol_adapter import ProtocolAdapter
from nonebot import on_shell_command
from utils.permission import white_list_handle
from utils.permission import only_me
from utils.push_manager import PushManager
from utils.task_deliver import TaskDeliverManager
from .data import init_emoji_data, reload_emoji_data

parser = ArgumentParser()
parser.add_argument("-r", "--redownload", action="store_true")
emoji_reload = on_shell_command(
    r"emoji_reload",
    rule=to_me(),
    priority=5,
    parser=parser,
    block=False,
)

emoji_reload.__doc__ = """emoji_mix"""
emoji_reload.__help_type__ = None

emoji_reload.handle()(white_list_handle("emoji_mix"))
emoji_reload.handle()(only_me)

is_executing = False

async def reload(**kwargs):
    global is_executing
    is_redownload = kwargs.get("redownload")
    msg_type = kwargs.get("msg_type")
    msg_type_id = kwargs.get("msg_type_id")
    if not is_redownload:
        is_success, pre_emoji_count, cur_emoji_count = init_emoji_data()
    else:
        url = "https://raw.githubusercontent.com/xsalazar/emoji-kitchen-backend/main/app/metadata.json"
        req = requests.get(url, allow_redirects=True)
        if req.status_code != 200:
            logger.warning(f"emoji_reload url {url} get fail ! status_code = {req.status_code}")
            is_success = False
            pre_emoji_count = 0
            cur_emoji_count = 0
        else:
            is_success, pre_emoji_count, cur_emoji_count = reload_emoji_data(emoji_data=req.text)

    if is_success:
        ret_msg = f"emoji热更新完成。当前总emoji数量： {cur_emoji_count}， 新增{cur_emoji_count - pre_emoji_count}个。"
    else:
        ret_msg = "emoji热更新失败。"
    is_executing = False
    PushManager.notify(PushManager.PushData(
        msg_type=msg_type,
        msg_type_id=msg_type_id,
        message=ProtocolAdapter.MS.text(ret_msg)
    ))


@emoji_reload.handle()
async def _(
    event: AdapterMessageEvent,
    params: Annotated[Namespace, ShellCommandArgs()]
):
    msg = ProtocolAdapter.MS.reply(event)
    params = vars(params)

    global is_executing
    if is_executing:
        await emoji_reload.finish(msg + ProtocolAdapter.MS.text("当前已有reload任务执行中！"))

    is_executing = True
    TaskDeliverManager.add_task(
        reload,
        redownload=params.get("redownload"),
        msg_type=ProtocolAdapter.get_msg_type(event),
        msg_type_id=ProtocolAdapter.get_msg_type_id(event))
    return await emoji_reload.finish(msg + ProtocolAdapter.MS.text("已启动emoji热更新流程。"))
