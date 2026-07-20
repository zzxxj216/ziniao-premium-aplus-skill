# -*- coding: utf-8 -*-
"""按 spec.json 创建 Etsy 定制化 listing(草稿):建草稿 → 传图/视频 → 设个性化 → 设属性。

用法:
  python create_listing.py spec.json          # 只本地校验+打印计划(dry)
  python create_listing.py spec.json --go     # 真建(全程只到草稿,上架人工)

spec.json 结构(完整示例见 ../references/spec-example.json):
  {
    "title": "...", "description": "...", "price": 12.99, "quantity": 999,
    "taxonomy_id": 1317, "tags": ["..."(≤13,每个≤20字符)], "materials": ["vinyl","laminate"],
    "who_made": "i_did", "when_made": "made_to_order", "type": "physical",
    "shipping_profile_id": 288718622687,          // queries.py shipping-profiles 查
    "readiness_state_id": null, "return_policy_id": null, "shop_section_id": null,
    "item_weight": 0.3, "item_weight_unit": "oz",  // calculated 模板必带重量尺寸
    "item_length": 6, "item_width": 4, "item_height": 0.1, "item_dimensions_unit": "in",
    "images": ["C:/abs/1.png", "..."],            // 本地绝对路径,顺序=rank,≤10 张
    "video": null,                                 // 可选 mp4(5-15秒/<100MB)
    "personalization": { "personalization_questions": [ ... ] },   // 定制化核心,规则见 SKILL.md
    "properties": [ {"property_id":..,"value_ids":[..],"values":[".."]} ]   // 可选
  }
"""
import json
import os
import sys

import _etsy

_UPLOAD_TYPES = {"unlabeled_upload", "labeled_upload"}


def check_personalization(p: dict) -> list[str]:
    """本地预检个性化问题(Etsy 2026-05 规则),返回错误清单。"""
    errs = []
    qs = (p or {}).get("personalization_questions") or []
    if not qs:
        return ["personalization_questions 为空"]
    if len(qs) > 5:
        errs.append(f"问题 {len(qs)} 个 >5(每 listing 上限)")
    if sum(1 for q in qs if q.get("question_type") in _UPLOAD_TYPES) > 1:
        errs.append("上传类问题(unlabeled/labeled_upload)每 listing 最多 1 个")
    for i, q in enumerate(qs, 1):
        t = q.get("question_type") or "text_input"
        text = q.get("question_text") or ""
        if not 1 <= len(text) <= 45:
            errs.append(f"问题{i} question_text 长度 {len(text)}(需 1-45)")
        if len(q.get("instructions") or "") > 120:
            errs.append(f"问题{i} instructions >120 字符")
        opts = q.get("options") or []
        if t == "text_input":
            if not (isinstance(q.get("max_allowed_characters"), int) and 1 <= q["max_allowed_characters"] <= 1024):
                errs.append(f"问题{i} text_input 需 max_allowed_characters(1-1024)")
        elif t == "dropdown":
            labels = [o.get("label") or "" for o in opts]
            if not 1 <= len(opts) <= 30:
                errs.append(f"问题{i} dropdown 需 1-30 个 options")
            if len(set(labels)) != len(labels):
                errs.append(f"问题{i} dropdown 选项 label 重复")
            if any(len(x) > 20 or not x for x in labels):
                errs.append(f"问题{i} dropdown 每个 label 需 1-20 字符")
            if q.get("instructions"):
                errs.append(f"问题{i} dropdown 的 instructions 必须为空")
        elif t == "unlabeled_upload":
            if not (isinstance(q.get("max_allowed_files"), int) and 1 <= q["max_allowed_files"] <= 10):
                errs.append(f"问题{i} unlabeled_upload 需 max_allowed_files(1-10)")
        elif t == "labeled_upload":
            n = q.get("max_allowed_files")
            if not (isinstance(n, int) and n >= 2 and len(opts) == n):
                errs.append(f"问题{i} labeled_upload 需 max_allowed_files≥2 且 options 数量与之相等")
        else:
            errs.append(f"问题{i} 未知 question_type '{t}'")
    return errs


