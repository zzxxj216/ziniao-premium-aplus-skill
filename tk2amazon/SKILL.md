---
name: tk2amazon
description: 把 TikTok Shop 上已有的产品**同步/搬运到 Amazon / Shopify / Etsy**(拉 TK 产品 → agent 自动补足目标平台要求 → 建草稿 listing)。当用户说"把 TK/TikTok 的产品同步到亚马逊/Shopify/Etsy""TK 上有这个品,帮我上到 XX 平台""从 TikTok 搬品"时使用。不要用于:纯 Amazon 上品(用 amazon-listing)、TK 侧上品/改品(本 skill 对 TK 只读)。
---

# TK → Amazon / Shopify / Etsy 产品同步(人机协作)

> 名字叫 tk2amazon 是历史原因;现在支持三个目标平台。Amazon 走完整 7 步(要求最严);
> Shopify/Etsy 轻量得多,见下方「Shopify / Etsy 方向」一节。

> TK 上已经在卖的产品,信息是**不完整的**(Amazon 要求严得多:product_type 必填集、
> 标题≤75、Item Highlight、5 条五点、后端词、白底主图…)。
> 流程:脚本拉事实 → `gap_check` 列出缺口 → **你(agent)从 TK 数据推断补齐事实 + 代写文案**
> → `to_payload` → amazon-listing 建品(草稿 qty=0)。推断不出且填错有实际损失的才去问人。

## 前置
1. 中间层 multi-channel-api 在跑;**首次使用**:`cp .env.example .env` 改 `AMAZON_MCA_URL`
   (或依赖仓根 .env / 环境变量,三处任一即可);
2. **amazon-listing skill 已安装且与本 skill 平级**(`../amazon-listing/scripts/`,
   Amazon 侧全靠它:stores/create_listing/create_family/lint/family_status);
3. TK 店铺已在中间层注册(`--shop <名>`,不传走默认店;店名打错会被拒)。

