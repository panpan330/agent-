# 阶段 4 第 32 节：本地 Docker 启动 Milvus Standalone

## 0. 本节状态

本节是 Milvus 实操入口。

当前状态：

```text
笔记和操作流程：已整理
VMware Ubuntu 实机启动：已验证
Windows 访问验证：已验证
```

本节已经在 VMware Ubuntu Docker 中完成实机启动验证。

验证结果：

```text
milvus-etcd：Up / healthy
milvus-minio：Up / healthy
milvus-standalone：Up / healthy
Milvus gRPC 端口：19530，Windows PowerShell 测试 TcpTestSucceeded=True
Milvus WebUI 端口：9091，Windows 浏览器已打开 WebUI
WebUI 状态：Your Cluster is running well
部署模式：STANDALONE
Milvus 版本：3.0-beta
```

本次实机排查中遇到一个真实问题：

```text
milvus-standalone Exited (134)
```

日志根因是：

```text
failed to mkdir
localStoragePath=/var/lib/milvus/data/
error="mkdir /var/lib/milvus/data/: permission denied"
```

也就是 Milvus 主容器要创建数据目录，但挂载出来的本地目录权限不允许写入。检查发现：

```text
volumes        root root
volumes/milvus root root
```

学习环境中用下面命令修复后，Milvus 主容器启动成功：

```bash
cd ~/milvus-standalone
sudo chmod -R 777 volumes/milvus
docker compose up -d
docker compose ps
```

注意：`chmod 777` 是学习环境中为了快速跑通服务的简化做法。生产环境应使用更明确的用户、用户组和目录权限管理，不能随意放开写权限。

## 1. 本节定位

上一节我们学习了：

```text
Milvus 是什么
Qdrant 是什么
Qdrant 和 Milvus 的核心概念怎么对应
什么时候选 Qdrant
什么时候评估 Milvus
```

这一节开始进入 Milvus 实操。

但本节不做 RAG 入库，也不写 Python 连接 Milvus 的业务代码。

本节只解决一个底层问题：

```text
如何在 VMware Ubuntu 里的 Docker 中，把 Milvus Standalone 跑起来，并确认 Windows 能访问它。
```

这就像我们之前学 Qdrant 时，先要确认：

```text
Qdrant 容器真的在跑
Windows 能访问 http://192.168.88.10:6333
```

Milvus 也是一样。

先启动成功，再谈 collection、schema、field、entity、index 和 RAG 入库。

## 2. 本节学习目标

学完本节，你要能做到：

1. 解释 Docker 和 Docker Compose 的区别。
2. 解释为什么 Milvus Standalone 适合本地学习。
3. 知道 Milvus Standalone Docker Compose 会启动哪些容器。
4. 知道 Milvus、etcd、MinIO 分别负责什么。
5. 知道 Milvus 默认服务端口 `19530` 的用途。
6. 知道 Milvus WebUI 端口 `9091` 的用途。
7. 能在 Ubuntu 中下载官方 Docker Compose 文件。
8. 能使用 `docker compose up -d` 启动 Milvus。
9. 能使用 `docker compose ps`、`docker logs` 查看运行状态。
10. 能从 Windows 访问 Ubuntu 虚拟机里的 Milvus WebUI。
11. 能区分 `docker compose stop`、`start`、`down` 和删除 `volumes` 的区别。
12. 能根据错误现象做初步排查。

## 3. 本节不学什么

这一节先不学：

1. Milvus collection schema 设计。
2. Milvus Python SDK。
3. 用 `pymilvus` 写入文档。
4. 用 Milvus 做向量检索。
5. Milvus scalar filter。
6. Milvus index 参数调优。
7. Milvus Cluster。
8. Kubernetes 部署。
9. 生产环境高可用。

这些会放到后续课程。

本节目标很明确：

```text
先让 Milvus 在本地 Docker 里稳定跑起来。
```

## 4. 官方资料核对

本节参考了官方文档，查阅日期：2026-07-17。

### 4.1 Milvus 官方资料

- Milvus Docker Compose 安装: https://milvus.io/docs/install_standalone-docker-compose.md
- Milvus Docker 单容器安装: https://milvus.io/docs/install_standalone-docker.md
- Milvus 配置 Docker Compose: https://milvus.io/docs/configure-docker.md
- Milvus 文档首页: https://milvus.io/docs

### 4.2 Docker 官方资料

- Docker Compose: https://docs.docker.com/compose/
- `docker compose up`: https://docs.docker.com/reference/cli/docker/compose/up/
- `docker compose down`: https://docs.docker.com/reference/cli/docker/compose/down/

这些资料里最关键的点是：

1. Milvus 官方推荐可以用 Docker Compose 启动 Standalone。
2. 官方 Docker Compose 文件会启动 `milvus-standalone`、`milvus-minio`、`milvus-etcd`。
3. `milvus-standalone` 默认暴露 `19530`。
4. Milvus WebUI 可以通过 `9091` 访问。
5. `docker compose up -d` 是后台启动。
6. `docker compose down` 会停止并删除 Compose 创建的容器和网络，但不等于自动删除你绑定出来的数据目录。

