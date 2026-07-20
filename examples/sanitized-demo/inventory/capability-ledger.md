# 演示能力账本

输入标识：`demo-environment-v1`

| ID | 能力槽 | 管理状态 | 健康状态 | 风险 | 授权级别 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| no-extra-tool | 不调用额外能力直接回答 | active | healthy | low | ordinary | 模型当前可用 |
| workspace-reader | 读取指定工作区并返回证据 | active | healthy | low | ordinary | 演示输入声明本轮读取成功 |
| local-shell | 运行本地只读检查并返回结果 | conditional | unverified | medium | ordinary / write-gated | 只有能力声明，没有本轮命令证据 |
| public-doc-search | 查询公开文档并返回来源 | cold | unverified | low | ordinary | 本轮未调用 |
| site-publisher | 把内容发布到外部网站 | disabled | unverified | high | publish-gated | 未启用、未授权 |

幂等规则：再次处理 `demo-environment-v1` 时按 ID 更新以上行，不新增同名或同义重复项。
