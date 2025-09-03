from shared.service_init import init_service

# 初始化服务
service_init = init_service("basket_k2")

# 导出配置和日志
config = service_init.config
logger = service_init.logger
service_name = service_init.service_name

#1 设置警戒区
#2 检查悬挂机构
#3 检查钢丝绳
#4 检查吊篮作业平台
#5 检查提升机
#6 检查安全锁
#7 检查电气系统
#8 空载试验
#9 检测安全带挂设
#10 检测到达位置，完成清洗作业
#11 检测清理现场
#12 检测撤出安全警戒