## 5. 基础知识铺垫

### 5.1 为什么还要学习部署

你可能会问：

```text
我不是学 AI 应用开发吗，为什么要学 Docker 启动 Milvus？
```

因为 AI 应用工程不是只写 prompt。

一个 RAG 系统至少涉及：

1. Python AI 服务。
2. 大模型 API。
3. embedding 模型。
4. 向量数据库。
5. 文档存储。
6. 权限系统。
7. 日志和 trace。
8. 测试和评测。

如果你只会写 Python 调用 SDK，但不知道向量数据库怎么启动、端口在哪里、数据存在哪里、怎么查看日志，那你遇到问题时会非常被动。

工程上经常会遇到：

```text
代码没错，但服务没启动。
服务启动了，但端口没暴露。
端口暴露了，但 Windows 访问不到虚拟机。
容器起来了，但依赖容器不健康。
数据写进去了，但下次重启丢了。
```

所以这一节不是偏离主线，而是在补 AI 工程必须会的基础设施能力。

### 5.2 Docker 是什么

Docker 可以先理解成：

```text
把一个服务和它运行需要的环境打包起来，用容器方式运行。
```

没有 Docker 时，你安装一个服务可能要关心：

1. 操作系统版本。
2. 依赖库版本。
3. 配置文件路径。
4. 启动命令。
5. 数据目录。
6. 端口监听。
7. 服务之间依赖。

有 Docker 后，很多东西被封装进 image。

你只需要：

```text
拉取镜像
创建容器
映射端口
挂载数据目录
启动服务
```

### 5.3 image 和 container 的区别

Docker 里最容易混的是 image 和 container。

简单说：

```text
image 是模板。
container 是用模板跑起来的实例。
```

类比 Java：

```text
class 是类。
object 是对象。
```

类比 Docker：

```text
image 是镜像。
container 是容器。
```

例如：

```text
milvusdb/milvus:v3.0-beta
```

这是镜像。

当它被启动后，出现：

```text
milvus-standalone
```

这是容器。

### 5.4 为什么容器需要端口映射

容器内部有自己的网络环境。

Milvus 在容器里监听 `19530`，不代表你的 Windows 或 Ubuntu 主机一定能访问。

需要端口映射：

```text
宿主机端口 -> 容器端口
```

比如：

```text
0.0.0.0:19530 -> container:19530
```

含义是：

```text
Ubuntu 主机的 19530 端口转发到 Milvus 容器的 19530 端口。
```

这样 Windows 才可能通过：

```text
192.168.88.10:19530
```

访问 Ubuntu 里的 Milvus。

### 5.5 为什么需要数据目录

容器默认是可以删除重建的。

如果数据只存在容器内部，容器删了数据可能也就没了。

所以数据库类服务通常要把数据挂载到宿主机目录。

Milvus 官方 Docker Compose 默认会把数据映射到当前目录下的：

```text
volumes/
```

常见结构会类似：

```text
milvus-standalone/
  docker-compose.yml
  volumes/
    etcd/
    minio/
    milvus/
```

你要理解：

```text
docker-compose.yml 是启动说明书。
volumes/ 是数据目录。
```

如果你删除 `volumes/`，就等于删除 Milvus 本地保存的数据。

### 5.6 Docker Compose 是什么

Docker Compose 是用一个 YAML 文件管理多个容器的工具。

Docker 官方文档的核心意思是：

```text
Compose 用一个 YAML 配置文件定义服务、网络和卷，然后用一个命令创建和启动整套服务。
```

如果只启动一个简单服务，可以用：

```bash
docker run ...
```

但 Milvus Standalone 官方 Compose 方式不是一个容器，而是多个容器配合：

```text
milvus-standalone
milvus-etcd
milvus-minio
```

这时用 Docker Compose 更合适。

### 5.7 为什么 Milvus 需要多个容器

Milvus 本身是向量数据库，但它还需要一些底层能力。

在 Standalone Docker Compose 中，常见容器包括：

| 容器 | 作用 |
| --- | --- |
| `milvus-standalone` | Milvus 主服务，对外提供向量数据库能力 |
| `milvus-etcd` | 存储元数据，比如 collection/schema 等内部状态 |
| `milvus-minio` | 对象存储，保存数据文件、索引文件等 |

你现在不用深入 etcd 和 MinIO 的实现。

先记住：

```text
Milvus 主服务负责对外工作。
etcd 负责元数据。
MinIO 负责对象存储。
```

这也是 Milvus 比 Qdrant 启动看起来更重的原因之一。

### 5.8 etcd 是什么

etcd 是一个分布式键值存储系统。

在 Milvus 里，你可以先把它理解成：

```text
保存 Milvus 内部元数据的地方。
```

比如：

1. 有哪些 collection。
2. schema 信息。
3. 内部协调状态。
4. 一些系统级元信息。

你不用把 etcd 当成业务数据库。

你的 RAG 文档 chunk 不是直接写到 etcd 里。

### 5.9 MinIO 是什么

MinIO 是一个兼容 S3 的对象存储服务。

