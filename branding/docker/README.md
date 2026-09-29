# 本地 Docker 测试环境

在仓库根目录运行（Python 3.9+、Docker Desktop / Docker Engine 和 Compose）：

```sh
python3 branding/docker/start.py
```

脚本构建当前工作树的主题 JAR 并打入 `lynxtonsso:v1.0.0` 镜像，生成随机测试密码，启动独立 PostgreSQL 与 Keycloak，等待健康检查后将管理域也设为灵通云主题。重复执行保留账号与数据库，并重建 Keycloak 容器加载新镜像。

- 账户中心：http://localhost:58080/realms/lynxton-preview/account/
- 管理控制台：http://localhost:58080/admin/master/console/
- OIDC 发现：http://localhost:58080/realms/lynxton-preview/.well-known/openid-configuration
- 管理员：`admin`；密码为本目录 `.env` 的 `SSO_ADMIN_PASSWORD`。
- 普通测试用户：`test-user`；密码为 `.env` 的 `SSO_TEST_PASSWORD`。

`.env` 初次创建权限为 `0600`，已由仓库忽略，不能提交。保留该文件以便重启后使用同一数据库密码；端口可通过其中的 `SSO_PORT` 调整。不要在已有数据库时直接修改初始密码值，账号密码需要从控制台修改，数据库密码需要同步到数据库。管理员在控制台改密码后，也需更新 `.env` 中的 `SSO_ADMIN_PASSWORD`，供脚本再次配置管理域主题使用。已有 LynxStudio 的本地工具也从此文件读取管理密码。

## 日常操作

以下命令均从仓库根目录执行：

```sh
# 状态
docker compose --env-file branding/docker/.env -f branding/docker/compose.yaml ps
# 日志
docker compose --env-file branding/docker/.env -f branding/docker/compose.yaml logs --tail=100 keycloak
# 停止并移除容器，保留数据库
docker compose --env-file branding/docker/.env -f branding/docker/compose.yaml down
# 重新启动（自动更新主题包）
python3 branding/docker/start.py
```

项目名固定为 `lynxtonsso`，使用独立网络和 `lynxtonsso_postgres-data` 卷；数据库和健康端口不发布到宿主机，HTTP 只发布到 `127.0.0.1`。已有 Realm 不会被启动导入覆盖；调整导入 JSON 后可通过控制台修改现有 Realm。只有明确需要清空本测试环境全部账号及数据时，才对上述 `down` 命令增加 `--volumes`，再重新启动。

## 版本与验证边界

定制镜像 `lynxtonsso:v1.0.0` 以本机已缓存并验证过品牌兼容性的 `quay.io/keycloak/keycloak:26.3.2` 为基础，数据库使用 `postgres:17.6-alpine`；其他机器若无镜像则由 Docker 下载。可通过环境变量 `KEYCLOAK_BASE_IMAGE` 指定另外核验过的 Keycloak 基础镜像。镜像构建上下文仅包含 Dockerfile 和主题 JAR，不包含 `.env`、账号或数据库。升级或更换版本前备份测试数据库，不能随意降级已升级的数据库。

`v1.0.0` 是公司的定制分支名。此环境使用该分支主题 JAR 和官方二进制，不是当前 `main` / `999.0.0-SNAPSHOT` 源码的完整构建；管理首页 Logo 替代文字的 JSX 修改仍需完整前端构建。

此环境供本机主题、注册、登录、账户中心和管理控制台验证，使用 `start-dev`。此脚本不会自动创建其他业务站点 Client、员工/外部用户双身份域、飞书、SMTP 或生产 HTTPS；本机迁移后继续以 `http://localhost:58080/realms/lynxstudio` 为已有 LynxStudio 提供身份服务，其他业务站点仍需配置 Client。测试用户为合成用户，邮箱为保留的 `.test` 地址，找回密码未启用。不要作为生产部署配置使用。

## 从旧本地 Keycloak 迁移

本机已将旧 `lynxstudio-dev-keycloak-1` 的 `master`、`lynxstudio` Realm 全量离线导出并迁入独立 PostgreSQL，保留用户 ID、客户端和签名配置，主题切换为 `lynxton`。原始数据备份位于本目录 `.local/backups/`，迁移导出位于 `.local/migration/`，均不入库。该目录可能含账号和客户端凭据，只留在本机，不作为构建上下文或代码提交。

旧容器退出运行后由 `lynxtonsso-keycloak-1` 接管 `58080`。LynxStudio 的本地启动脚本调用本项目入口；其 reset 不删除独立 SSO 数据。原生 Java 预览端口 `19891` 和临时 Compose 测试端口 `19892` 不再使用。

新机器只运行 `start.py` 会创建全新 `lynxton-preview` 测试 Realm，不会凭空获得已迁移的本机账号或业务 Client。旧 Realm 通过一次性离线导入迁入数据库，日常容器仅挂载 `.local/import/` 中的合成测试 Realm。迁移文件不会在正常启动时加载，日常变更应通过管理控制台进行。

迁移跨数据库后，原浏览器会话需要重新登录；已有账号、客户端和用户 ID 保留。
