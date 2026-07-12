# 紫鸟高级 A+ 制作技能(ziniao-premium-aplus)

把"一组素材图"变成亚马逊后台的**高级 A+(Premium A+)草稿**。识别/选型/文案由 agent(Claude Code / Codex 通用,**同一个文件夹**)完成,**创建执行由中心服务**(装了紫鸟的公共电脑)通过 HTTP 接口完成。本目录只含**技能 + 参考文档**,不含服务端代码。

## 这是什么
- 运营给一个素材文件夹 → agent 看图、选模块、写文案 → **先出本地预览页/排版方案和运营确认** → 调中心服务 `POST /aplus/create` → 出**草稿**(回**内容编号 UUID**,运营按编号去后台 Preview)。
- 草稿只建不提交;运营在后台预览后**人工提交审核**(含 AI 图片披露确认)。
- 支持全部 19 类高级 A+ 模块(完整图片/单图文/双图/四图/文本/背景图片/问答/技术规格/轮播·简单规则导航视频图像/全视频/含文本视频/对比表1·2·3/热点1·2)。
- **对比表 3**:只填 ASIN 自动拉图+标题,短标题自动替换过长自动标题。
- **儿童姓名标签系列模板**:5 主题固定 7 模块已跑通,换主题只改几个变量(见 `reference/kidlabels-template.md`)。
- 图不达标可用 agent 绘图能力按模块尺寸重绘(先和运营确认,标 `ai_generated: true`)。

## 目录
- `SKILL.md` —— 技能入口(带 frontmatter,Claude Code 与 Codex 通用)
- `reference/` —— api.md(接口/返回)、modules.md(每模块字段/尺寸/字数上限)、
  spec-examples.md(19 类可照抄示例)、layout-planning.md(排版规划)、
  kidlabels-template.md(儿童标签 5 主题模板)、about-aplus.md(A+ 是什么)
- `.env.example` —— 配置模板

## 安装(Claude Code / Codex 同一份)
```bash
# Claude Code
cp -R ziniao-premium-aplus ~/.claude/skills/
# Codex(同一个文件夹,Codex 从 cwd 向上扫 .agents/skills 自动发现)
cp -R ziniao-premium-aplus ~/.agents/skills/
# 然后:
cd ~/.claude/skills/ziniao-premium-aplus   # 或 ~/.agents/skills/...
cp .env.example .env   # 填 APLUS_BASE_URL 和 APLUS_API_KEY
```
重开一个会话即可;运营说"用这个文件夹给某商品做高级A+"会自动触发。

## 配置(每台机器一次)
```
APLUS_BASE_URL=http://<公共电脑IP>:8848   # 本机自测用 http://127.0.0.1:8848
APLUS_API_KEY=<与服务端一致的密钥>
```
- 运营端**不需要**任何代码/紫鸟,只需地址+密钥;执行都在公共电脑。
- 服务不在本机时,建 A+ 前先 `POST /aplus/upload` 把本地图传到服务端,用返回的服务端路径填 spec(SKILL.md 第 4 步)。

## 护栏
只建草稿、绝不自动提交;一次一个商品(并发 409,可查 `/aplus/status`);只用运营给的素材,缺就问;一篇最多 7 个模块;AI 图必须披露。