在 Milvus Standalone 里，它可以用于存储：

1. 向量数据相关文件。
2. 索引文件。
3. 其他持久化文件。

你可以先这样理解：

```text
etcd 更像存系统元数据。
MinIO 更像存大块数据文件。
Milvus 主服务负责协调查询和写入。
```

### 5.10 Standalone 是什么

Standalone 的意思是单机部署模式。

它不是说只有一个容器。

它的重点是：

```text
整体作为单机 Milvus 实例运行，不是分布式集群。
```

对于学习来说，Standalone 的好处是：

1. 比 Cluster 简单。
2. 可以在单台虚拟机里跑。
3. 足够学习 collection、schema、insert、search。
4. 不需要 Kubernetes。
5. 不需要理解复杂的分布式部署。

### 5.11 Cluster 是什么

Cluster 是集群部署模式。

它通常用于：

1. 更大数据量。
2. 更高并发。
3. 更高可用要求。
4. 多节点扩展。
5. 企业生产环境。

但是 Cluster 会引入更多组件和运维知识。

对你当前学习阶段来说，直接上 Cluster 会干扰主线。

所以我们按这个顺序：

```text
Standalone 跑通
-> 核心概念
-> 入库检索
-> filter 和 index
-> 再谈选型和生产差距
```

### 5.12 为什么不直接用 Milvus Lite

Milvus Lite 更轻，可以作为 Python 库在本地使用。

但我们这里选择 Docker Standalone，原因是：

1. 你已经有 VMware Ubuntu Docker 环境。
2. 后面更接近真实服务部署方式。
3. 可以练习端口、容器、数据目录、日志排查。
4. 更适合理解 Milvus 作为独立服务存在。
5. 后续和 `ai-service` 的服务访问方式更接近真实项目。

学习 AI 工程，不能只停留在“一个 Python 包在本地跑”。

你需要理解服务化部署。

### 5.13 为什么这节要强调 Windows 访问 Ubuntu

你的项目目录在 Windows：

```text
D:\wendang\java+python+ai
```

Docker 在 VMware Ubuntu：

```text
192.168.88.10
```

这意味着将来的访问链路是：

```text
Windows ai-service
-> Ubuntu 虚拟机 IP
-> Docker 端口映射
-> Milvus 容器
```

如果这条链路不通，即使 Milvus 在 Ubuntu 里启动了，Windows 项目也连不上。

所以本节验证要分两层：

1. Ubuntu 内部验证 Milvus 容器正常。
2. Windows 主机验证能访问 Ubuntu 暴露的端口。

## 6. 本节主题系统讲解

### 6.1 本节整体流程

完整流程是：

```text
打开 VMware Ubuntu
-> 确认 Docker 可用
-> 确认 Docker Compose 可用
-> 创建 Milvus 工作目录
-> 下载官方 docker-compose.yml
-> 启动 Milvus
-> 查看容器状态
-> 查看日志
-> Ubuntu 本机验证
-> Windows 访问验证
-> 记录启动结果
```

### 6.2 为什么要创建单独目录

不要随便在 `~` 目录直接下载 `docker-compose.yml`。

建议创建：

```bash
mkdir -p ~/milvus-standalone
cd ~/milvus-standalone
```

原因：

1. `docker-compose.yml` 和 `volumes/` 放在一起，方便管理。
2. 不会和其他 Docker 服务混在一起。
3. 以后删除或迁移更清楚。
4. 日后排查时容易定位。

你可以把这个目录理解成：

```text
Milvus 本地部署目录
```

### 6.3 为什么下载官方 Compose 文件

官方文档给出的命令是下载 release 里的 Compose 文件。

当前官方文档示例是：

```bash
wget https://github.com/milvus-io/milvus/releases/download/v3.0-beta/milvus-standalone-docker-compose.yml -O docker-compose.yml
```

为什么不自己手写？

因为 Milvus 的组件、镜像、健康检查、依赖关系和环境变量会随版本变化。

学习阶段更稳妥的做法是：

```text
使用官方当前版本的 Compose 文件。
```

等你理解清楚以后，再学习如何修改配置。

### 6.4 为什么不用旧的 `docker-compose`

旧命令是：

```bash
docker-compose
```

新命令是：

```bash
docker compose
```

中间没有连字符。

官方文档也提醒，如果系统还是 Docker Compose V1，建议迁移到 V2。

你现在先检查：

```bash
docker compose version
```

如果能输出版本，说明 V2 可用。

### 6.5 `docker compose up -d` 是什么

命令：

```bash
docker compose up -d
```

逐个拆开：

| 部分 | 含义 |
| --- | --- |
| `docker` | Docker 命令行 |
| `compose` | 使用 Docker Compose |
| `up` | 创建并启动 Compose 文件里的服务 |
| `-d` | detached，后台运行 |

不用 `-d` 会怎样？

服务日志会一直占着当前终端。

学习数据库服务时，一般希望服务在后台跑，所以用：

```bash
docker compose up -d
```

### 6.6 `docker compose ps` 看什么

启动后用：

```bash
docker compose ps
```

你要看：

