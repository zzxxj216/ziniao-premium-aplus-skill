# -*- coding: utf-8 -*-
"""给**已有** Etsy listing 设置/更新个性化问题(整体替换)。

用法:
  python personalize.py <listing_id> questions.json          # dry:本地校验+打印
  python personalize.py <listing_id> questions.json --go     # 真设(整体替换!)
  python personalize.py <listing_id> show                    # 看当前问题(含 question_id)

questions.json = {"personalization_questions":[...]}(结构/规则同 create_listing.py)。
⚠️ POST 是**整体替换**:想保留已有问题,先 show 拿到 question_id,把老问题(带 question_id)
和新问题一起放进数组再提交;漏掉的老问题会被删掉。
"""
import json
import sys

import _etsy
from create_listing import check_personalization


def main(argv):
    if len(argv) < 2:
        print(__doc__); sys.exit(1)
    lid = argv[0]
    if argv[1] == "show":
        o = _etsy.api("GET", f"/listings/{lid}/personalization")
        if not o.get("success"):
            # Etsy 对从未用新版问题 API 设置过的 listing 返回 404 = 没有问题记录
            if "404" in str(o.get("message") or o.get("detail")):
                print(f"listing {lid} 尚未设置个性化问题(可直接整体新设,无老问题要保留)")
                return
            raise SystemExit(f"[失败] 查个性化:{o.get('message') or o.get('detail')}")
        qs = (o.get("data") or {}).get("personalization_questions") or []
        print(f"listing {lid} 个性化问题 {len(qs)} 个:")
        print(json.dumps(qs, ensure_ascii=False, indent=1))
        return
    p = json.load(open(argv[1], encoding="utf-8"))
    errs = check_personalization(p)
    if errs:
        print(f"❌ 预检不过({len(errs)}):")
        for e in errs:
            print(f"  - {e}")
        sys.exit(2)
    qs = p.get("personalization_questions") or []
    print(f"✅ 预检通过:{len(qs)} 个问题({'/'.join(q.get('question_type','?') for q in qs)})")
    if "--go" not in argv:
        print(json.dumps(p, ensure_ascii=False, indent=1))
        print("\n[dry] 未发请求。⚠️ 这是整体替换,确认包含要保留的老问题(带 question_id)后加 --go。")
        return
    _etsy.die_if_failed(_etsy.api("POST", f"/listings/{lid}/personalization", body=p), "设置个性化")
    print(f"✅ listing {lid} 个性化已更新({len(qs)} 个问题)。复核:python personalize.py {lid} show")


if __name__ == "__main__":
    main(sys.argv[1:])
