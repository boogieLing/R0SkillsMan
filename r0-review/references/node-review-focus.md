# Node.js Review Focus

## 异步与错误传播
- Promise 链是否遗漏 `catch`，是否可能产生 unhandled rejection。
- `async/await` 是否在边界层统一捕获并映射错误码。
- 是否存在回调与 Promise 混用导致的双重回调风险。

## 安全与输入
- 输入校验是否覆盖 body/query/path/header。
- 模板渲染、HTML 拼接、反序列化是否可被注入。
- 第三方包是否有高危 API（如 `eval`、动态 `require`）。

## 运行时稳定性
- 长耗时任务是否阻塞事件循环。
- 流与文件句柄是否正确关闭。
- 重试与限流是否避免雪崩。

## 可维护性
- 控制器是否过重（解析 + 业务 + IO + 编排）。
- 错误日志是否可关联请求上下文。