1. 是否有 `milvus-standalone`。
2. 是否有 `milvus-minio`。
3. 是否有 `milvus-etcd`。
4. 状态是否是 `Up`。
5. 有没有 `healthy`。
6. 端口是否映射出来。

不要只看命令没有报错。

真正要看容器状态。

### 6.7 `docker logs` 看什么

如果容器状态异常，用：

```bash
docker logs milvus-standalone --tail 100
```

这会显示 `milvus-standalone` 最近 100 行日志。

你要重点看：

1. 是否有 error。
2. 是否连接不上 etcd。
3. 是否连接不上 MinIO。
4. 是否端口被占用。
5. 是否权限不足。
6. 是否镜像拉取失败。

### 6.8 为什么不能用 `curl http://localhost:19530`

Qdrant 的 `6333` 是 HTTP API，所以你可以：

```bash
curl http://localhost:6333
```

Milvus 的 `19530` 主要是客户端连接端口，常用于 gRPC/SDK 连接。

所以不要期待：

```bash
curl http://localhost:19530
```

能像 Qdrant 一样返回 JSON。

Milvus 更适合用：

1. WebUI 验证 `9091`。
2. `docker compose ps` 看端口和健康状态。
3. 后续用 Python SDK 验证 `19530`。
4. Windows 用 `Test-NetConnection` 测端口可达性。

### 6.9 Milvus WebUI 是什么

官方文档说可以访问：

```text
http://127.0.0.1:9091/webui/
```

在 Ubuntu 虚拟机内部，这个地址是：

```text
http://localhost:9091/webui/
```

在 Windows 访问 VMware Ubuntu，就要换成虚拟机 IP：

```text
http://192.168.88.10:9091/webui/
```

前提是：

1. 虚拟机 IP 仍然是 `192.168.88.10`。
2. Ubuntu 防火墙没拦截。
3. Docker 端口映射到了 `0.0.0.0:9091`。
4. Windows 和虚拟机网络互通。

### 6.10 为什么要记录 `hostname -I`

虚拟机 IP 可能变化。

你上次看到的是：

```text
192.168.88.10
```

但下次 VMware 重启后，不一定永远一样。

所以每次需要 Windows 访问 Ubuntu 服务时，都建议在 Ubuntu 执行：

```bash
hostname -I
```

看第一个局域网 IP。

如果变成：

```text
192.168.88.11
```

那 Windows 访问地址也要换成：

```text
http://192.168.88.11:9091/webui/
```

### 6.11 Docker Compose 的停止方式

有几种常用命令。

#### 6.11.1 暂停服务

```bash
docker compose stop
```

含义：

```text
停止容器，但不删除容器。
```

下次可以：

```bash
docker compose start
```

重新启动。

#### 6.11.2 删除容器和网络

```bash
docker compose down
```

含义：

```text
停止并删除 Compose 创建的容器和网络。
```

但如果数据目录是本地 `volumes/` 这种绑定目录，它通常还在。

#### 6.11.3 删除数据

官方文档里删除数据是：

```bash
rm -rf volumes
```

这一步要非常小心。

它的含义是：

```text
删除 Milvus 本地数据目录。
```

学习阶段如果只是想停掉服务，不要执行这一步。

### 6.12 本节不要和 Qdrant 混在一个目录

你已经有 Qdrant 容器。

Milvus 不要放到 Qdrant 的目录里。

建议：

```text
~/qdrant-data 或 Qdrant 原目录
~/milvus-standalone
```

原因：

1. 数据目录分开。
2. Compose 文件分开。
3. 日后删除不误伤。
4. 端口和服务状态更清晰。

### 6.13 Milvus 和 Qdrant 端口不冲突

你之前 Qdrant 用：

```text
6333
6334
```

Milvus 常用：

```text
19530
9091
```

它们默认不冲突。

但要注意：

```text
如果 9091 被别的服务占用，Milvus WebUI 可能起不来或端口映射失败。
```

这时用：

```bash
docker compose ps
```

和：

```bash
docker logs milvus-standalone --tail 100
```

排查。

## 7. 实机操作步骤

下面命令在 VMware Ubuntu 里执行，不是在 Windows PowerShell 里执行。

### 7.1 打开 VMware Ubuntu

先打开你的 VMware Ubuntu。

登录后确认终端提示符类似：

```text
panpan@panpan-VMware-Virtual-Platform:~$
```

### 7.2 确认 Docker 可用

执行：

```bash
docker --version
```

期望看到类似：

```text
Docker version 29.1.4, build ...
```

你的版本不一定完全一样，重点是能正常输出。

### 7.3 确认 Docker Compose 可用

执行：

```bash
docker compose version
```

期望看到类似：

```text
Docker Compose version v2.x.x
```

如果提示：

```text
docker: 'compose' is not a docker command
```

说明 Docker Compose V2 不可用，需要先安装或修复 Compose。

### 7.4 创建 Milvus 目录

执行：

```bash
mkdir -p ~/milvus-standalone
cd ~/milvus-standalone
```

确认当前目录：

```bash
pwd
```

期望：

```text
/home/panpan/milvus-standalone
```

