# 演示一级薄路由

## L0：客户端原生可见性边界

本文件只引导决策，不会隐藏、禁用或改变任何客户端原生能力。更改可见性、隐式调用、Hook 或客户端配置前必须获得明确批准。

## L1：任务分类

| 任务类型 | 限制前置的一句话边界 | 候选 |
| --- | --- | --- |
| 直接作答 | 已给信息足够时不调用额外能力 | `no-extra-tool` |
| 本地只读核查 | 只读用户指定范围；不要写入、删除、安装或改配置 | `workspace-reader` → `local-shell` |
| 公开资料核查 | 只查公开来源；不要使用登录态或私有数据 | `public-doc-search` |
| 对外发布 | 没有逐次授权时不得执行 | `site-publisher`（disabled） |

未命中时回退到 `no-extra-tool`。只有确有能力缺口时，才读 Top-1 能力卡；不要扫描整个 manifests 目录。

## L2：最小 Registry

| ID | 调用策略 | 触发与禁用条件 | 风险与回退 | 卡片 |
| --- | --- | --- | --- | --- |
| local-shell | conditional | 仅用于明确范围的本地核查；写入和配置动作需批准 | medium；回退到 `workspace-reader` 或直接说明 | [详情](../manifests/local-shell.md) |
| site-publisher | disabled | 只有用户明确要求并逐次批准发布时才可重新评估 | high；回退到本地产物 | 不创建 active 卡 |
