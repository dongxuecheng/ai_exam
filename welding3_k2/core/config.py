from shared.utils.config import get_service_config
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights' / "welding3_k2"
IMAGES_DIR = BASE_DIR / 'images' / "welding3_k2"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# 使用YAML配置创建服务器配置
WELDING3_K2_CONFIG = get_service_config('welding3_k2')

"""
[复位]
1=油桶需放到指定位置
2=总开关需处于关闭状态
3=漏电保护开关需处于关闭状态
4=焊机开关需处于关闭状态
5=气阀需处于关闭状态
6=焊枪需处于指定位置
7=接地夹需处于指定位置

[实操]
1=排除危险源
2=检查电源线
3=检查二次线
4=检查焊机外壳
5=检查焊机合格证
6=检查供气系统


7=打开总开关
8=打开漏电保护开关
9=打开焊机开关
10=夹好接地夹

11=打开气阀


12=摆放焊件
13=试焊
14=焊接作业

15=关闭焊机开关
16=关闭漏电保护开关
17=关闭总开关

18=关闭气阀

19=清除焊渣
20=检查考件


21=放回焊枪
22=放回接地夹
23=焊后场地清理
"""