如果你的用户名不是 `panpan`，路径会不一样，这是正常的。

### 7.5 下载官方 Docker Compose 文件

执行：

```bash
wget https://github.com/milvus-io/milvus/releases/download/v3.0-beta/milvus-standalone-docker-compose.yml -O docker-compose.yml
```

如果 `wget` 不存在，可以先安装：

```bash
sudo apt update
sudo apt install -y wget
```

下载后确认文件存在：

```bash
ls -lh docker-compose.yml
```

### 7.6 查看 Compose 文件里的服务名

执行：

```bash
grep -E "container_name:|image:|ports:" -n docker-compose.yml
```

你会看到和容器名、镜像、端口相关的信息。

这一步不是必须，但很适合学习。

它可以让你知道：

```text
这个 Compose 文件到底要启动什么。
```

### 7.7 启动 Milvus

执行：

```bash
docker compose up -d
```

如果你当前用户没有 Docker 权限，可能要用：

```bash
sudo docker compose up -d
```

如果开始拉取镜像，这一步可能比较慢。

等待它完成。

### 7.8 查看容器状态

执行：

```bash
docker compose ps
```

或者：

```bash
docker ps --filter name=milvus
```

你希望看到至少这些容器：

```text
milvus-standalone
milvus-minio
milvus-etcd
```

状态应该是：

```text
Up
```

部分容器可能有：

```text
healthy
```

### 7.9 查看 Milvus 日志

执行：

```bash
docker logs milvus-standalone --tail 100
```

如果容器名不同，以你的 `docker ps` 输出为准。

不要看到几行英文日志就慌。

重点看有没有明显的：

```text
error
failed
panic
connection refused
address already in use
permission denied
```

### 7.10 Ubuntu 内部访问 WebUI

在 Ubuntu 里可以执行：

```bash
curl -I http://localhost:9091/webui/
```

如果有 HTTP 响应，说明 WebUI 端口有服务。

也可以在 Ubuntu 浏览器里打开：

```text
http://localhost:9091/webui/
```

如果 Ubuntu 没有桌面浏览器，没关系，重点是后面从 Windows 浏览器访问。

### 7.11 查看 Ubuntu IP

执行：

```bash
hostname -I
```

你之前看到的是：

```text
192.168.88.10 172.17.0.1
```

这里通常要选第一个局域网地址：

```text
192.168.88.10
```

`172.17.0.1` 通常是 Docker 内部网桥地址，不是 Windows 访问 Ubuntu 的首选地址。

### 7.12 Windows 访问 WebUI

在 Windows 浏览器打开：

```text
http://192.168.88.10:9091/webui/
```

如果你的 `hostname -I` 显示不是 `192.168.88.10`，就替换成实际 IP。

例如：

```text
http://192.168.88.11:9091/webui/
```

### 7.13 Windows 测试端口

在 Windows PowerShell 里执行：

```powershell
Test-NetConnection 192.168.88.10 -Port 19530
```

如果通，通常会看到：

```text
TcpTestSucceeded : True
```

再测 WebUI：

```powershell
Test-NetConnection 192.168.88.10 -Port 9091
```

也希望是：

```text
TcpTestSucceeded : True
```

### 7.14 注意 PowerShell 的 curl

在 Windows PowerShell 里，`curl` 可能是 `Invoke-WebRequest` 的别名。

之前你已经遇到过安全提示。

所以 Windows 里建议用：

```powershell
curl.exe http://192.168.88.10:9091/webui/
```

或者直接用浏览器访问。

## 8. 本节推荐执行顺序汇总

下面这组命令在 Ubuntu 执行。

```bash
docker --version
docker compose version

mkdir -p ~/milvus-standalone
cd ~/milvus-standalone

wget https://github.com/milvus-io/milvus/releases/download/v3.0-beta/milvus-standalone-docker-compose.yml -O docker-compose.yml

ls -lh docker-compose.yml
grep -E "container_name:|image:|ports:" -n docker-compose.yml

docker compose up -d
docker compose ps
docker logs milvus-standalone --tail 100

hostname -I
```

下面这组命令在 Windows PowerShell 执行。

```powershell
Test-NetConnection 192.168.88.10 -Port 19530
Test-NetConnection 192.168.88.10 -Port 9091
```

Windows 浏览器打开：

```text
http://192.168.88.10:9091/webui/
```

把 `192.168.88.10` 换成你自己的 `hostname -I` 结果。

## 9. 如何判断启动成功

### 9.1 Ubuntu 里成功的标志

至少满足：

1. `docker compose ps` 能看到 `milvus-standalone`。
2. `milvus-standalone` 状态是 `Up`。
3. 能看到 `milvus-etcd` 和 `milvus-minio`。
4. `docker logs milvus-standalone --tail 100` 没有持续报错。
5. `9091` 端口可访问。

### 9.2 Windows 里成功的标志

至少满足：

1. `Test-NetConnection <Ubuntu IP> -Port 19530` 成功。
2. `Test-NetConnection <Ubuntu IP> -Port 9091` 成功。
3. 浏览器能打开 `http://<Ubuntu IP>:9091/webui/`。

