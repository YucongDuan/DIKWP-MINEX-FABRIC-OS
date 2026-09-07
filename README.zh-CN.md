# DIKWP-MINEX-FABRIC-OS 1.0.0

**最小能耗与最小有效付出能力路由、功能内化、联邦借用和计量交换运行时**

系统不再要求每项任务都先打开某个 App，而是把软件、API、模型能力和远程节点统一表示为有权限边界的“能力”。面对一个明确目的，系统可以比较：模型原生完成、生成本地代码、本地 API、远程 API、浏览器、GUI/Computer Use、联邦节点和人工执行。

规划器先执行硬约束：授权、数据等级、质量、可靠性、语义损失、隐私、不可逆性、预算和期限。通过硬约束后才计算 Pareto 前沿，并按公开的字典序选择；默认第一目标是物理能耗最小。金钱、延迟、人工时间、隐私风险和语义损失不会被静默换算为焦耳。

## 已实现

- 能力清单、注册表与版本谱系；
- 约束优先、Pareto 保留的能力路由；
- 安全白名单参考函数的确定性执行；
- 模型原生、生成代码、API、浏览器、GUI、联邦节点和人工八种模式；
- 权限范围、数据等级、节点白名单、有限租约和调用额度；
- 带 Bearer 认证和签名租约的本地能力节点；
- 不移动真实资金的报价、预留和结算凭证；
- 经过许可确认和一致性测试的声明式功能内化；
- 追加式 SHA-256 证据账本和 DIKWP 记录；
- 不覆盖历史的运行结果校准；
- 12 个参考场景、66 项自动测试、双语离线驾驶舱和单文件程序。

## 明确禁止或未实现

- 绕过登录、MFA、SSO、操作系统、数据或软件权限；
- 任意 Shell 或不受限的模型生成代码执行；
- 抽取专有 API、模型权重、系统提示或商业秘密；
- 真实支付、托管、加密货币或资金保管；
- 自动外部行动权；
- 以一个总分用低能耗补偿错误、侵权或隐私损失。

## 快速运行

```bash
python dist/DIKWP_MINEX_FABRIC_OS.pyz inspect
python dist/DIKWP_MINEX_FABRIC_OS.pyz suite --root . --output outputs/my-suite
python dist/DIKWP_MINEX_FABRIC_OS.pyz run examples/tasks/01_csv_profile_direct_function.json \
  --capabilities examples/capabilities --output outputs/my-run
python dist/DIKWP_MINEX_FABRIC_OS.pyz verify outputs/my-run/evidence_ledger.jsonl
```

浏览器直接打开 `web/DIKWP_MINEX_FABRIC_OS_Dashboard.html` 即可查看离线双语驾驶舱。

## 来源边界

用户提供的背景文章被作为“模型、API、浏览器、命令行和 GUI 交互逐渐汇合”的情景输入。文章中的未来产品名称和基准数据不由本软件独立认证；本系统也不依赖任何特定厂商或模型名称。
## 可复现的本机联邦借用演示

```bash
python tools/run_federation_demo.py --output outputs/federation-demo/result.json
```

演示只打开临时本机回环端口，先获取能力清单和报价，再通过 Bearer 凭证及到期签名租约执行一次白名单哈希功能。