## 工作目录约定(重要,别混)
**整个流程固定在一个工作目录跑**(建议专门建一个,比如 `D:\tk2amazon-work\`):
`tk_drafts/<product_id>/` 会建在这里,里面是 draft.json、imgs/、payload.json/family.json。
草稿里的图片路径、to_payload 产出的 `file:` 全是**绝对路径**,所以后续调 amazon-listing
的脚本从**任何目录**跑都不断链;但你自己找文件方便起见,别换来换去。

## 🔴 红线
- **TK 侧只读**:代码级闸门(`_tk.api` 只放行 GET 和 POST /products/search),
  中间层的 TK 创建/修改/删除/上下架端点本 skill 永远不碰。
- **事实优先取自 TK 数据**:数量/尺寸/价格/类型从 TK 标题/价格/类目链推断;
  只有推断不出、且填错有实际损失的(如定价策略拿不准)才去问人。
- Amazon 侧沿用 amazon-listing 红线:新唯一 SKU + **父与全部子体** GET 防覆盖、
  qty=0 草稿(to_payload 写死)、brand 默认 Inkelligent。

## 工作流(7 步)

```bash
# 1. 找品(--status 真实枚举:ACTIVATE/SELLER_DEACTIVATED/DRAFT/...)
python <skill>/scripts/tk_list.py [--shop main] [--n 50] [--status ACTIVATE]

# 2. 拉草稿:**一开始就带 --download**(图片下到本地,绝对路径)
#    重跑安全:draft 已存在时 amazon 块和已下图自动保留(彻底重来才用 --force)
python <skill>/scripts/tk_pull.py <product_id> --download

# 3. 体检缺口:📝待补(exit 1)/ 完整(exit 0)
python <skill>/scripts/gap_check.py tk_drafts/<id>/draft.json
```
4. **你(agent)直接编辑 draft.json** 按待补清单把事实写进 `amazon` 块——**优先从
   TK 数据推断**(数量看标题、价格沿用 TK 价注意 raw 百倍歧义、类型看类目链、SKU 自己
   生成 INK- 前缀)。字段类型/示例见 tk_pull.py 里 amazon 块的行内注释(store 是
   `"main"`/`"byane@UK"` 字符串、bullets 是 5 条英文字符串数组、price_usd 是数字)。
   推断不出且填错有实际损失的才去问人。
5. **你代写文案**(英文):标题≤75、Item Highlight≤125、5 条五点、描述(基于
   `description_text` 重写,别照抄 TK 的 HTML 腔)、后端词≤249 字节 —— 全部埋词,
   写回 `amazon` 块。
6. 机械转换 + 建品(不用手拼 30 个属性,脚本来):
   ```bash
   python <skill>/scripts/to_payload.py tk_drafts/<id>/draft.json            # 单品 → payload.json
   python <skill>/scripts/to_payload.py tk_drafts/<id>/draft.json --family   # 变体族 → family.json
   python ../amazon-listing/scripts/create_listing.py create <payload> --store <店>
   ```
   to_payload 自带守门:缺关键字段/超长/五点≠5 条直接拒;图片用 draft 里的绝对路径
   自动转 `file:`;qty 写死 0(草稿)。create 返回的 issues 要看,有问题改 draft 重转重建。
   变体族:走 `create_family.py create <family.json>`;create 前脚本会对父+全部子 SKU 防覆盖。
7. 收尾:`lint_listing.py <SKU...>` 体检 + `family_status.py` 记 ASIN → 向用户汇报
   (SKU/ASIN/状态,以及"qty=0 草稿,确认后再放库存")。

## draft.json 结构
- TK 事实(脚本填):`title_tk` / `description_html`+`description_text`(已洗实体)/
  `images[]`(url + local **绝对路径**)/ `skus[]`(seller_sku、price + **price_raw 原始值**、
  qty_tk、sales_attributes 含变体名/变体图 image_url+local)/ `package` / `category_chain`。
- `amazon` 块(第 4-5 步由 agent 填):见 tk_pull.py 行内注释;`variants` 供变体族;
  `notes` 是可选备注数组(如推断依据),不强制。

## TK 数据坑(已在脚本里处理,改脚本时别丢)
- **价格双格式**:`'13.98'`(小数)与 `'1699'`(整数分)并存;`_tk.amount` 有点透传、
  无点除 100;**`'17'` 这类无点整值有 100 倍歧义** → draft 同时存 `price_raw`,
  gap_check 展示两个值让人裁决。
- 描述是 **HTML** → `description_text` 已剥标签 + `html.unescape` 全实体解码。
- 字段新旧双版:`main_images|images`、`urls|url_list`、`inventory|stock_infos`、
  `quantity|available_stock`、`id|sku_id` —— 都做了 fallback。
- 图片扩展名按响应 **Content-Type** 定(PNG/WebP 别存成 .jpg);单图下载失败只跳过不中断,
  draft 先落盘。
- `--status` 过滤:中间层曾把参数包错位置导致静默失效(已修:顶层 `status`);
  tk_list 仍带客户端兜底过滤。
- 单 SKU 产品 `sales_attributes` 为空;多变体时 `name/value_name`,变体图在 `sku_img`。
- **TK 图 ≠ Amazon 图(高频雷区)**:TK 主副图常是营销风——场景图、贴大字标语、促销角标、
  九宫格拼图,Amazon 会拒收或抑制 listing。规则:主图**纯白底**(255,255,255)、无文字/水印/
  logo/道具、产品占比 ~85%;副图无水印无网址;全部 ≥1000px(建议 1600px)。
  gap_check 装了 Pillow 会自动初筛(尺寸不足/主图四角非白)并给出警告(不阻塞);
  你按警告自行判断:能重做/替换就换,不能就用原图并在汇报里说明风险。

## Shopify / Etsy 方向(轻量:平台宽松,两步走)
两个方向共用第 1-2 步(tk_list 找品 → tk_pull --download 拉草稿),然后**跳过 Amazon 的
gap_check**(平台要求宽松),直接用专属脚本 —— **直接带 `--go` 执行**(不带 --go 只
打印计划,可用于自查);两边都**只建草稿**,上架永远人工:

```bash
# Etsy(走中间层现成端点;tags 必给——TK 没有对应字段,你自行拟定)
python scripts/to_etsy.py tk_drafts/<id>/draft.json --tags "a,b,..."(≤13)        [--title ..] [--price 12.99|--price-mult 1.3] [--qty 1-999] [--taxonomy-id 1317] [--go]
python scripts/to_etsy.py profiles      # 查运费模板/备货时效/类目(只读)
python scripts/to_etsy.py list draft    # 列 Etsy 草稿(只读)
# 建成后:draft 状态,上架=人工 PATCH state=active(开始计上架费);
# ⚠️ 重复 --go 会建新草稿不覆盖;更新已有 listing 用 --listing-id <id>(只刷文案/tags)

# Shopify(经中间层建品,status=draft 写死;图用已下载本地图 base64,不依赖 TK CDN)
python scripts/to_shopify.py tk_drafts/<id>/draft.json [--title ..] [--price ..] [--qty ..]        [--tags "a,b"] [--go]
python scripts/to_shopify.py list       # 列 Shopify 产品(只读)
# 建成后:draft 状态,上架=人工在 Shopify 后台切 Active
```
平台差异速查:Etsy 标题 ≤140、tags ≤13、数量 ≤999、类目/运费模板必须有(端点自动兜底取
店铺第一个,店里没配会报错,先跑 profiles 看);多变体 Etsy 最多 2 维。Shopify 几乎无硬性
要求(title 即可),多变体自动展开为 variants(option1=变体名)。图片:Etsy 由端点从 TK CDN
转传;Shopify 优先本地图 base64(先 tk_pull --download)。**TK 图合规要求两平台都宽松
(无白底强制),但仍建议人扫一眼有没有 TK 水印/促销角标。**

## 与其它 skill 的分工
- **amazon-listing**(平级目录 `../amazon-listing/`):Amazon 侧一切读写(第 4/6/7 步在调它);
- **ziniao-premium-aplus**:同步完想做高级 A+ 时再用;
- 本 skill 负责「TK 事实搬运 + 缺口管理 + 三平台机械转换」;中间层另有服务端一键同步端点(amazon/etsy 的 sync-from-tiktok),参数都齐时可直调,本 skill 的价值是**把参数自动补对**。