### 9.3 暂时不要求什么

本节暂时不要求：

1. Python SDK 连接成功。
2. 创建 collection。
3. 插入 vector。
4. 搜索 vector。
5. 接入 `ai-service`。

这些放到后面。

## 10. 常见问题和排查

### 10.1 镜像拉取很慢

现象：

```text
docker compose up -d
```

卡在 pulling image。

原因可能是：

1. 网络慢。
2. Docker Hub 或镜像源访问慢。
3. GitHub 访问慢。
4. 虚拟机网络不稳定。

处理思路：

1. 先确认网络：

```bash
ping -c 4 github.com
ping -c 4 docker.com
```

2. 多等一会儿。
3. 重新执行：

```bash
docker compose pull
docker compose up -d
```

4. 如果长期很慢，再考虑 Docker 镜像加速或手动拉取。

### 10.2 `docker compose` 不存在

现象：

```text
docker: 'compose' is not a docker command
```

说明 Compose V2 没有安装或不可用。

先执行：

```bash
docker --version
docker compose version
docker-compose --version
```

把输出发给我。

不要自己乱装一堆版本。

### 10.3 权限不足

现象：

```text
permission denied while trying to connect to the Docker daemon socket
```

原因：

当前用户没有权限访问 Docker daemon。

临时解决：

```bash
sudo docker compose up -d
sudo docker compose ps
```

长期解决通常是把用户加入 docker 组，但这需要谨慎操作。你如果遇到这个问题，把输出贴给我，我再一步一步带你做。

### 10.4 端口被占用

现象可能包含：

```text
address already in use
```

排查：

```bash
sudo ss -lntp | grep -E "19530|9091"
```

如果某个端口已经被占用，需要看是谁占用。

不要直接杀进程。

先把输出发给我。

### 10.5 容器一直 Restarting

查看：

```bash
docker ps -a --filter name=milvus
docker logs milvus-standalone --tail 200
```

重点看：

1. 配置错误。
2. 依赖服务没起来。
3. 文件权限。
4. 内存不足。
5. 镜像版本问题。

### 10.6 Windows 访问不到 Ubuntu

如果 Ubuntu 里服务正常，但 Windows 打不开：

```text
http://192.168.88.10:9091/webui/
```

排查顺序：

1. Ubuntu 里重新执行：

```bash
hostname -I
```

确认 IP 没变。

2. Windows PowerShell：

```powershell
ping 192.168.88.10
```

3. Windows PowerShell：

```powershell
Test-NetConnection 192.168.88.10 -Port 9091
```

4. Ubuntu 查看端口：

```bash
docker compose ps
sudo ss -lntp | grep 9091
```

5. 检查 VMware 网络模式。

你之前 Qdrant 已经能从 Windows 访问，说明这条链路原则上可行。

### 10.7 WebUI 打不开但 19530 通

这说明 Milvus 主连接端口可能通，但 WebUI 端口有问题。

排查：

```bash
docker compose ps
docker logs milvus-standalone --tail 100
sudo ss -lntp | grep 9091
```

后续 Python SDK 可能仍然能连 `19530`，但本节我们还是希望 WebUI 能打开，方便学习观察。

### 10.8 `curl http://localhost:19530` 没有正常返回

这不一定是问题。

因为 `19530` 不是 Qdrant 那种普通 HTTP 根路径。

你应该用：

```bash
docker compose ps
curl -I http://localhost:9091/webui/
```

或后续用 Python SDK 连接。

## 11. 停止、启动、删除的正确方式

### 11.1 临时停止

在 `~/milvus-standalone` 目录执行：

```bash
docker compose stop
```

下次启动：

```bash
docker compose start
```

适合：

```text
今天不用了，但以后还要继续用。
```

### 11.2 关闭并删除容器

```bash
docker compose down
```

适合：

```text
想清理容器和网络，但保留本地数据目录。
```

下次再启动：

```bash
docker compose up -d
```

### 11.3 删除数据

非常谨慎执行：

```bash
rm -rf volumes
```

含义：

```text
删除 Milvus 保存的数据。
```

学习阶段，如果你只是想关掉虚拟机，不需要删数据。

### 11.4 关闭虚拟机前建议怎么做

如果 Milvus 还在运行，建议先：

```bash
cd ~/milvus-standalone
docker compose stop
```

然后再关虚拟机。

下次打开虚拟机后：

```bash
cd ~/milvus-standalone
docker compose start
```

这样比直接断电更清晰。

## 12. 本节和 Qdrant 的对比

### 12.1 Qdrant 启动更简单

之前 Qdrant 通常一个容器就能跑：

```text
qdrant/qdrant
```

端口：

```text
6333
6334
```

访问：

```text
http://192.168.88.10:6333
```

能直接返回 JSON。

### 12.2 Milvus 启动更像一组服务

Milvus Docker Compose 会启动多个容器：

```text
milvus-standalone
milvus-etcd
milvus-minio
```

访问方式：

```text
19530 给 SDK/客户端连接
9091 给 WebUI/健康观察
```

这就是你体感上会觉得 Milvus 更重的原因。

