# amazon-listing skill

创建 / 编辑 / 拉取 Amazon listing(单品 + 设计款变体族)+ **标准 A+**,经 **multi-channel-api** 中间层(SP-API)。Claude Code 与 Codex 通用。

> 与本仓根目录的「紫鸟高级A+(Premium A+)」skill 互补:那个用紫鸟建 **Premium** A+;这个用 SP-API 做 listing 全流程 + **标准** A+。

## 功能(`scripts/`)
- `create_listing.py` —— 创建/校验 listing(单品/变体族;本地图 `file:` 自动传 COS)
- `edit_listing.py` —— PATCH 改已有 listing(标题/价格/库存/属性)
- `pull_product.py` —— 拉产品信息(按 SKU=listing 视角 / 按 ASIN=catalog 摘要)
- `aplus.py` —— A+ 列出 / 绑定到 ASIN(含 Premium 文档)/ 用图建标准 A+

## 安装
```bash
pip install requests qcloud-cos-python-sdk-v5 Pillow python-dotenv
cp .env.example .env          # 填 AMAZON_MCA_URL + 腾讯 COS_*
# Claude Code:把本目录放进 ~/.claude/skills/
# Codex:    把本目录放进 ~/.agents/skills/(或项目 .agents/skills/)
```

## 依赖的服务
- **multi-channel-api**(中间层,持有 SP-API 凭证,部署在跑 SP-API 的机器上)必须在跑;地址填 `.env` 的 `AMAZON_MCA_URL`。
- **腾讯云 COS**(图床,`COS_*`)——传图给 Amazon 抓取用。

详细操作 + 字段坑见 `SKILL.md` 和 `references/tips.md`。
