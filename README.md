# Amazon 运营技能合集

本仓含两个互补的 agent 技能(Claude Code / Codex 通用),各自独立、一个文件夹一个 skill:

| 技能 | 文件夹 | 做什么 |
|---|---|---|
| **紫鸟高级A+** | [`ziniao-premium-aplus/`](ziniao-premium-aplus/) | 用紫鸟(浏览器自动化,中心服务)把素材图建成 **Premium 高级 A+** 草稿 |
| **amazon-listing** | [`amazon-listing/`](amazon-listing/) | 用 SP-API(multi-channel-api 中间层)做 listing **创建/编辑/拉取 + 标准 A+** |
| **tk2amazon** | [`tk2amazon/`](tk2amazon/) | 把 TikTok Shop 已有产品**同步到 Amazon / Shopify / Etsy**(拉TK→人机协作补缺口→建草稿) |

两者**互补**:`ziniao-premium-aplus` 做 SP-API 建不了的 **Premium A+**;`amazon-listing` 做 listing 全流程 + **标准 A+**。

## 怎么用
每个文件夹都是一个**自包含的 skill**(含 `SKILL.md` + `README.md`)。安装时把对应文件夹拷进 agent 的 skills 目录:
- **Claude Code**:`cp -R <文件夹> ~/.claude/skills/`
- **Codex**:`cp -R <文件夹> ~/.agents/skills/`(`ziniao-premium-aplus` 用其 `codex/` 子目录)

各自的依赖、配置、用法见**文件夹内的 `README.md` / `SKILL.md`**:
- 紫鸟高级A+ → [`ziniao-premium-aplus/README.md`](ziniao-premium-aplus/README.md)(配 `APLUS_BASE_URL` / `APLUS_API_KEY`)
- amazon-listing → [`amazon-listing/README.md`](amazon-listing/README.md)(运营端只填 `AMAZON_MCA_URL`)

> 两个技能的**服务端**(紫鸟中心服务 / multi-channel-api 中间层)都部署在各自的主项目仓库,本仓只含技能/指令 + 文档,不含服务端代码,也不含任何密钥。