### 12.3 这说明什么

这说明工具选型不只是 API。

还包括：

1. 部署复杂度。
2. 运维复杂度。
3. 数据目录管理。
4. 依赖组件。
5. 端口规划。
6. 日志排查。
7. 备份恢复。

你以后跟别人讲 Qdrant vs Milvus 时，不能只讲 collection 和 vector，也要讲部署和运维体验。

## 13. 本节执行记录模板

你实机执行后，可以按这个模板发给我。

```text
1. docker --version 输出：

2. docker compose version 输出：

3. docker compose ps 输出：

4. docker logs milvus-standalone --tail 100 里是否有 error：

5. hostname -I 输出：

6. Windows Test-NetConnection 19530 结果：

7. Windows Test-NetConnection 9091 结果：

8. 浏览器能否打开 http://<Ubuntu IP>:9091/webui/：
```

我会根据这些输出判断：

```text
Milvus 是否启动成功
Windows 是否能访问
是否可以进入第 33 节
```

### 13.1 本机验证记录

本节实机验证记录如下。

Ubuntu 容器状态：

```text
milvus-etcd         Up / healthy
milvus-minio        Up / healthy
milvus-standalone   Up / healthy
```

Milvus 主容器端口映射：

```text
0.0.0.0:19530->19530/tcp
0.0.0.0:9091->9091/tcp
```

Windows PowerShell 验证：

```text
Test-NetConnection 192.168.88.10 -Port 19530
TcpTestSucceeded : True
```

Windows 浏览器验证：

```text
http://192.168.88.10:9091/webui/
WebUI 可打开
Your Cluster is running well
```

本次有一个小错误也要记住：

```text
Test-NetConnection 192.168.88.10 -Port 909
```

这条命令测的是 `909`，不是 Milvus WebUI 的 `9091`，所以失败是正常的。正确端口是：

```powershell
Test-NetConnection 192.168.88.10 -Port 9091
```

不过浏览器已经打开 `9091` 的 WebUI，因此 WebUI 访问链路已经验证通过。

## 14. 本节练习

### 练习 1：概念解释

请用自己的话解释：

```text
Docker image 和 Docker container 的区别是什么？
```

### 练习 2：Compose 理解

为什么 Milvus Standalone 推荐用 Docker Compose，而不是只用一个简单的 `docker run` 命令？

### 练习 3：组件职责

请说明下面三个容器的大致职责：

| 容器 | 职责 |
| --- | --- |
| `milvus-standalone` | ? |
| `milvus-etcd` | ? |
| `milvus-minio` | ? |

### 练习 4：端口判断

请回答：

1. `19530` 主要用于什么？
2. `9091` 主要用于什么？
3. 为什么不要用 `curl http://localhost:19530` 判断 Milvus 是否像 Qdrant 一样正常？

### 练习 5：停止和删除

请解释下面命令的区别：

```bash
docker compose stop
docker compose start
docker compose down
rm -rf volumes
```

### 练习 6：Windows 访问

如果 Ubuntu 执行 `hostname -I` 输出：

```text
192.168.88.15 172.17.0.1
```

那么 Windows 浏览器应该访问哪个 Milvus WebUI 地址？

## 15. 练习参考答案

### 练习 1 参考答案

image 是镜像，相当于服务运行环境的模板；container 是容器，是用镜像真正跑起来的实例。一个 image 可以创建多个 container。

### 练习 2 参考答案

因为 Milvus Standalone Docker Compose 方式不只是启动 Milvus 主服务，还会同时启动 etcd、MinIO 等依赖服务。Docker Compose 可以用一个 `docker-compose.yml` 管理多个服务、网络、端口和数据目录，比手写多个 `docker run` 命令更清晰。

### 练习 3 参考答案

| 容器 | 职责 |
| --- | --- |
| `milvus-standalone` | Milvus 主服务，对外提供向量数据库能力 |
| `milvus-etcd` | 保存 Milvus 内部元数据和协调状态 |
| `milvus-minio` | 对象存储，用于保存数据文件、索引文件等 |

### 练习 4 参考答案

1. `19530` 主要用于 Milvus 客户端和 SDK 连接。
2. `9091` 主要用于 Milvus WebUI 和健康观察。
3. 因为 `19530` 不是 Qdrant `6333` 那样的普通 HTTP 根路径，不能期待它用 `curl` 返回 JSON。判断 Milvus 要看容器状态、WebUI、日志，以及后续用 SDK 连接。

### 练习 5 参考答案

| 命令 | 含义 |
| --- | --- |
| `docker compose stop` | 停止容器，但保留容器 |
| `docker compose start` | 启动已经存在的容器 |
| `docker compose down` | 停止并删除 Compose 创建的容器和网络 |
| `rm -rf volumes` | 删除本地数据目录，可能清空 Milvus 数据 |

### 练习 6 参考答案

应该访问：

```text
http://192.168.88.15:9091/webui/
```

不要用 `172.17.0.1`，它通常是 Docker 内部网桥地址，不是 Windows 访问 Ubuntu 虚拟机的首选地址。

## 16. 自测题

