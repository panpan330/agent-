# 阶段 4 第 8 节：本地启动 Qdrant

> 本节结论：Qdrant 不是安装在 Python 项目里的一个普通依赖，而是一个独立运行的向量数据库服务。我们当前选择在 VMware Ubuntu 虚拟机里的 Docker 中启动 Qdrant，然后让 Windows 上的 `ai-service` 以后通过 `http://Ubuntu虚拟机IP:6333` 访问它。本节先学会 Docker 镜像、容器、端口映射、数据持久化和启动验证；暂时不写入真实向量，也不接入 RAG 代码。

## 本节状态说明

这一节和前面纯文档课不同，它需要在你的 VMware Ubuntu 终端里实际执行命令。

当前已经完成实机验证：

```text
Docker：Docker version 29.1.4
Qdrant 容器：qdrant/qdrant
Qdrant 版本：1.18.2
Ubuntu IP：192.168.88.10
Windows 访问地址：http://192.168.88.10:6333
验证结果：Ubuntu curl 和 Windows 浏览器均可访问 Qdrant REST API。
```

验证链路是：

```text
Windows 浏览器
-> 192.168.88.10:6333
-> VMware Ubuntu
-> Docker 端口映射
-> Qdrant 容器
```

本节当前状态：

```text
已完成。
```

补充说明：

```text
ds：未找到命令
```

这只是误输入了一个 Linux 不存在的命令，和 Qdrant 启动没有关系。

判断 Qdrant 是否成功，主要看：

```text
docker ps --filter name=qdrant
curl http://localhost:6333
Windows 访问 http://UbuntuIP:6333
```

## 生成笔记前的教学复核

这一节必须讲清：

```text
1. 为什么 Qdrant 是一个服务，不是 Python 包。
2. Docker 镜像和容器是什么。
3. 为什么我们把 Qdrant 放在 VMware Ubuntu 的 Docker 里。
4. Windows 主项目如何访问 Ubuntu 虚拟机里的 Qdrant。
5. 6333 和 6334 端口分别是什么。
6. docker pull、docker run、docker ps、docker logs 分别做什么。
7. -p 6333:6333 是什么。
8. -v ~/qdrant_storage:/qdrant/storage 是什么。
9. 怎么确认 Qdrant 启动成功。
10. 访问失败时怎么排查。
```

## 本节一句话定位

第 6 节讲：

```text
为什么需要向量数据库，为什么先选 Qdrant。
```

第 7 节讲：

```text
Qdrant 里的数据模型：collection、point、vector、payload。
```

第 8 节开始进入环境实践：

```text
先把 Qdrant 服务跑起来。
```

注意，本节只解决：

```text
Qdrant 服务能不能启动、能不能访问。
```

不解决：

```text
怎么创建 collection。
怎么写入 embedding。
怎么做 RAG 检索。
```

这些放到后面的章节。

## 当前推荐结构

你现在的实际情况是：

```text
Windows：放 Java + Python + AI 主项目
VMware Ubuntu：已经装了 Docker
Qdrant：准备运行在 Ubuntu 的 Docker 容器里
```

所以整体结构是：

```text
Windows
└── D:/wendang/java+python+ai
    └── projects/ai-service
        └── 以后通过 HTTP 访问 Qdrant

VMware Ubuntu
└── Docker
    └── qdrant 容器
        ├── REST API: 6333
        ├── Web UI: 6333/dashboard
        └── gRPC API: 6334
```

未来访问链路是：

```text
Windows ai-service
-> http://Ubuntu虚拟机IP:6333
-> Ubuntu Docker 端口映射
-> Qdrant 容器 6333
```

这句话你要能讲清楚：

```text
Qdrant 跑在 Ubuntu 虚拟机里，但 Windows 项目可以通过网络访问它。
```

## 基础知识铺垫：Qdrant 是服务，不是普通依赖

你后面会看到 Python 里可能安装：

```bash
pip install qdrant-client
```

或者：

```bash
uv add qdrant-client
```

但要注意：

```text
qdrant-client 只是 Python 客户端。
Qdrant 服务本身是向量数据库进程。
```

