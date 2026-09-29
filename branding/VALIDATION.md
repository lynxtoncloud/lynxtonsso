# 品牌主题验证记录

日期：2026-09-29。

## 范围与环境

- 定制基线：官方 Keycloak `b035515009c0b8826e532a186d4ca347475947b1`。
- 实际服务：2026-09-29 下载的官方 nightly，版本 `999.0.0-SNAPSHOT`，Quarkus `3.40.0.CR1`；不将 nightly 版本名当作源码提交号。
- 下载来源：`https://github.com/keycloak/keycloak/releases/download/nightly/keycloak-999.0.0-SNAPSHOT.tar.gz`。
- 运行方式：仅监听 `127.0.0.1`，独立开发数据库、合成测试用户和实际主题 JAR；未连接生产服务。
- 浏览器：本机 Chrome，通过 Playwright 检查；1440×1000 与 320×800。
- 主题 JAR SHA256：`a849e3e22585d3938853677dacdce266469555e4ff3baec60508529ddd50f3dc`。

## 已通过

- 中文登录页、英文切换、主站 Logo、品牌标题与页脚。
- 无效密码提示与真实账号登录成功。
- 注册页面、找回密码页面及上游密码显示/隐藏按钮。
- 键盘 Tab 顺序与可见焦点。
- 账户中心、管理控制台正常加载，未出现浏览器脚本或资源请求错误。
- 登录、注册、账户中心在 320px 无页面横向溢出；账户菜单改为两行，保留所有操作入口。
- 手机 OTP 设置页面和二维码可见且无横向溢出。
- 三类页面 favicon 请求成功，返回文件的 SHA256 与新的 ICO 完全一致。
- 账户与管理页 Logo 成功加载，图片尺寸与主站原图一致。
- 打包清单、全部主题源文件、生成的旧版简体语言别名逐字节核对通过，JAR CRC 无错误。
- `git diff --check` 通过。

## 验证边界

注册与找回密码仅验证页面和控件，未触发邮件投递；OTP 验证设置页面，未登记真实设备。本次不涉及飞书联邦、双身份域、生产部署或完整 Keycloak 发行构建。管理首页 Logo 替代文字的一行 JSX 修改已静态核对，须随源码前端构建发布；独立主题包不替换上游 JavaScript。

Keycloak 26.3.2 额外检查了中文登录、错误、注册与管理主题；生成的 `zh_CN` 兼容语言文件使其能读取同一份中文文案，不据此声明所有旧版本兼容。

## Docker 本地替换验证（2026-09-29）

- 镜像：`lynxtonsso:v1.0.0`，基于官方 Keycloak `26.3.2`，内置本分支主题 JAR；不包含完整主线源码构建。
- 运行：独立 Compose 项目 `lynxtonsso`，Keycloak 与 PostgreSQL 均 healthy，HTTP 仅发布 `127.0.0.1:58080`；数据库端口不发布。
- 迁移：旧 H2 数据先停机备份，然后离线导出并导入新 PostgreSQL。`master` / `lynxstudio` Realm ID、全部 4 个用户 ID、15 个客户端 ID 与 8 个签名提供者 ID 核对一致。旧 OIDC issuer `http://localhost:58080/realms/lynxstudio` 不变。
- 实际浏览器：普通测试用户登录账户中心、管理员登录控制台、错误密码拒绝、旧业务 Realm 的灵通云登录页均通过；桌面和 320px 无横向溢出；Logo/favicon 返回 200，SHA256 与源码一致；无页面脚本或资源错误。
- 网络：宿主浏览器与 Docker 容器经 `host.docker.internal:58080` 读取原 Realm 的 OIDC discovery 均通过。
- 启动：已验证新建容器和保留数据库后更换镜像。LynxStudio 启动脚本已改用独立入口，其 Bash/Python 语法与本地配置静态检查通过；未运行会覆盖已有用户的 Realm 对账。
- 清理：原 `lynxstudio-dev-keycloak-1` 容器、19892 临时测试容器与数据库卷已移除；19891 原生 Java 预览已停止。旧身份数据只保留为离线备份与未挂载的原卷。

迁移不延续已有浏览器登录会话，需重新登录。完整源码前端构建、其他业务站点接入及飞书联邦不在此环境验证结果内。

## 管理员登录页残留 Logo 与域名准备（2026-09-29）

- 已复现用户浏览器中的双 Logo：master 遗留 `displayNameHtml` 包含 `kc-logo-text`，被登录主题的 Realm 名称区域再次渲染。图片文件和 favicon 本身已是公司资源，问题来自运行数据。
- 已清空实际 master 的该字段，`start.py` 持续归一化为纯文本回退；实际内置浏览器刷新后的管理员登录页仅显示灵通云品牌。
- 新增 `branding/check-login.py`，覆盖 master 与普通用户登录页；真实页面、Logo/favicon 字节匹配均通过，原始嵌套 Logo 样例能触发失败。
- `https://login.lynxtoncloud.com` 的本机 TLS 证书、Docker Desktop 独立 Namespace、Ingress 和后端转发已部署，使用现有 CA 校验且指定本机解析时返回 HTTP 200。
- **域名切换待完成**：本机 hosts 尚未加入该域名，当前运行中的 SSO issuer 仍为 localhost。启动脚本会在本地域名未正确解析时退出，不重建服务。消费者与身份绑定迁移脚本已准备并通过静态检查，数据库、消费者 Secret 与 Deployment 尚未切换。
- 不修改公网 DNS，也未部署公网证书。待本机管理员完成 hosts 后，再原子协调 SSO hostname、平台身份绑定和消费者 TLS/issuer 的切换。