### 自测 1

本节为什么选择 Milvus Standalone，而不是 Milvus Cluster？

### 自测 2

Docker Compose 文件通常负责描述哪些内容？

### 自测 3

为什么数据库类容器要挂载数据目录？

### 自测 4

Milvus Standalone Docker Compose 常见会启动哪三个容器？

### 自测 5

如果 `docker compose up -d` 之后没有报错，是否一定代表 Milvus 完全正常？为什么？

### 自测 6

Windows 访问 Ubuntu 里的 Milvus 时，为什么要先执行 `hostname -I`？

### 自测 7

为什么 `docker compose down` 和 `rm -rf volumes` 不是一回事？

### 自测 8

如果 Windows 访问不到 `http://192.168.88.10:9091/webui/`，你会按什么顺序排查？

### 自测 9

Milvus 的 `19530` 和 Qdrant 的 `6333` 在访问方式上有什么差异？

### 自测 10

为什么本节不直接写 Python 连接 Milvus？

## 17. 自测题参考答案

### 自测 1 参考答案

因为当前是本地学习阶段，重点是先理解 Milvus 的基本启动、端口、容器和访问方式。Cluster 涉及更多节点、组件和运维知识，会让学习重点偏离 RAG 主线。

### 自测 2 参考答案

Docker Compose 文件通常描述服务、镜像、容器名、端口映射、环境变量、数据卷、网络和服务依赖等内容。

### 自测 3 参考答案

因为容器可以删除重建，如果数据只在容器内部，容器删除后数据可能丢失。挂载数据目录可以把数据库数据保存到宿主机目录，便于重启和后续管理。

### 自测 4 参考答案

常见是：

1. `milvus-standalone`
2. `milvus-etcd`
3. `milvus-minio`

### 自测 5 参考答案

不一定。命令没有报错只说明 Compose 启动流程提交了，还要用 `docker compose ps` 看容器是否 Up/healthy，用 `docker logs` 看是否持续报错，并从 Ubuntu 和 Windows 验证端口是否能访问。

### 自测 6 参考答案

因为 VMware Ubuntu 的 IP 可能变化。Windows 要访问 Ubuntu 里的服务，需要用当前真实 IP，而不是一直假设还是以前的 `192.168.88.10`。

### 自测 7 参考答案

`docker compose down` 停止并删除 Compose 创建的容器和网络，但本地绑定的数据目录可能还在；`rm -rf volumes` 是删除 Milvus 数据目录，会清掉本地保存的数据。

### 自测 8 参考答案

可以按这个顺序：

1. Ubuntu 执行 `hostname -I` 确认 IP。
2. Ubuntu 执行 `docker compose ps` 看容器状态。
3. Ubuntu 执行 `docker logs milvus-standalone --tail 100` 看日志。
4. Ubuntu 执行 `sudo ss -lntp | grep 9091` 看端口监听。
5. Windows 执行 `ping <Ubuntu IP>`。
6. Windows 执行 `Test-NetConnection <Ubuntu IP> -Port 9091`。
7. 检查 VMware 网络模式或防火墙。

### 自测 9 参考答案

Qdrant 的 `6333` 是 HTTP API，直接 `curl http://host:6333` 通常能看到 JSON；Milvus 的 `19530` 主要用于客户端/SDK 连接，不适合用普通 `curl` 判断是否像 HTTP 服务一样返回 JSON。

### 自测 10 参考答案

因为本节目标是先确认 Milvus 服务本身启动成功。如果服务没启动或 Windows 连不到端口，直接写 Python 连接代码会把问题混在一起。后面第 33-34 节会再进入 Milvus 概念和 Python 写入检索。

## 18. 本节总结

本节最重要的不是背命令，而是理解本地 Milvus 的运行结构。

你现在应该知道：

1. Milvus Standalone 适合本地学习。
2. Docker 是运行容器的工具。
3. Docker Compose 用一个 YAML 文件管理多个容器。
4. Milvus Standalone Compose 通常会启动 Milvus、etcd、MinIO。
5. `19530` 是 Milvus 客户端连接端口。
6. `9091` 可以用来访问 Milvus WebUI。
7. `volumes/` 是数据目录，不能随便删。
8. Windows 访问 VMware Ubuntu 服务时要用 Ubuntu 当前 IP。
9. 启动成功要看容器状态、日志、端口和 Windows 访问结果。
10. 本节不写 Python 连接代码，是为了先把基础设施问题单独讲清楚。

一句话总结：

```text
Milvus 不是一个 Python 函数，而是一个独立运行的向量数据库服务；你要先让服务稳定跑起来，才能在后续课程里用 Python 和 RAG 项目连接它。
```

## 19. 下一节预告

第 33 节会学习：

```text
Milvus 核心概念：collection、schema、field、entity、index
```

本节实机验证已经完成，可以进入第 33 节。

如果你把以下输出贴给我，我就能判断是否可以继续：

```text
docker compose ps
hostname -I
Windows Test-NetConnection 19530
Windows Test-NetConnection 9091
浏览器能否打开 http://<Ubuntu IP>:9091/webui/
```
