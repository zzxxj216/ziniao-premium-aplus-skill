---
name: etsy-listing
description: 在 Etsy 创建**定制化/个性化** listing(草稿):买家下单时填名字(text_input)、选字体/颜色(dropdown)、上传照片或 logo(买家传图)。也可给已有 listing 补设/修改个性化问题、查运费模板/类目/属性等 id。当用户说"在 Etsy 上一个定制商品""建个 Etsy 定制 listing""给这个 Etsy listing 加个性化选项/让买家填名字"时使用。不要用于:从 TikTok 搬品(用 tk2amazon 的 to_etsy)、Amazon 上品(用 amazon-listing)。
---

# Etsy 定制化 Listing 创建

把"一组素材图 + 商品信息 + 定制项设计"变成 Etsy 上的**个性化草稿 listing**。
脚本在 `scripts/`,自包含;所有读写走中间层 `AMAZON_MCA_URL` 的 `/api/v1/etsy`(密钥在中间层,
运营端零密钥)。图片/视频从**运营本机**直接 multipart 上传,不需要放到中间层机器。

## 前置
1. `pip install requests python-dotenv`(与 amazon-listing 相同);
2. `cp .env.example .env` 填 `AMAZON_MCA_URL`;中间层必须在跑。

## 🔴 红线
- **只建草稿**:`state=draft`,绝不自动上架(上架=运营人工 PATCH `state=active`,开始计上架费)。
- **禁删 listing**:任何情况不调 DELETE;要下架用 PATCH state,清理用改草稿/库存 0。
- **改已有 listing 须显式给 listing_id**,改前先 `queries.py show <id>` 看一眼现状。
- 个性化 POST 是**整体替换**:更新已有 listing 的问题时,必须把要保留的老问题
  (带 `question_id`)一起提交,否则会被删掉。

## 工作流

```bash
# 1. 查 id(建 listing 要引用的都在这):
python scripts/queries.py shipping-profiles   # 运费模板(必选一个)
python scripts/queries.py readiness           # 备货时效(实体商品必选一个)
python scripts/queries.py taxonomy sticker    # 类目 taxonomy_id
python scripts/queries.py sections            # 店铺分区(可选)
python scripts/queries.py properties 1317     # 该类目可设属性(可选)

# 2. 你(agent)按下方规则设计定制项 + 写英文文案,拼 spec.json
#    (完整示例照抄:references/spec-example.json)

# 3. 预检+建草稿(一条龙:建 listing → 传图 → 设个性化 → 设属性):
python scripts/create_listing.py spec.json         # dry:只校验+打印计划
python scripts/create_listing.py spec.json --go    # 真建(草稿)

# 4. 复核 + 汇报 listing_id:
python scripts/queries.py show <listing_id>
```

给**已有** listing 补设/修改个性化:
```bash
python scripts/personalize.py <listing_id> show               # 先看现状(拿 question_id)
python scripts/personalize.py <listing_id> questions.json --go  # 整体替换(含要保留的老问题)
```

## 定制项(personalization)设计规则 —— 本 skill 的核心

每个 listing 最多 **5 个问题**;四种类型,按定制内容选:

| 类型 | 用途 | 必带字段 | 限制 |
|------|------|---------|------|
| `text_input` | 买家填文字(名字/日期/短语) | `max_allowed_characters`(1-1024) | instructions 可选 ≤120 |
| `dropdown` | 买家选项(字体/颜色/尺寸/主题) | `options`(1-30 个) | label 唯一且 ≤20 字符;**instructions 必须为空** |
| `unlabeled_upload` | 买家传图(照片/logo) | `max_allowed_files`(1-10) | 上传类每 listing **最多 1 个问题** |
| `labeled_upload` | 买家按标签传多张图(如"正面照""背面照") | `max_allowed_files`≥2 且 = options 数 | 同上,与 unlabeled 二选一 |

- `question_text` ≤45 字符,英文,写清楚要买家给什么;`required` 按定制逻辑定
  (核心定制项 true,可选加购项 false)。
- 设计思路:**文字定制**(刻名/日期)→ text_input 限字数(和产品实际可印宽度匹配,
  比如姓名贴 ≤25);**样式选择**(字体/颜色)→ dropdown,选项与素材图里的展示一致;
  **图片定制**(照片贴纸/logo)→ upload 类。描述里写一段 "HOW TO ORDER" 引导买家填。
- 有变体维度(尺寸/张数不同价)时:个性化问题**不做价格差异**(它不影响价格);
  价差用 inventory 变体做,或拆成多个 listing。

## 文案/图片要点
- 标题 ≤140(埋 "custom/personalized + 品类 + 场景" 搜索词);tags ≤13 个、每个 ≤20 字符
  (关键词由你 AI 生成:核心词+长尾词,模拟美国买家搜索);描述带 HOW TO ORDER 步骤。
- 图 ≤10 张,顺序=rank(第 1 张主图);建议 ≥5 张、最长边 ≥2000px;定制品必备:
  效果图、字体/颜色选项图、尺寸图。视频可选(mp4, 5-15 秒, <100MB)。
- 实体商品必带 `shipping_profile_id`(calculated 模板还要重量尺寸,spec 里贴纸默认
  0.3oz/6×4×0.1in 一般不用动);`taxonomy_id` 默认 1317=Stickers,其它品类先查。

## 事实与守门
- 价格/数量/运费模板选择等事实优先从用户请求和素材推断;推断不出且填错有实际损失的才问人。
- `create_listing.py` 本地预检(字段缺失/超长/个性化规则/图片存在性)不过直接拒,改好再 --go。
- 建完只汇报 `listing_id` + 状态;上架永远人工。