def check_spec(s: dict) -> list[str]:
    errs = []
    for k in ("title", "description", "price", "quantity", "taxonomy_id"):
        if s.get(k) in (None, "", []):
            errs.append(f"缺必填字段 {k}")
    if len(s.get("title") or "") > 140:
        errs.append(f"标题 {len(s['title'])} 字 >140")
    tags = s.get("tags") or []
    if len(tags) > 13:
        errs.append(f"tags {len(tags)} 个 >13")
    if any(len(t) > 20 for t in tags):
        errs.append("有 tag >20 字符(Etsy 上限)")
    q = s.get("quantity")
    if isinstance(q, int) and not 1 <= q <= 999:
        errs.append("quantity 需 1-999")
    if not s.get("shipping_profile_id"):
        errs.append("缺 shipping_profile_id(实体商品必填;queries.py shipping-profiles 选一个)")
    imgs = s.get("images") or []
    if not imgs:
        errs.append("images 为空(至少 1 张,建议≥5 张、最长边≥2000px)")
    if len(imgs) > 10:
        errs.append(f"images {len(imgs)} 张 >10")
    for p in imgs:
        if not os.path.isfile(p):
            errs.append(f"图片不存在:{p}")
    v = s.get("video")
    if v and (not os.path.isfile(v) or not v.lower().endswith(".mp4")):
        errs.append(f"视频不存在或非 mp4:{v}")
    if s.get("personalization"):
        errs += check_personalization(s["personalization"])
    else:
        errs.append("缺 personalization(本 skill 专做定制化 listing;真不需要个性化就删掉这条校验对应的块并确认)")
    return errs


_LISTING_FIELDS = ["quantity", "title", "description", "price", "who_made", "when_made",
                   "taxonomy_id", "shipping_profile_id", "readiness_state_id", "return_policy_id",
                   "materials", "tags", "type", "should_auto_renew", "is_taxable", "shop_section_id",
                   "item_weight", "item_length", "item_width", "item_height",
                   "item_weight_unit", "item_dimensions_unit"]


def main(path: str, go: bool):
    s = json.load(open(path, encoding="utf-8"))
    errs = check_spec(s)
    print(f"=== etsy-listing: {path} ===")
    if errs:
        print(f"❌ 预检不过({len(errs)}):")
        for e in errs:
            print(f"  - {e}")
        sys.exit(2)
    body = {k: s[k] for k in _LISTING_FIELDS if s.get(k) is not None}
    body.setdefault("who_made", "i_did")
    body.setdefault("when_made", "made_to_order")
    body.setdefault("type", "physical")
    qs = (s.get("personalization") or {}).get("personalization_questions") or []
    print(f"✅ 预检通过:{len(s.get('images') or [])} 张图, 个性化问题 {len(qs)} 个"
          f"({'/'.join(q.get('question_type','?') for q in qs)})")
    if not go:
        print(json.dumps(body, ensure_ascii=False, indent=1))
        print("\n[dry] 未发请求。计划无误就加 --go 真建(草稿)。")
        return

    d = _etsy.die_if_failed(_etsy.api("POST", "/listings", body=body), "创建草稿")
    lid = d.get("listing_id")
    print(f"✅ 草稿已建:listing_id={lid}")

    for i, img in enumerate(s.get("images") or [], 1):
        o = _etsy.upload_file(f"/listings/{lid}/images", img, params={"rank": i})
        print(f"  图{i} rank={i}: {'✅' if o.get('success') else '❌ ' + str(o.get('message'))[:80]}")
    if s.get("video"):
        o = _etsy.upload_file(f"/listings/{lid}/video", s["video"])
        print(f"  视频: {'✅' if o.get('success') else '❌ ' + str(o.get('message'))[:80]}")

    if s.get("personalization"):
        _etsy.die_if_failed(_etsy.api("POST", f"/listings/{lid}/personalization", body=s["personalization"]),
                            "设置个性化")
        print(f"  个性化: ✅ {len(qs)} 个问题已设")

    for pr in s.get("properties") or []:
        o = _etsy.api("PUT", f"/listings/{lid}/properties/{pr['property_id']}",
                      body={"value_ids": pr["value_ids"], "values": pr["values"]})
        print(f"  属性 {pr['property_id']}: {'✅' if o.get('success') else '❌ ' + str(o.get('message'))[:80]}")

    print(f"\n✅ 完成:listing_id={lid} 仍是 draft。人工审核后上架 →"
          f" PATCH /api/v1/etsy/listings/{lid} {{\"fields\":{{\"state\":\"active\"}}}}(开始计上架费)")
    print(f"   复核:python queries.py show {lid}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--go"]
    if not args:
        print(__doc__); sys.exit(1)
    main(args[0], "--go" in sys.argv)
