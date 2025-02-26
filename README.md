# nonebot_plugin_timed_nickname_updater

## 📖 介绍

基于Nonebot2，按时更新群友昵称中日期，机器人账号需要为管理员。

## 💿 安装

使用nb-cli安装插件

```shell
nb plugin install nonebot_plugin_timed_nickname_updater
```

使用pip安装插件

```shell
pip install nonebot_plugin_timed_nickname_updater
```

## 🕹️ 使用

1. `昵称更新 <更新值> <间隔>`：更新值为整数，默认为 1，间隔为整数，以天为单位，默认为 1
2. `昵称重置 <更新值>`：将昵称中数字重置为更新值，默认为 0

示例：
无敌鲍龙战士（禁欲第24天）
一天后更新为
无敌鲍龙战士（禁欲第25天）
