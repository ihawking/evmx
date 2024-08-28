# EVMx
教程文档编写中。。。。。。建议待本项目完善文档后，再进行生产环境部署！

基于EVM区块链的加密货币结算系统.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: GPLv3

## 项目简介

**EVMx**
是一个基于EVM区块链开发的加密货币结算系统。目的是解决传统中心化系统的资产上链问题，集成了支付、充币、提币等核心功能。  
适合任何需要对接加密货币到系统中的项目，都可以使用本项目作为与区块链资产互通的网关。  
本项目已在多款**链游**与**链改**项目中集成。

## 核心功能

1、💳 加密货币**支付网关**  
2、💰 加密货币**充值网关**  
3、🏧 加密货币**提币系统**  
4、🖥️ 完备的**后台管理**功能  
5、👥 **多租户系统**

## 支持网络

Ethereum、BSC、Polygon等基于EVM架构的区块链。

## 支持币种

1、ETH、BNB、MATIC等各个公链主币  
2、USDT、USDC、UNI等任意ERC20代币，支持自定义发行的代币

## 后续功能开发

1、智能合约事件订阅  
2、离线签名提币  
3、NFT资产数据同步  
...

## 环境配置要求

1、2核4G主机起步，添加的公链越多，配置要求越高  
2、Docker、Docker compose  
3、HTTPS 格式的区块链RPC接口，监听服务需要高频访问此接口

## 启动项目
1、克隆代码仓库到本地  
`git clone https://github.com/ihawking/evmx.git`  
2、进入代码库  
`cd evmx`  
3、启动项目  
`docker compose up -d --build`  

项目启动成功后服务地址：http://0.0.0.0:9527

## 版本更新
1、进入项目根目录  
`cd evmx`  
2、停止项目  
`docker compose down`  
3、更新代码库  
`git pull`  
4、启动项目  
`docker compose up -d --build`


### 功能原理概述

- 项目主要包含Postgres、Redis、Web、区块链监听、定时任务五个子系统，均由docker compose统一管理。
- 本项目持续监听区块链的所有爆块与交易（因此对主机配置要求较高）。
- 解析每一笔交易，判断是否是系统内交易，如果是则入库处理。
- 处理完交易，生成对应通知，发送到回调接口。