可以类比 MySQL：

```text
mysql server：真正保存数据的数据库服务
pymysql / mysql-connector：Python 连接 MySQL 的客户端库
```

Qdrant 也是：

```text
qdrant server：真正保存向量和 payload 的数据库服务
qdrant-client：Python 连接 Qdrant 的客户端库
```

所以只安装 Python 包不等于 Qdrant 已经运行。

你必须有一个正在运行的 Qdrant 服务。

本节就是启动这个服务。

## 基础知识铺垫：Docker 是什么

Docker 可以先理解成：

```text
一种把应用和运行环境打包并隔离运行的工具。
```

传统安装软件可能会遇到：

```text
依赖版本不一致
系统环境不一致
配置散落在机器各处
卸载不干净
换机器难复现
```

Docker 的思路是：

```text
把应用和它需要的运行环境打包成镜像。
需要运行时，用镜像创建容器。
```

所以学习 Docker，先抓住两个词：

```text
image：镜像
container：容器
```

## image 镜像是什么

镜像可以理解成：

```text
一个应用的安装包 + 运行环境模板。
```

例如：

```text
qdrant/qdrant
```

就是 Qdrant 官方 Docker 镜像名。

它里面包含了运行 Qdrant 需要的程序和基础环境。

当你执行：

```bash
docker pull qdrant/qdrant
```

含义是：

```text
从 Docker 镜像仓库下载 qdrant/qdrant 镜像到 Ubuntu 本机。
```

这一步类似：

```text
把安装包下载下来。
```

但镜像本身还没有运行。

## container 容器是什么

容器可以理解成：

```text
镜像运行起来之后的实例。
```

当你执行：

```bash
docker run qdrant/qdrant
```

含义是：

```text
用 qdrant/qdrant 镜像启动一个 Qdrant 容器。
```

镜像和容器的关系类似：

```text
镜像：类 / 模板 / 安装包
容器：对象 / 运行实例 / 正在跑的程序
```

同一个镜像可以启动多个容器。

但我们学习阶段只需要一个 Qdrant 容器。

## 为什么用 Docker 跑 Qdrant

原因很直接：

```text
1. 不需要手动编译 Qdrant。
2. 不需要把 Qdrant 安装进系统各个目录。
3. 启动、停止、删除都比较清晰。
4. 以后换机器也容易复现。
5. 数据目录可以单独挂载，便于理解持久化。
```

官方文档也把 Docker 作为本地快速开始方式之一。

本节不追求生产部署。

我们的目标是：

```text
开发学习环境能跑起来。
```

## 端口是什么

服务运行起来后，外部要通过端口访问它。

可以先这样理解：

```text
IP 地址：找到哪台机器。
端口：找到这台机器上的哪个服务。
```

例如：

```text
http://192.168.1.50:6333
```

其中：

```text
192.168.1.50：Ubuntu 虚拟机 IP
6333：Qdrant REST API 端口
```

Qdrant 常用端口：

| 端口 | 用途 |
| --- | --- |
| 6333 | HTTP REST API、健康检查、Web UI |
| 6334 | gRPC API |
| 6335 | 分布式部署相关，当前不用 |

学习阶段重点记：

```text
6333 是我们最常用的访问端口。
```

## 什么是端口映射

Qdrant 跑在 Docker 容器里。

容器内部有自己的端口：

```text
容器内部 Qdrant 监听 6333
```

但 Windows 不能直接进入容器内部访问。

所以要把 Ubuntu 主机端口映射到容器端口：

```bash
-p 6333:6333
```

含义是：

```text
Ubuntu 主机的 6333 端口 -> Qdrant 容器的 6333 端口
```

格式是：

```text
-p 主机端口:容器端口
```

所以：

```bash
-p 6334:6334
```

含义是：

```text
Ubuntu 主机的 6334 端口 -> Qdrant 容器的 6334 端口
```

如果不映射端口，容器可能在内部运行正常，但 Windows 访问不到。

## 什么是数据持久化

数据库最重要的问题之一是：

```text
容器删了以后，数据还在不在？
```

如果不做数据持久化，数据可能只存在容器内部。

