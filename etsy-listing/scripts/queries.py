# -*- coding: utf-8 -*-
"""Etsy 只读查询:建 listing 前把要引用的 id 都查齐。

用法:
  python queries.py shipping-profiles      # 运费模板(id/类型/发货地/目的地)
  python queries.py readiness              # 备货时效(readiness_state_id)
  python queries.py return-policies        # 退货政策(return_policy_id)
  python queries.py sections               # 店铺分区(shop_section_id)
  python queries.py taxonomy [关键词]      # 类目树查 taxonomy_id(如 sticker)
  python queries.py properties <taxonomy_id>   # 该类目可设置的属性(property_id/值)
  python queries.py show <listing_id>      # listing 详情+个性化问题+图片数
"""
import json
import sys

import _etsy


def sp():
    rows = (_etsy.die_if_failed(_etsy.api("GET", "/shipping-profiles"), "拉运费模板") or {}).get("results") or []
    print(f"运费模板 {len(rows)} 个:")
    for r in rows:
        n = len(r.get("shipping_profile_destinations") or [])
        print(f"  {r.get('shipping_profile_id')}  [{r.get('profile_type')}]  {r.get('title')}"
              f"  (发货地 {r.get('origin_country_iso')} {r.get('origin_postal_code') or ''}, 目的地{n})")


def readiness():
    rows = (_etsy.die_if_failed(_etsy.api("GET", "/readiness-states"), "拉备货时效") or {}).get("results") or []
    print(f"备货时效 {len(rows)} 个:")
    for r in rows:
        print(f"  {r.get('readiness_state_id')}  [{r.get('readiness_state')}]"
              f"  {r.get('processing_days_display_label') or ''}")


def return_policies():
    rows = (_etsy.die_if_failed(_etsy.api("GET", "/return-policies"), "拉退货政策") or {}).get("results") or []
    print(f"退货政策 {len(rows)} 个:")
    for r in rows:
        print(f"  {r.get('return_policy_id')}  accepts_returns={r.get('accepts_returns')}"
              f" exchanges={r.get('accepts_exchanges')} deadline={r.get('return_deadline')}")


def sections():
    d = _etsy.die_if_failed(_etsy.api("GET", "/sections"), "拉店铺分区") or {}
    rows = d.get("results") or []
    print(f"店铺分区 {len(rows)} 个:")
    for r in rows:
        print(f"  {r.get('shop_section_id')}  {r.get('title')}  (在售 {r.get('active_listing_count')})")


def taxonomy(query: str | None):
    d = _etsy.die_if_failed(_etsy.api("GET", "/taxonomy", params={"query": query}), "查类目") or []
    rows = d.get("results") if isinstance(d, dict) else d
    print(f"类目({query or '全部'}):")
    for r in (rows or [])[:20]:
        print(f"  {r.get('id')}  {r.get('name')}  ({r.get('full_path') or ''})")


def properties(taxonomy_id: str):
    o = _etsy.api("POST", "/call", body={"method": "GET",
                                         "path": f"/application/seller-taxonomy/nodes/{taxonomy_id}/properties"})
    rows = (_etsy.die_if_failed(o, "查类目属性") or {}).get("results") or []
    print(f"taxonomy {taxonomy_id} 可设属性 {len(rows)} 个:")
    for r in rows:
        vals = ", ".join(f"{v.get('value_id')}={v.get('name')}" for v in (r.get("possible_values") or [])[:6])
        print(f"  {r.get('property_id')}  {r.get('name')}  (required={r.get('is_required')})")
        if vals:
            print(f"      可选值: {vals}{' …' if len(r.get('possible_values') or []) > 6 else ''}")


def show(listing_id: str):
    d = _etsy.die_if_failed(_etsy.api("GET", f"/listings/{listing_id}"), "查 listing") or {}
    p = d.get("price") or {}
    amt = p.get("amount")
    price = f"{amt / (p.get('divisor') or 100):.2f}" if isinstance(amt, (int, float)) else "?"
    print(f"listing {listing_id}  [{d.get('state')}]  ${price}  qty={d.get('quantity')}")
    print(f"  标题: {d.get('title','')[:100]}")
    print(f"  tags: {', '.join(d.get('tags') or [])}")
    print(f"  taxonomy={d.get('taxonomy_id')} shipping_profile={d.get('shipping_profile_id')}"
          f" personalizable={d.get('is_personalizable')}")
    imgs = _etsy.api("GET", f"/listings/{listing_id}/images")
    n = len(((imgs.get("data") or {}).get("results")) or [])
    print(f"  图片: {n} 张")
    pers = _etsy.api("GET", f"/listings/{listing_id}/personalization")
    qs = ((pers.get("data") or {}).get("personalization_questions")) or []
    print(f"  个性化问题 {len(qs)} 个:")
    for q in qs:
        print(f"    [{q.get('question_type')}] {q.get('question_text')}"
              f" (required={q.get('required')}, id={q.get('question_id')})")


def main(argv):
    if not argv:
        print(__doc__); sys.exit(1)
    cmd = argv[0]
    if cmd == "shipping-profiles":
        sp()
    elif cmd == "readiness":
        readiness()
    elif cmd == "return-policies":
        return_policies()
    elif cmd == "sections":
        sections()
    elif cmd == "taxonomy":
        taxonomy(argv[1] if len(argv) > 1 else None)
    elif cmd == "properties" and len(argv) > 1:
        properties(argv[1])
    elif cmd == "show" and len(argv) > 1:
        show(argv[1])
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
