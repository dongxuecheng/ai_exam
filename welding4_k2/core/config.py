from shared.service_init import init_service

# 初始化服务
service_init = init_service("welding4_k2")

# 导出配置和日志
config = service_init.config
logger = service_init.logger
service_name = service_init.service_name

"""
[复位]
1=油桶需放到指定位置
2=气割枪需处于指定位置
3=去除焊台上的焊件

[实操]
1=排除危险源
2=检查气管
3=检查切刀
4=检查阀门


5=摆放焊件
6=切开焊件


7=关闭阀门
8=焊后场地清理
9=放回气割枪
"""