容器删除后，数据也可能丢失。

所以要把 Qdrant 容器内部的数据目录挂载到 Ubuntu 主机目录：

```bash
-v ~/qdrant_storage:/qdrant/storage
```

含义是：

```text
Ubuntu 主机目录 ~/qdrant_storage
映射到
容器内部目录 /qdrant/storage
```

Qdrant 在容器内部写入 `/qdrant/storage` 时，实际数据会落到 Ubuntu 的：

```text
~/qdrant_storage
```

这样即使以后删除容器，只要这个目录还在，数据就有机会继续保留。

注意：

```text
删除容器 != 一定删除数据
删除挂载目录 = 数据会丢
```

## 本节操作总览

你需要在 VMware Ubuntu 终端里执行：

```text
1. 确认 Docker 可用。
2. 创建 Qdrant 数据目录。
3. 拉取 Qdrant 镜像。
4. 启动 Qdrant 容器。
5. 查看容器是否运行。
6. 在 Ubuntu 内部访问 Qdrant。
7. 查 Ubuntu 虚拟机 IP。
8. 在 Windows 浏览器或 PowerShell 访问 Qdrant。
```

下面每一步都写清楚。

## 第 1 步：确认 Docker 可用

在 VMware Ubuntu 终端执行：

```bash
docker --version
```

你应该看到类似：

```text
Docker version 26.x.x, build ...
```

这表示 Docker 命令存在。

再执行：

```bash
docker ps
```

如果能看到表头：

```text
CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
```

说明当前用户可以查看 Docker 容器。

如果报权限错误，例如：

```text
permission denied while trying to connect to the Docker daemon socket
```

可以临时用：

```bash
sudo docker ps
```

如果 `sudo docker ps` 可以，说明 Docker 是好的，只是当前用户没有 Docker 权限。

学习阶段可以先用 `sudo docker ...` 继续。

## 第 2 步：创建 Qdrant 数据目录

在 Ubuntu 里执行：

```bash
mkdir -p ~/qdrant_storage
```

解释：

```text
mkdir：创建目录
-p：如果上级目录不存在就一起创建；如果目录已存在也不报错
~/qdrant_storage：当前用户 home 目录下的 qdrant_storage
```

查看目录：

```bash
ls -ld ~/qdrant_storage
```

你会看到类似：

```text
drwxr-xr-x 2 your_user your_user ... /home/your_user/qdrant_storage
```

这个目录以后保存 Qdrant 数据。

## 第 3 步：拉取 Qdrant 镜像

执行：

```bash
docker pull qdrant/qdrant
```

如果你需要 sudo：

```bash
sudo docker pull qdrant/qdrant
```

解释：

```text
docker pull：下载镜像
qdrant/qdrant：Qdrant 官方镜像名
```

拉取完成后查看镜像：

```bash
docker images qdrant/qdrant
```

可能看到类似：

```text
REPOSITORY        TAG       IMAGE ID       CREATED        SIZE
qdrant/qdrant     latest    xxxxxxxx       ...            ...
```

这表示镜像已经在 Ubuntu 里了。

## 第 4 步：启动 Qdrant 容器

推荐先用这个命令：

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v ~/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

如果你需要 sudo：

