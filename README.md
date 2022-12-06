# 锐捷校园网自动登录程序

该程序用于监测校园网环境并在下线后自动登录。

## 要求

* python >= 3.10
* 安装有 google-chrome (推荐) 或者 chromium, edge (未测试), brave-browser (未测试)
* Linux (推荐) 或 windows 10 以上

## 安装

1. 安装 chromium 浏览器
    ```shell
    apt install chromium chromium-l10n
    ```
2. 安装 python 依赖
   ```shell
   pip install -r requirements.txt
   ```

3. 填写账号信息  
   打开`conf/user.json`，参考下面内容编辑 (实际填写不能包含注释)。
   ```json
   {
     "username": "xxx", // 用户名
     "password": "xxx", // 密码
     "type": 1 // 账号类型, 0: 教师, 1: 学生, 2: 临时
   }
   ```
4. 下载驱动  
   在连接互联网的环境下运行 `main.py` 会自动下载驱动。

## 运行

```shell
python main.py
```

## Docker 部署

设置docker国内镜像

```shell
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://kxfrmcpz.mirror.aliyuncs.com", "http://hub-mirror.c.163.com"]
}
EOF
```

构建

```shell
docker compose up -d
```