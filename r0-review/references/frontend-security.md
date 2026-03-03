# Frontend Security Checklist

适用场景：Web 前端（React/Vue/Next.js 等）。

## 输入与渲染
- 默认禁止拼接 HTML 字符串；必须确认是否存在 XSS 注入点。
- 审查 `dangerouslySetInnerHTML`、`innerHTML`、模板插值中的未转义输入。
- URL 参数、富文本、第三方返回内容必须经过白名单或可信清洗。

## 鉴权与会话
- Token 存储策略是否合理（优先 HttpOnly Cookie；谨慎 localStorage）。
- 是否存在把 access token 输出到日志、埋点、错误上报。
- 退出登录是否真正清理会话状态与缓存。

## 请求安全
- 关键写操作是否具备 CSRF 防护。
- CORS 配置是否最小化，避免 `*` 放开敏感域。
- 重定向目标是否做白名单校验，避免开放重定向。

## 前端依赖与构建
- 是否引入高危第三方脚本或无版本锁定资源。
- Source map 是否在生产暴露敏感实现与路径信息。
- 环境变量是否误暴露服务端密钥。