```bash
sudo docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v ~/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

逐行解释：

```text
docker run：创建并启动容器
-d：后台运行，不占住终端
--name qdrant：把容器命名为 qdrant
-p 6333:6333：把 Ubuntu 6333 映射到容器 6333
-p 6334:6334：把 Ubuntu 6334 映射到容器 6334
-v ~/qdrant_storage:/qdrant/storage：把数据保存到 Ubuntu 的 ~/qdrant_storage
qdrant/qdrant：使用这个镜像启动
```

执行成功后，会输出一长串容器 ID，例如：

```text
8b1f0c9a...
```

这表示容器已经被创建并启动。

## 如果提示容器名已存在

如果你看到：

```text
Conflict. The container name "/qdrant" is already in use
```

说明以前已经创建过名叫 `qdrant` 的容器。

先查看：

```bash
docker ps -a --filter name=qdrant
```

如果它已经存在但没运行，可以启动：

```bash
docker start qdrant
```

如果你确认旧容器不要了，可以删除旧容器：

```bash
docker rm qdrant
```

然后重新执行 `docker run`。

注意：

```text
docker rm qdrant 只删除容器。
如果数据挂载在 ~/qdrant_storage，目录还在，数据不会因为删除容器自动消失。
```

但不要随便删除：

```bash
rm -rf ~/qdrant_storage
```

因为这会删除数据目录。

## 第 5 步：查看 Qdrant 容器状态

执行：

```bash
docker ps --filter name=qdrant
```

你应该看到类似：

```text
CONTAINER ID   IMAGE            STATUS         PORTS                                           NAMES
xxxxxxxxxxxx   qdrant/qdrant    Up ...         0.0.0.0:6333->6333/tcp, 0.0.0.0:6334->6334/tcp  qdrant
```

关键看：

```text
STATUS 是 Up
PORTS 里有 6333->6333
NAMES 是 qdrant
```

如果没有容器，说明没启动。

如果 STATUS 不是 Up，查看日志：

```bash
docker logs qdrant
```

日志可以告诉你启动失败原因。

## 第 6 步：在 Ubuntu 里访问 Qdrant

先在 Ubuntu 里执行：

```bash
curl http://localhost:6333
```

如果成功，通常会看到类似 JSON 响应，里面包含 Qdrant 标识或版本信息。

再访问 collections API：

```bash
curl http://localhost:6333/collections
```

刚启动时没有 collection，也没关系。

你重点看：

```text
能不能连上 Qdrant 服务。
```

如果提示：

```text
Connection refused
```

通常说明：

```text
1. 容器没运行。
2. 端口没映射。
3. Qdrant 启动失败。
```

这时回到：

```bash
docker ps
docker logs qdrant
```

排查。

## 第 7 步：查 Ubuntu 虚拟机 IP

Windows 访问 Ubuntu，需要知道 Ubuntu 的 IP。

在 Ubuntu 执行：

```bash
ip addr
```

你会看到多个网卡。

常见名字可能是：

```text
ens33
eth0
enp0s3
```

找类似这样的地址：

```text
inet 192.168.x.x/24
```

例如：

```text
inet 192.168.1.50/24
```

这里 Ubuntu IP 就是：

```text
192.168.1.50
```

也可以用更简洁的命令：

```bash
hostname -I
```

它可能输出：

```text
192.168.1.50
```

如果输出多个 IP，你需要选 Windows 能访问的那个。

## 第 8 步：在 Windows 访问 Ubuntu Qdrant

假设 Ubuntu IP 是：

```text
192.168.1.50
```

那在 Windows 浏览器访问：

```text
http://192.168.1.50:6333
```

或者访问 Qdrant Web UI：

```text
http://192.168.1.50:6333/dashboard
```

也可以在 Windows PowerShell 执行：

```powershell
Invoke-RestMethod http://192.168.1.50:6333
```

或者：

```powershell
Invoke-RestMethod http://192.168.1.50:6333/collections
```

如果能返回结果，说明：

```text
Windows -> Ubuntu -> Docker -> Qdrant
```

这条链路通了。

## 如果 Windows 访问不了怎么办

按顺序排查，不要乱改。

### 1. 先确认 Ubuntu 自己能访问

在 Ubuntu：

```bash
curl http://localhost:6333
```

如果 Ubuntu 自己都访问不了，先查 Qdrant 容器：

```bash
docker ps --filter name=qdrant
docker logs qdrant
```

### 2. 确认端口映射

在 Ubuntu：

```bash
docker ps --filter name=qdrant
```

看 PORTS 是否有：

```text
0.0.0.0:6333->6333/tcp
```

如果只有容器内部端口，没有主机映射，Windows 访问不到。

### 3. 确认 Ubuntu IP

在 Ubuntu：

```bash
hostname -I
```

确认你在 Windows 访问的是正确 IP。

### 4. 确认 Windows 能 ping 到 Ubuntu

在 Windows PowerShell：

```powershell
ping 192.168.1.50
```

如果 ping 不通，可能是 VMware 网络模式或防火墙问题。

### 5. 检查 VMware 网络模式

VMware 常见网络模式：

```text
NAT
Bridged
Host-only
```

学习阶段通常 NAT 或 Bridged 都可能可用。

如果 Windows 访问不了 Ubuntu，问题可能在：

```text
虚拟机 IP 不是 Windows 可访问网段
VMware 网络适配器配置
Ubuntu 防火墙
Windows 防火墙
端口映射没做好
```

不要一上来重装 Docker。

先按链路排查。

### 6. 检查 Ubuntu 防火墙

在 Ubuntu：

```bash
sudo ufw status
```

如果防火墙启用并阻止 6333，可以临时允许：

```bash
sudo ufw allow 6333/tcp
```

如果你要用 gRPC，再允许：

```bash
sudo ufw allow 6334/tcp
```

学习阶段重点是 6333。

## 常用 Docker 命令

启动容器：

```bash
docker start qdrant
```

停止容器：

```bash
docker stop qdrant
```

重启容器：

```bash
docker restart qdrant
```

查看运行中的容器：

```bash
docker ps
```

查看所有容器：

```bash
docker ps -a
```

查看日志：

```bash
docker logs qdrant
```

持续看日志：

```bash
docker logs -f qdrant
```

删除已停止容器：

```bash
docker rm qdrant
```

查看镜像：

```bash
docker images
```

## 不要随便执行的命令

下面这些命令有风险，先不要随便执行：

```bash
docker system prune -a
rm -rf ~/qdrant_storage
docker volume prune
```

原因：

```text
docker system prune -a 可能删除未使用镜像、容器、缓存。
rm -rf ~/qdrant_storage 会删除 Qdrant 数据目录。
docker volume prune 可能删除没被容器使用的 volume。
```

学习阶段要养成习惯：

```text
先知道命令会删除什么，再执行删除命令。
```

## 为什么本节暂时不创建 collection

官方 quickstart 会继续创建 collection、添加向量、查询。

但我们这一节先停在：

```text
Qdrant 服务启动成功
Windows 能访问 Qdrant
```

原因是：

```text
1. 第 7 节刚学完数据模型，不急着上代码。
2. 第 8 节重点是服务部署和网络访问。
3. 第 13 节会正式生成 embedding 并写入 Qdrant。
4. 如果现在同时讲 Docker、网络、collection、upsert，会把重点搅乱。
```

所以本节验收标准是：

```text
能访问 http://UbuntuIP:6333
能访问 http://UbuntuIP:6333/dashboard
能看到 /collections 返回结果
```

这就够了。

## 本节你需要发给我的信息

你在 Ubuntu 执行完后，可以把这些输出发给我：

```bash
docker --version
docker ps --filter name=qdrant
curl http://localhost:6333
hostname -I
```

以及 Windows 访问结果：

```powershell
Invoke-RestMethod http://UbuntuIP:6333
```

如果你不确定哪些内容敏感，可以先发截图前问我。

一般这些输出不包含 API key。

## 本节练习

### 练习 1：解释镜像和容器

问题：

```text
docker pull qdrant/qdrant 和 docker run qdrant/qdrant 有什么区别？
```

参考答案：

```text
docker pull qdrant/qdrant 是下载 Qdrant 镜像，只是把运行模板下载到本机。
docker run qdrant/qdrant 是用这个镜像创建并启动一个容器，让 Qdrant 真正运行起来。
镜像不等于正在运行的服务，容器才是运行实例。
```

### 练习 2：解释端口映射

问题：

```text
-p 6333:6333 表示什么？
```

参考答案：

```text
它表示把 Ubuntu 主机的 6333 端口映射到 Qdrant 容器内部的 6333 端口。
这样 Windows 访问 UbuntuIP:6333 时，请求会进入容器里的 Qdrant REST API。
格式是 -p 主机端口:容器端口。
```

### 练习 3：解释数据持久化

问题：

```text
-v ~/qdrant_storage:/qdrant/storage 表示什么？
```

参考答案：

```text
它表示把 Ubuntu 主机的 ~/qdrant_storage 目录挂载到容器内部的 /qdrant/storage 目录。
Qdrant 在容器里写入 /qdrant/storage 的数据，会保存到 Ubuntu 主机的 ~/qdrant_storage。
这样删除容器后，只要这个主机目录还在，数据就不会因为容器删除而直接丢失。
```

### 练习 4：判断访问链路

问题：

```text
Windows 浏览器访问 http://192.168.1.50:6333 时，请求经过哪些地方？
```

参考答案：

```text
Windows 浏览器
-> VMware Ubuntu 虚拟机 IP 192.168.1.50
-> Ubuntu 主机 6333 端口
-> Docker 端口映射
-> Qdrant 容器内部 6333 端口
-> Qdrant REST API 返回响应
```

### 练习 5：排查问题

问题：

```text
Ubuntu 里 curl http://localhost:6333 能访问，但 Windows 访问 http://UbuntuIP:6333 不行，可能是什么原因？
```

参考答案：

```text
说明 Qdrant 容器大概率在 Ubuntu 内部运行正常。
问题更可能出在 Windows 到 Ubuntu 的网络链路上，例如 Ubuntu IP 选错、VMware 网络模式问题、Ubuntu 防火墙阻止 6333、Windows 与虚拟机不互通。
这时应检查 hostname -I、ping UbuntuIP、VMware 网络模式、sudo ufw status。
```

## 自测问题

### 自测 1：Qdrant 是 Python 包吗？

参考答案：

```text
不是。Qdrant 本身是独立运行的向量数据库服务。
Python 里的 qdrant-client 只是连接 Qdrant 服务的客户端库。
```

### 自测 2：为什么我们当前把 Qdrant 跑在 VMware Ubuntu 里？

参考答案：

```text
因为用户当前 Docker 已经在 VMware Ubuntu 中可用，主项目先放在 Windows。
这样可以避免现在额外折腾 Windows Docker Desktop，同时让 Windows ai-service 通过 Ubuntu IP 和 6333 端口访问 Qdrant。
```

### 自测 3：6333 和 6334 分别是什么？

参考答案：

```text
6333 是 Qdrant 的 HTTP REST API、健康检查和 Web UI 常用端口。
6334 是 Qdrant 的 gRPC API 端口。
当前学习阶段主要关注 6333。
```

### 自测 4：如果 docker ps 看不到 qdrant 容器，说明什么？

参考答案：

```text
可能容器没有启动，或者容器已退出，或者容器名称不是 qdrant。
可以用 docker ps -a 查看所有容器，用 docker logs qdrant 查看日志。
```

### 自测 5：删除容器一定会删除 Qdrant 数据吗？

参考答案：

```text
不一定。
如果使用 -v ~/qdrant_storage:/qdrant/storage 挂载了主机目录，删除容器通常不会自动删除 ~/qdrant_storage 里的数据。
但如果删除了这个挂载目录，数据就会丢失。
```

### 自测 6：Windows 以后连接 Qdrant 应该用 localhost 吗？

参考答案：

```text
如果 Qdrant 跑在 VMware Ubuntu 里，Windows 不能用 localhost 访问 Ubuntu 容器。
Windows 应该使用 http://Ubuntu虚拟机IP:6333。
localhost 在 Windows 上表示 Windows 本机，不表示 Ubuntu 虚拟机。
```

## 本节复盘

你现在要能讲清楚：

```text
1. Qdrant 是独立服务，不是 Python 项目里的普通包。
2. Docker 镜像是模板，容器是运行实例。
3. docker pull 是拉镜像，docker run 是启动容器。
4. -p 6333:6333 是端口映射。
5. -v ~/qdrant_storage:/qdrant/storage 是数据持久化。
6. Qdrant 跑在 Ubuntu Docker 里，Windows 通过 Ubuntu IP 访问。
7. 本节只验证服务启动，不创建 collection，不写入向量。
```

本节已经在 VMware Ubuntu 中完成实机验证。

下一节可以进入阶段 4 第 9 节：

```text
RAG 项目结构设计。
```

## 参考资料

- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quickstart/)
- [Qdrant Installation](https://qdrant.tech/documentation/installation/)
