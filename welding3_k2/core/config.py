from shared.schemas import StreamConfig, ServerConfig
from pathlib import Path
import os

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights'/ "welding3_k2"
IMAGES_DIR = BASE_DIR / 'images'/ "welding3_k2"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)

# 耀安一楼
STREAM_CONFIGS = [
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.230/cam/realmonitor?channel=1&subtype=0",
        target_models={0,7}  #油桶/扫把视角视频流 需要在顶部，目标检测（油桶，扫把）,再检测焊枪接地夹
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.231/cam/realmonitor?channel=1&subtype=0",
        target_models={1}  #垂直向下，检测焊机二次线的视角，分割（人体）来判断二次线的交集的大小
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.247/cam/realmonitor?channel=1&subtype=0",
        target_models={2,3}  # 拍摄开关灯视角，焊枪，搭铁线视频流（目标检测上述物体）,分割检测是否触碰气瓶
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.232/cam/realmonitor?channel=1&subtype=0",
        target_models={4,5}  # 焊台视角，搭铁线视频流，目标检测焊件，搭铁线，刷子，铁锤，图像分类焊接过程
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.238/cam/realmonitor?channel=1&subtype=0",
        target_models={6}  # 焊机开关视频流,目标检测（开关）
    )
]

# 机电学院

# STREAM_CONFIGS = [
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya147369@@192.168.1.127/cam/realmonitor?channel=1&subtype=0",
#         target_models={0}  #油桶/扫把视角视频流 需要在顶部，目标检测（油桶，扫把）
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya147369@@192.168.1.109/cam/realmonitor?channel=1&subtype=0",
#         target_models={1}  #垂直向下，检测焊机二次线的视角，分割（人体）来判断二次线的交集的大小
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya147369@@192.168.1.124/cam/realmonitor?channel=1&subtype=0",
#         target_models={2}  # 拍摄开关灯视角，焊枪，搭铁线视频流（目标检测上述物体）
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya147369@@192.168.1.110/cam/realmonitor?channel=1&subtype=0",
#         target_models={3,4}  # 焊台视角，搭铁线视频流，目标检测焊件，搭铁线，刷子，铁锤，图像分类焊接过程
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya147369@@192.168.1.127/cam/realmonitor?channel=1&subtype=0",
#         target_models={5}  # 焊机开关视频流,目标检测（开关），分割（人体）来判断一次线
#     )
# ]


WELDING3_K2_CONFIG= ServerConfig(
    server_ip='127.0.0.1',
    server_port=5005,
    weights_paths=[
        os.path.join(WEIGHTS_BASE_DIR, 'welding_oil_tank_last.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yolo11l-seg1.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'welding_light_last1.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yolo11l-seg2.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'welding_desk_last.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'welding_cls_last.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'welding_switch_last.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'welding_light_last2.pt')
    ],
    images_dir=IMAGES_DIR,
    static_mount_path='/welding3_k2',#url中的路径
    img_url_path=f'http://127.0.0.1:5005/welding3_k2',
    stream_configs=STREAM_CONFIGS
)

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