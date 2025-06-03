from shared.service_init import init_service

# 初始化服务
service_init = init_service("welding1_k2")

# 导出配置和日志
config = service_init.config
logger = service_init.logger
service_name = service_init.service_name
