# Amazon 运营技能合集

本仓含两个互补的 agent 技能(Claude Code / Codex 通用):

| 技能 | 位置 | 做什么 |
|---|---|---|
| **紫鸟高级A+(ziniao-premium-aplus)** | 仓根目录 | 用紫鸟(浏览器自动化)把素材图建成**Premium 高级 A+** 草稿 |
| **amazon-listing** | `amazon-listing/` | 用 SP-API(multi-channel-api 中间层)做 listing **创建/编辑/拉取 + 标准 A+** |

详见各自的 `SKILL.md` / `README.md`。下面是「紫鸟高级A+」的说明。

---

# 紫鸟高级 A+ 制作技能(ziniao-premium-aplus)

把"一组素材图"变成亚马逊后台的**高级 A+(Premium A+)草稿**。识别/选型/文案由 agent(Claude Code 或 Codex)完成,**创建执行由中心服务**(装了紫鸟的公共电脑)通过 HTTP 接口完成。本仓库只含**技能/指令 + 文档**,不含服务端代码。

## 这是什么
- 运营给一个素材文件夹 → agent 看图、选模块、写文案 → 调中心服务 `POST /aplus/create` → 出**草稿**。
- 草稿只建不提交;运营在后台预览后**人工提交审核**。
- 支持全部 19 类高级 A+ 模块(完整图片/单图文/双图/四图/文本/背景图片/问答/技术规格/轮播·简单规则导航视频图像/全视频/含文本视频/对比表1·2·3/热点1·2)。

## 目录
- `SKILL.md` —— Claude Code 技能入口(带 frontmatter)
- `reference/` —— api.md(接口)、modules.md(每模块字段/尺寸/字数上限)、spec-examples.md(可照抄示例)、layout-planning.md(排版规划)、about-aplus.md(A+ 是什么)
- `codex/` —— Codex 版(`AGENTS.md` + 同一套 reference)
- `.env.example` —— 配置模板

## 安装:Claude Code
```bash
git clone <本仓库> ziniao-premium-aplus
cp -R ziniao-premium-aplus ~/.claude/skills/
cd ~/.claude/skills/ziniao-premium-aplus
cp .env.example .env   # 填 APLUS_BASE_URL 和 APLUS_API_KEY
```
重开一个 Claude Code 会话即可;运营说"用这个文件夹给某商品做高级A+"会自动触发。

## 安装:Codex
把 `codex/AGENTS.md` 放进 Codex 工作目录(或并入 `~/.codex/AGENTS.md`),并把 `codex/reference/` 一起带上;再 `export APLUS_BASE_URL`、`APLUS_API_KEY`。详见 `codex/AGENTS.md`。
> 若你的 Codex 支持 `~/.codex/skills/`(同 SKILL.md 格式),也可直接把本仓库当作一个 skill 放进去。

## 配置(每台机器一次)
`.env`(或环境变量):
```
APLUS_BASE_URL=http://<公共电脑IP>:8848   # 本机自测用 http://127.0.0.1:8848
APLUS_API_KEY=<与服务端一致的密钥>
```
- 运营端**不需要**任何代码/紫鸟,只需地址+密钥;执行都在公共电脑。
- 中心服务(`server.py`)在主项目仓库,部署在那台装了紫鸟的电脑上。

## 护栏
只建草稿、绝不自动提交;一次一个商品(并发返回 409);只用用户给的素材,缺就问;图片路径需中心服务那台机器可访问。
