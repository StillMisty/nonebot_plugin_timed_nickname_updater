from nonebot import require, get_bots
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot

import re
import json

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (  # noqa: E402
    CommandMeta,
    on_alconna,
    AlconnaMatch,
    Match,
    Alconna,
    Args,
)

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store  # noqa: E402

name_updater = on_alconna(
    Alconna(
        "昵称更新",
        Args["value", int, 1]["days", int, 1],
        meta=CommandMeta(
            compact=True,
            description="更新昵称中的数字",
            usage="昵称更新 <更新值> <间隔>",
        ),
    ),
    aliases={"名称更新"},
    priority=5,
    block=True,
)

name_reset = on_alconna(
    Alconna(
        "昵称重置",
        Args["value", int, 0],
        meta=CommandMeta(
            compact=True, description="重置昵称中的数字", usage="昵称重置 <新值>"
        ),
    ),
    aliases={"名称重置"},
    priority=5,
    block=True,
)


@name_updater.handle()
async def _(
    event: GroupMessageEvent,
    value: Match = AlconnaMatch("value"),
    days: Match = AlconnaMatch("days"),
):
    value = value.result
    days = days.result

    if (not -65536 <= value <= 65535) or (not 0 < days <= 65535):
        await name_updater.finish("数值超出范围")

    group_id = event.group_id
    user_id = event.user_id

    # 从昵称中提取出数字并递增
    card = event.sender.card or event.sender.nickname

    try:
        update_name(card, value)
    except ValueError:
        await name_updater.finish("昵称中没有数字")

    # 更新数据
    set_data(group_id, user_id, value, days)
    await name_updater.finish(f"昵称变化将{value}，每{days}天更新一次")


@name_reset.handle()
async def _(bot: Bot, event: GroupMessageEvent, value: Match = AlconnaMatch("value")):
    group_id = event.group_id
    user_id = event.user_id
    value = value.result

    card = event.sender.card or event.sender.nickname

    try:
        new_card = reset_name(card, value)
    except ValueError:
        await name_reset.finish("昵称中没有数字")

    await bot.set_group_card(group_id=group_id, user_id=user_id, card=new_card)
    await name_reset.finish(f"昵称重置为{new_card}")


def get_data_file():
    """获取数据文件路径，集中管理文件路径"""
    return store.get_plugin_data_file("nonebot_plugin_timed_nickname_updater.json")


def load_data() -> dict[str, dict[str, dict[str, int]]]:
    """加载数据文件"""
    data_file = get_data_file()
    if not data_file.exists() or data_file.stat().st_size == 0:
        return {}
    return json.loads(data_file.read_text())


def save_data(data: dict):
    """保存数据到文件"""
    data_file = get_data_file()
    data_file.write_text(json.dumps(data, ensure_ascii=False, indent=4))


def update_name(name: str, value: int) -> str:
    """
    更新字符串中的数字值
    参数:
        name (str): 包含数字的字符串
        value (int): 要增加的值
    返回:
        str: 更新数字后的字符串
    异常:
        ValueError: 当输入字符串中没有数字时抛出
    """
    num = re.search(r"\d+", name)
    if num:
        num = int(num.group())
        return re.sub(r"\d+", str(num + value), name)
    else:
        raise ValueError("昵称中没有数字")


def reset_name(name: str, value: int) -> str:
    """
    设置新字符串中的数字值
    参数:
        name (str): 包含数字的字符串
        value (int): 要设置的值
    返回:
        str: 设置数字后的字符串
    异常:
        ValueError: 当输入字符串中没有数字时抛出
    """
    num = re.search(r"\d+", name)
    if num:
        num = int(num.group())
        return re.sub(r"\d+", str(value), name)
    else:
        raise ValueError("昵称中没有数字")


def set_data(group_id: int, user_id: int, value: int, days: int):
    """设置用户数据到存储文件中。如果文件或数据结构不存在，会自动初始化。
    Args:
        group_id (int): QQ群号
        user_id (int): QQ用户ID
        value (int): 增加的数值
        days (int): 间隔的天数
    存储结构示例:
    {
        "群号1": {
            "用户1": {
                "value": 100,  # 增加的数值
                "days": 30,    # 间隔的天数
                "last": 0      # 上次更新后经过的天数
            }
        }
    }
    """
    data = load_data()

    # 更新数据
    if str(group_id) not in data:
        data[str(group_id)] = {}
    data[str(group_id)][str(user_id)] = {"value": value, "days": days, "last": 0}

    save_data(data)


@scheduler.scheduled_job("cron", hour=0, minute=2)
async def timed_updater():
    data = load_data()
    bots = get_bots()

    updates = []
    for group_id, users in data.items():
        for user_id, user_data in users.items():
            # 积累所有更新任务
            if user_data["last"] + 1 >= user_data["days"]:
                updates.append((group_id, user_id, user_data))
            else:
                user_data["last"] += 1

    for bot in bots.values():
        for group_id, user_id, user_data in updates:
            card = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
            card = card["card"] or card["nickname"]

            try:
                new_card = update_name(card, user_data["value"])
            except ValueError:
                continue

            await bot.set_group_card(group_id=group_id, user_id=user_id, card=new_card)
            user_data["last"] = 0

    save_data(data)
