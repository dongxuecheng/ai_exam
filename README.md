# ai_exam

特征作业考核重构

## 快速开始

### 自动迁移到UV（推荐）

如果你是从conda环境迁移，可以使用自动迁移脚本：

```bash
cd ai_exam
./migrate_to_uv.sh
```

### 手动安装UV

```bash
# 在执行安装命令前，先设置环境变量
export UV_RELEASES_URL="https://download.fastgit.org/astral-sh/uv/releases"
wget -qO- https://astral.sh/uv/install.sh | sh

# Shell自动补全
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
echo 'eval "$(uvx --generate-shell-completion bash)"' >> ~/.bashrc

# 设置清华源永久
echo 'export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"' >> ~/.bashrc
source ~/.bashrc

# UV创建虚拟环境
uv venv -p python3.12

# 激活虚拟环境
source .venv/bin/activate

# UV安装包
uv pip install -r requirements.txt
```

## 搭建环境

```bash
git clone https://github.com/dongxuecheng/ai_exam.git
cd ai_exam

# 使用UV创建虚拟环境
uv venv -p python3.12

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt
```

将权重复制到weights文件夹

## 如何启动服务

### 方法一：使用UV管理器（推荐）

```bash
cd ai_exam

# 首次使用：设置环境
./uv_manager.sh setup

# 查看所有可用服务
./uv_manager.sh list

# 启动特定服务
./uv_manager.sh start welding1_k2
./uv_manager.sh start basket_k2
./uv_manager.sh start sling_k2
```

### 方法二：直接使用启动脚本

```bash
cd ai_exam

# 确保虚拟环境已激活
source .venv/bin/activate

# 启动welding1_k2服务
chmod +x start_welding_k2.sh
./start_welding_k2.sh

# 或者启动其他服务
chmod +x scripts/start_basket_k2.sh
./scripts/start_basket_k2.sh
```

### 可用服务列表

- `welding1_k1` - 焊接K1服务 (端口: 5001)
- `welding1_k2` - 焊接K2服务 (端口: 5002)
- `welding2_k2` - 焊接2-K2服务 (端口: 5003)
- `welding3_k2` - 焊接3-K2服务 (端口: 5007)
- `basket_k2` - 吊篮K2服务 (端口: 5005)
- `sling_k2` - 吊索K2服务 (端口: 5006)
