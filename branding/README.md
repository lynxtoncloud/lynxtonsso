# 灵通云 SSO 品牌主题

`lynxton` 为公司统一身份入口的独立主题，覆盖登录页、账户中心和管理控制台。品牌样式与灵通云主站一致：白色控制台顶栏、浅灰蓝背景、主蓝操作按钮、中文 Logo 和山猫网站图标。登录页桌面使用品牌区与表单双列，800px 以下折叠为单列。

## 分支与上游

- 官方上游：`https://github.com/keycloak/keycloak.git`，本地 remote 为 `upstream`，禁止向其推送。
- 公司仓库：`https://github.com/lynxtoncloud/lynxtonsso.git`，remote 为 `origin`。
- `main` 只接受官方 `upstream/main` 的快进同步，不合入品牌提交。
- 定制分支：`v1.0.0`。
- 本次起点：`b035515009`（完整提交以 Git 为准）；源码版本为 `999.0.0-SNAPSHOT`，不是正式发布版本。

同步时先提交或妥善保存当前改动，然后执行：

```sh
git fetch upstream main
git switch main
git merge --ff-only upstream/main
git push origin main
git switch v1.0.0
git merge main
```

`main` 发生分叉时停止处理，不使用强制推送或 `reset --hard`。定制分支通过合并吸收上游，保留已发布的历史。生产升级另行选定兼容的正式版本并验证；跟踪上游主分支不等于自动部署。

## 源码与边界

主题位于 `themes/src/main/resources/theme/lynxton`：

| 目录 | 责任 |
| --- | --- |
| `common` | 共享品牌变量、控制台样式、Logo、favicon |
| `login` | 登录页面样式、中英文品牌文案、页脚 |
| `account` | 继承 `keycloak.v3` 的账户中心品牌配置 |
| `admin` | 继承 `keycloak.v2` 的管理控制台品牌配置 |

登录继承 `keycloak.v2`。不复制登录主模板、表单或控制台组件，不改变认证协议和认证流程。唯一 React 调整是管理首页 Logo 的替代文字从硬编码 Keycloak 改为既有 `logo` 翻译键，便于读屏识别自定义品牌；这行修改需随完整前端构建生效，独立主题 JAR 不替换上游 JavaScript。注册、错误、重置密码、OTP、Passkey、组织选择及第三方登录继续由上游与实际 Realm 配置决定。页面不添加未配置的飞书、员工或客户登录按钮；本主题不实现双身份域和飞书联邦。

主题在 `themes/src/main/resources/META-INF/keycloak-themes.json` 注册，可随完整源码构建；也可独立打包部署。`import=common/lynxton` 共享资源，上游 `common/keycloak` 仍负责 PatternFly、字体及脚本。不要把 `common` 属性改成 `common/lynxton`。

新登录文案放在主题的 `messages_en.properties`、`messages_zh_Hans.properties`；当前上游将 `zh-CN` 映射为 `zh-Hans`；构建器从同一份简体文案生成 `zh_CN` 兼容条目，供仍使用地区语言文件名的旧版运行时读取，不维护两份翻译。控制台的 title/description 使用上游模板提供的属性。主题仅启用浅色，以匹配主站；不影响其他主题。

## Logo、图标与样式来源

主站参考目录：`/Users/qianhuanping/workspace/website`，提交 `cbbeb87e534d611ead86b4b8cceb91a1c83e095b`；2026-09-29 同时核对 `https://www.lynxtoncloud.com/`。

- `public/logo_cn.png` → `common/resources/img/logo.png`，原图复制。
  SHA256：`477bc68490e5efed9b34b05d65f8a0746053af5cace6d58ef2b91101f155f4a3`。
- `src/app/icon.png` → `common/resources/img/favicon.ico`，保留原图案，转为 16/32/48/64/128/256 像素 ICO。
  原 PNG SHA256：`ec0663cbe9418ffb2dc029bef55335f0213d464ae33919d4e38bdba0dd7abf5b`。
- 配色与字体参考 `src/styles/index.css`、`src/app/globals.css`、`src/components/home/home-top-bar.css`，为本主题重新组织 CSS，未复制主站页面实现。
- 主按钮用 `#0b5bd3` 实色，保证小字号白字对比度；未照搬线上浅蓝渐变。

主题保留上游许可证与来源信息；公司品牌图片仅用于灵通云定制发行，不作为 Keycloak 上游品牌资产。

## 构建与启用

仅需要 Python 3.9+ 标准库；不安装前端依赖、不重编译 Keycloak：

```sh
python3 branding/build-theme.py
# 或将产物写到指定位置
python3 branding/build-theme.py --output /tmp/lynxton-theme.jar
```

产物默认位于 `branding/target/lynxton-theme.jar`，不提交版本库。将 JAR 放入经过版本核验的 Keycloak `providers/` 目录，按该版本要求执行构建和重启。已有 Realm 不会被自动修改。

在目标 Realm 的 Realm settings → Themes 中，将 Login theme、Account theme、Admin theme 都设为 `lynxton`。管理控制台对应哪个 Realm，就在那个 Realm 配置 Admin theme。启用国际化并按需设置默认语言 `zh-CN` 或 `en`；Realm 显示名继续标明实际登录范围。邮件主题保持原配置。

开发时也可以将整个 `lynxton` 目录只读挂载到 `/opt/keycloak/themes/lynxton`，使用 `--spi-theme--static-max-age=-1 --spi-theme--cache-themes=false --spi-theme--cache-templates=false` 禁用主题缓存。只绑定本机测试端口，勿将开发服务和测试账号用于生产。

## 本地 Docker 测试

运行 `python3 branding/docker/start.py` 可启动独立的本机测试环境，包含 PostgreSQL、测试 Realm 和当前主题。地址、测试账号与日常操作见 [Docker 测试说明](docker/README.md)。

## 验证范围

发布前验证真实 Keycloak 的中文/英文登录、注册、表单错误、找回密码、OTP/Passkey、退出确认、账户中心及管理控制台；检查 Logo 和 favicon 返回成功、键盘焦点、320px 与桌面布局、长错误提示及操作栏。登录认证能力的开关仍由 Realm 配置决定，未配置能力不能用静态界面替代。

管理员登录页也必须单独验证：master 初始化可能遗留含上游 Logo 的 `displayNameHtml`。本地启动入口将它清空以回退到纯文本显示名；`python3 branding/check-login.py --base-url <入口地址>` 会检查实际登录 HTML 和品牌资源。

每次更新上游都需复查继承主题、资源解析、PatternFly 变量和三类页面；不以单纯 JAR 打包成功替代浏览器及认证流程验证。
