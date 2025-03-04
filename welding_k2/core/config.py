from ..schemas import StreamConfig, ServerConfig

STREAM_CONFIGS = [
    StreamConfig(
        rtsp_url="rtsp://admin:ya123456@192.168.0.103/cam/realmonitor?channel=1&subtype=0",
        target_models={0}  #油桶/扫把视角视频流
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:ya123456@192.168.0.105/cam/realmonitor?channel=1&subtype=0",
        target_models={1,2}  # 焊台视角，搭铁线视频流
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:ya123456@192.168.0.107/cam/realmonitor?channel=1&subtype=0",
        target_models={3, 4}  # 开关灯视角，焊机，焊枪，搭铁线视频流
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:ya123456@192.168.0.106/cam/realmonitor?channel=1&subtype=0",
        target_models={5}  # 焊机开关视频流
    )
]

WELDING_K2_CONFIG= ServerConfig(
    server_ip='127.0.0.1',
    server_port=5002,
    #/home/dxc/ai_exam/weights/welding_k2/welding_desk_cls_1121.pt
    weights_paths=['/home/dxc/ai_exam/weights/welding_k2/yz_oil_tank.pt',
                 '/home/dxc/ai_exam/weights/welding_k2/yz_grounding_wire.pt',
                 '/home/dxc/ai_exam/weights/welding_k2/welding_desk_cls_1121.pt',
                 '/home/dxc/ai_exam/weights/welding_k2/yz_switching_light_view.pt',
                 '/home/dxc/ai_exam/weights/welding_k2/yolo11x-pose.pt',
                 '/home/dxc/ai_exam/weights/welding_k2/yz_welding_switches.pt'],
    images_dir="/home/dxc/ai_exam/images/welding_k2",
    static_mount_path='/welding_k2',#url中的路径
    img_url_path=f'http://127.0.0.1:5002/welding_k2',
    stream_configs=STREAM_CONFIGS
)