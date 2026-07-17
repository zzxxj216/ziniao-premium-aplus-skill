# 复用模板:Inkelligent 儿童姓名标签(Kids Name Labels)高级 A+

一条**已跑通 5 遍**的固定流水线:把"一个主题的一组 A+ 成品横幅图"建成 Inkelligent 美国站的
标准 7 模块高级 A+ 草稿。**换主题时只改几个变量,骨架/问答/对比表几乎不动。**

已建主题(每个都 `ok:true` / 7 模块 / 仅草稿,未提交):

| 主题 | hero ASIN(对比表序号1) | SKU | 素材文件夹 | 构建脚本 |
|------|----------------------|-----|-----------|---------|
| Construction | `B0H6LQWT6M` | INK-KIDLABELS-CONSTRUCTIONS | `~/Desktop/CONSTRUCTION/A+` | `build_kidlabels.py` |
| Animals | `B0H6M66LMW` | NK-KIDLABELS-ANIMALS | `~/Desktop/ANIMALS/A+` | `build_kidlabels_animals.py` |
| Dinosaur | `B0H6M8NTNW` | INK-KIDLABELS-DINOSAURS | `~/Desktop/dinosaur/A+` | `build_kidlabels_dinosaur.py` |
| Insect | `B0H6M82DG8` | INK-KIDLABELS-INSECTS | `~/Desktop/insect/a+-1`(web/h5) | `build_kidlabels_insect.py` |
| Monster | `B0H6M8RNYH` | INK-KIDLABELS-MONSTERS | `~/Desktop/monster/A+` | `build_kidlabels_monster.py` |

> 脚本都在 `ziniao-premium-aplus-poc/service/`。新主题**照抄最接近的一份**(单文件夹选 monster/dinosaur,双文件夹选 insect)再改变量即可。

## 一、固定 7 模块骨架(顺序不要动)
所有主题的图都是「**成品横幅**」(文字/设计已印在图里)→ 一律「完整图片 / 轮播」,**只配 alt,不另写标题正文**。

| # | 模块 | 内容角色 | 图 |
|---|------|---------|----|
| 1 | 完整图片 | `head` 头图 | 1 张(PC+MB) |
| 2 | 完整图片 | `motif` 主题设计展示("Choose Your Favorite …") | 1 张 |
| 3 | 完整图片 | `size` 尺寸指南 | 1 张 |
| 4 | 轮播 简单 | 定制流程:`design` `background` `text` `peel` | **4 面板** |
| 5 | 轮播 简单 | 使用场景:`clothing` `bottles` `waterproof` | **3 面板** |
| 6 | 问答 | 5 组 Q&A(见下,固定) | — |
| 7 | 对比表1 | hero + 固定 6 品 × 5 指标 = 35 值 | — |

共 3+4+3 = **10 张成品横幅**(每张都要 PC 桌面 + MB 移动两版)。
`name` = `"Kids Name Labels A+ - {主题}"`,`store` = `"Inkelligent"`。

## 二、问答(逐字照抄,勿改)
5 组;**A1 恰好 248 字**(上限 250),且已把 5 个主题列进去,新主题无需改动。
直接从任一 `build_kidlabels_*.py` 的 `qa` 块复制。要点:
- Q1 答案里 `Animals, Construction, Dinosaur, Insect or Monster` —— 若将来加**第 6 个主题**,要把新主题名加进这句并**重新数字数 ≤250**。
- 模块级带 `"ai_generated": true`。

## 三、对比表(复用 `build_sticker_sets.comparison`)
`from build_sticker_sets import comparison` → `cmp = comparison(HERO_ASIN, HERO_NAME); cmp["title"] = "Compare Our Custom Label Range"`。
- **只有 hero(序号1)每主题换**:`HERO_ASIN` + `HERO_NAME`(短标题 **≤25 字**,如 `"Monster Kids Labels"`)。
- 序号 2~7 固定:`["B0H5VWTJ6B","B0GGHLH9SJ","B0GWPV2MN2","B0H1M6Q8VS","B0G4DLD2P9","B0GR91PN41"]`。
- 5 指标固定:Color / Material / Finish type / Minimum of Pieces / Apply(hero 那列 Minimum=`60 pcs`)。
- hero ASIN 必须**该店铺可用**;换主题务必核对。

## 四、⚠️ 图片文件夹结构每主题都不同 —— 必须现场探明
这是唯一的坑。已见 4 种布局,**不要假设**:

