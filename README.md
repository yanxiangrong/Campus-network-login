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
   打开`conf/user.json`，(如果没有，则新建)，参考下面内容编辑 。
    ```json
    {
      "username": "xxx",
      "password": "xxx",
      "type": 1
    }
    ```
   | 字段       | 解释                       |
       |----------|--------------------------|
   | username | 用户名                      |
   | password | 密码                       |
   | type     | 账号类型 0: 教师, 1: 学生, 2: 临时 |

4. 安装驱动  
   在连接互联网的环境下运行 `main.py` 会自动下载驱动。  
   **注意**：驱动版本和浏览器版本必须一致，程序在自动下载驱动时会检测浏览器版本并下载对应版本驱动。如果浏览器更新，需要重新运行此程序下载驱动

5. 设置开机自启  
   在 `/usr/lib/systemd/system/` 下面新建一个 `ruijie-login.service`文件，内容参考如下：
    ```ini
    [Unit]
    Description=锐捷校园网自动登录程序
    After=network.target
    Wants=network.target
    
    [Service]
    Type=simple
    User=nobody
    # python 文件位置需要更改为实际位置
    ExecStart=python ruijie-login/main.py
    Restart=on-failure
    RestartSec=600s
    
    [Install]
    WantedBy=multi-user.target
    ```
    ```shell
    systemctl reload
    systemctl enable --now ruijie-login.service
    ```

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