# -*- coding: utf-8 -*-
"""同步草稿体检:draft.json 的 amazon 块还缺什么 → 「待补清单」(agent 自行补齐)。

用法:python gap_check.py tk_drafts/<id>/draft.json

原则:缺口由 agent **优先从 TK 数据推断补齐**(标题里的数量、TK 价格、类目链等);
实在推断不出、且填错会造成实际损失的(如定价策略),才去问人。

退出码:0=完整可转 payload;1=还有待补项;3=文件/JSON 坏。
"""
import json
import sys


def main(path: str):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        print(f"[错误] 文件不存在:{path}"); sys.exit(3)
    except json.JSONDecodeError as e:
        print(f"[错误] draft.json 不是合法 JSON:{e}"); sys.exit(3)
    a = d.get("amazon") or {}
    todo, warns, ok = [], [], []

    # —— 事实类:agent 从 TK 数据推断填入 ——
    def fact(key, hint):
        if a.get(key) in (None, "", []):
            todo.append(hint)

    fact("store", "store 未填:同步到哪个店铺/站点?(--store 写法,如 main / byane@UK;默认 main,不确定跑 stores.py 看矩阵)")
    fact("product_type", f"product_type 未填(TK 类目链:{' > '.join(d.get('category_chain') or []) or '无'};"
                         "贴纸=STICKER_DECAL 标签=LABEL,拿不准用探针 /product-types?keywords=)")
    fact("number_of_items", f"number_of_items 未填:从 TK 标题推断(参考:{d.get('title_tk','')[:60]}…)")
    fact("unit_count", "unit_count 未填(通常=每包数量)")
    prices = [f"{s.get('price')} (raw {s.get('price_raw')!r})" for s in d.get("skus") or []]
    fact("price_usd", f"price_usd 未填:可沿用 TK 价(参考:{prices});"
                      "⚠️ raw 无小数点的值有 100 倍歧义,按合理售价判断取哪个")
    fact("sku", "sku 未填:生成全新唯一 SKU(建议 INK- 前缀;变体族要父+子一套)")
    has_var = any(s.get("sales_attributes") for s in d.get("skus") or [])
    if has_var and not a.get("variants"):
        todo.append('TK 有变体(sales_attributes)→ 填 amazon.variants:'
                    '[{"sku":..,"color":..,"main_image":"file:绝对路径"}](变体名→COLOR,变体图已在 sales_attributes[].local)')

    # —— 文案类:agent 代写 ——
    t = a.get("title")
    if not t:
        todo.append("写 Amazon 标题(≤75 字符,英文,埋关键词;带 Item Highlight 时 ≤75 是硬规则)")
    elif len(str(t)) > 75:
        todo.append(f"标题 {len(str(t))} 字 >75(带 Item Highlight 是硬规则),要改短")
    h = a.get("title_differentiation")
    if not h:
        todo.append("写 Item Highlight(≤125 字符;创建时必带,漏了只能事后逐 SKU 补)")
    elif len(str(h)) > 125:
        todo.append(f"Item Highlight {len(str(h))} 字 >125,要改短")
    if len(a.get("bullets") or []) != 5:
        todo.append(f"写五点(现 {len(a.get('bullets') or [])} 条,要 5 条,埋卖点关键词)")
    if not a.get("description"):
        todo.append("写 product_description(基于 draft 的 description_text 重写成 Amazon 风格英文纯文本)")
    bk = a.get("backend_keywords")
    if not bk:
        todo.append("拼后端词(空格分隔英文搜索词,≤249 字节,别与标题重复)")
    elif not isinstance(bk, str):
        todo.append("backend_keywords 应是字符串(空格分隔),现在不是")
    elif len(bk.encode("utf-8")) > 249:
        todo.append(f"后端词 {len(bk.encode('utf-8'))} 字节 >249(超了整条不索引),要裁")

    # —— 图片 ——
    imgs = d.get("images") or []
    if len(imgs) < 7:
        warns.append(f"TK 只有 {len(imgs)} 张图(<7,建议 1主+6副起步;有补图就补,没有就先建)")
    if not any(im.get("local") for im in imgs):
        todo.append("图片未下载:重跑 tk_pull.py <id> --download(重拉会保留 amazon 块,不丢已填内容)")

    # ⚠️ TK 图 ≠ Amazon 图:TK 常见营销风(场景图/贴大字/促销角标/拼图),Amazon 会拒或抑制。
    # Pillow 可用时自动初筛(尺寸/主图白底);结果作为警告提示,不阻塞流程。
    try:
        from PIL import Image
        for i, im in enumerate(imgs, 1):
            loc = im.get("local")
            if not loc:
                continue
            try:
                with Image.open(loc) as pic:
                    w, h = pic.size
                    if max(w, h) < 1000:
                        warns.append(f"图{i} 仅 {w}x{h}(<1000px,Amazon 无法缩放/可能抑制)")
                    if i == 1:                       # 主图:四角采样测白底
                        rgb = pic.convert("RGB")
                        corners = [rgb.getpixel(p) for p in
                                   [(3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)]]
                        if any(min(c) < 235 for c in corners):
                            warns.append(f"主图四角非纯白(采样 {corners[0]}…)——Amazon 主图必须纯白底(255,255,255)")
            except Exception:
                pass
    except ImportError:
        pass                                          # 没装 Pillow 就跳过初筛

    print(f"=== gap_check: {path} ===")
    print(f"TK 标题: {d.get('title_tk','')[:70]}\n")
    if todo:
        print(f"📝 待补({len(todo)}),agent 按下列提示补进 amazon 块:")
        for i, q in enumerate(todo, 1):
            print(f"  {i}. {q}")
    if warns:
        print(f"\n⚠️ 图片提示(不阻塞,自行判断替换/重做):")
        for q in warns:
            print(f"  - {q}")
    if ok:
        print(f"\n✅ 已就绪:")
        for q in ok:
            print(f"  - {q}")
    if not todo:
        print("✅ 草稿完整:python to_payload.py <draft> [--family] → amazon-listing create。")
    sys.exit(1 if todo else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(3)
    main(sys.argv[1])