| 布局 | 例 | PC/MB 区分 | 编号 |
|------|----|-----------|------|
| 单文件夹 + 按宽度分 | Animals | 宽 >1900 = PC,窄 = MB | 尺寸指南 PC 可能无 `(N)` 后缀 |
| 单文件夹 + 按宽度分 + **MB 打乱** | Dinosaur | 同上 | 需 `PC_TO_MB` 内容映射 |
| **双文件夹** | Insect | `web/`=PC,`h5/`=MB | PC 文件名非连续 `NN_*`;MB `(N)` 干净 1:1 |
| 单文件夹 + **双时间戳批** + **MB 打乱** | Monster | `17_05_*`=PC,`17_06_*`=MB | MB `(N)` 与 PC 内容不同义 |

**探明步骤(每次必做):**
1. `ls` 看文件名 → 判断是单/双文件夹、靠什么分 PC/MB(宽度?时间戳?子目录?)。
2. `sips -g pixelWidth/pixelHeight` 抽查尺寸。
3. **逐张 Read 看图**,记下每张的内容标题。
4. **PC↔MB 按内容配对,不能靠编号!** 多个主题的 MB 编号是打乱的(MB `(1)` 未必对 PC `(1)`)。
   把 10 张 PC、10 张 MB 都看完,建 `内容→(pc_n, mb_n)` 映射再写 `ROLE` 表。

## 五、脚本结构(照抄 monster/insect)
- 常量:文件夹路径、`HERO_ASIN`、`HERO_NAME`(≤25)、`CMP_TITLE="Compare Our Custom Label Range"`。
- `ROLE = {角色: (pc_n, mb_n, alt), ...}` —— 10 个角色,`mb_n` 填**内容匹配**的 MB 号;`alt` 写本主题英文替代文本。
- glob 定位:`_pc(n)` / `_mb(n)`(按该主题布局写 glob;注意 `*(1).png` 不会误配 `(10).png`)。
- `banner(role)` → `{"desktop":_pc, "mobile":_mb, "alt":...}`;`build_spec()` 按上面 7 模块拼 `modules`。
- 支持 `--dry` 打印 spec JSON。

## 六、建之前先出预览页(不碰紫鸟)
**用紫鸟创建之前,先由 agent 按 spec 自己写一个 HTML 预览页(如 `preview.html`)给运营确认排版。**
**纯本地、不登录不建草稿。** 预览页尽量贴近上架后观感,建议做到:
- 💻/📱 **视图切换**(桌面/移动两版图切换,页宽跟着变);
- **真轮播**(箭头 + 圆点,一屏一屏切);
- **样式化对比表**(hero 列高亮、首列固定、可横向滚动);
- **问答手风琴**;可**隐藏模块标注**看真实效果;缺图标红框。

**图片默认内嵌**(缩到 1200px 的 JPEG 后 base64 内嵌成单文件,如 monster 约 7MB):任何浏览器
都能显示、可直接转发。**这是必需的**——Safari 等浏览器禁止 `file://` 页面加载本地图片,
不内嵌就是一堆空图。仅在确定用宽松浏览器、且图就在本机时,可加 `--link` 用轻量 file:// 版。
确认无误再进第七步建草稿。

## 七、跑构建(护栏,务必遵守)
- **凭据只走环境变量**:`ZINIAO_USERNAME` / `ZINIAO_PASSWORD` / `ZINIAO_COMPANY`(不在任何文件/仓库里)。用一个 runner 脚本在进程内注入 `os.environ` 后再 `create_aplus(build_spec())`。打印凭据一律**打码**,绝不明文。
- **先 dry-run 校验**:所有图片路径存在、A1 ≤250、hero ASIN 正确、模块数=7。
- **`create_aplus` 非幂等**:每跑一次建一个**新草稿**。**只跑一次**,输出 tee 到 `xxx_out.txt`。
  - `ok:false` 且 `modules:[]` = 什么都没建,可重试;
  - `ok:true` = 草稿已建,**绝不重跑**(重跑会建重复草稿)。
- 服务端浏览器串行,一次一个商品;并发返回 409。
- **汇报只回编号**:从返回 `url` 里取 `content/([0-9a-f-]+)/` 作为内容编号回给运营,**不贴整条链接**。

## 八、建完之后(运营手动,程序不代做)
1. 后台点 **Preview** 核对排版;
2. 确认 **AI 图片披露**已勾选(自动化可能没勾上);
3. 关联对应 **SKU**;
4. 满意后**手动提交审核**;junk 草稿手动删。
