"""amazon-listing skill 共享工具(自包含 / portable)。

中间层 HTTP + COS 上传(内联,无主项目依赖)+ 字段助手 + 店铺选择 + 安全检查。
配置从 **本 skill 目录的 .env** 或环境变量读(见 .env.example)。
依赖:requests(标准)、qcloud_cos(COS 上传时)、Pillow(A+ 裁图时,在 aplus.py)。
"""
from __future__ import annotations
import json, os, sys, hashlib, urllib.request, urllib.error
from urllib.parse import urlencode

# 中间层是内网服务:请求**绕过系统代理**(否则挂梯子的机器会把 192.168.x 发给代理导致连不上)
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# --- 载入 .env:优先本 skill 目录(scripts 的上一级),再退 cwd ---
_SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
try:
    from dotenv import load_dotenv
    for p in (os.path.join(_SKILL_DIR, ".env"), os.path.join(os.getcwd(), ".env")):
        if os.path.isfile(p):
            load_dotenv(p, override=False)
except Exception:
    pass

MP = os.getenv("AMAZON_MARKETPLACE_ID", "ATVPDKIKX0DER")   # 默认美国站
STORE = os.getenv("AMAZON_STORE", "main")                  # 当前店铺,默认 main
BASE = os.getenv("AMAZON_MCA_URL", "http://localhost:8000").rstrip("/")
BRAND = os.getenv("AMAZON_BRAND", "Inkelligent")           # 必须用已备案品牌(GTIN 豁免)

# 店铺白名单:**动态取自中间层 /stores**(=真正配了 SP-API 授权的店),
# 中间层挂了才退回内置兜底;env AMAZON_ALLOWED_STORES 显式设置时优先级最高。
# 加新店只需改中间层 .env 的 AMAZON_STORES_JSON 并重启,skill 零改动。
_FALLBACK_STORES = "main,qifengz,serenorch,bfpeaky"
DEFAULT_STORE = "main"


def _allowed_stores() -> set:
    env = (os.getenv("AMAZON_ALLOWED_STORES") or "").strip()
    if env:
        return {s.strip() for s in env.split(",") if s.strip()}
    try:
        req = urllib.request.Request(f"{BASE}/api/v1/amazon/stores",
                                     headers={"Accept": "application/json"})
        with _OPENER.open(req, timeout=8) as r:
            o = json.loads(r.read().decode())
        stores = o.get("data") or []
        if o.get("success") and stores:
            return set(stores)
    except Exception:
        pass
    print(f"[warn] 取不到中间层店铺列表({BASE}),用内置兜底白名单")
    return set(_FALLBACK_STORES.split(","))


def consume_store(argv: list) -> list:
    """取出 `--store <name>`,校验白名单,设当前店铺,打印横幅。返回去掉该 token 的 argv。"""
    global STORE
    out, i, store = [], 0, os.getenv("AMAZON_STORE", DEFAULT_STORE)
    while i < len(argv):
        if argv[i] == "--store" and i + 1 < len(argv):
            store = argv[i + 1].strip(); i += 2; continue
        if argv[i].startswith("--store="):
            store = argv[i].split("=", 1)[1].strip(); i += 1; continue
        out.append(argv[i]); i += 1
    allowed = _allowed_stores()
    # 二维寻址 store@SITE(如 byane@UK):白名单按店名部分校验;站点由中间层解析,
    # 未授权区域中间层会给出清晰报错(缺哪个条目)。白名单里写 byane@UK 则只放行该站点。
    base = store.split("@", 1)[0]
    if store not in allowed and base not in allowed:
        raise SystemExit(f"[拒绝] 店铺 '{store}' 不在授权列表 {sorted(allowed)}"
                         f"(来自中间层 /stores)。新店先在中间层 .env 的 AMAZON_STORES_JSON 注册并重启;"
                         f"临时放行可设 env AMAZON_ALLOWED_STORES。用法:--store 店名[@站点],如 byane@UK。")
    STORE = store
    print(f"[store = {store}]" + ("" if store == DEFAULT_STORE else "  ⚠️ 非默认店!"))
    return out


def Lt(v):
    return [{"value": v, "language_tag": "en_US", "marketplace_id": MP}]


def L(v):
    return [{"value": v, "marketplace_id": MP}]


def api(method: str, path: str, *, params: dict | None = None, body: dict | None = None, timeout: int = 120) -> dict:
    url = f"{BASE}/api/v1/amazon{path}"
    if params:
        url += "?" + urlencode({k: v for k, v in params.items() if v is not None})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"success": False, "message": f"HTTP {e.code}", "_status": e.code}
    except urllib.error.URLError as e:
        return {"success": False, "message": f"NETWORK: {e.reason}; 中间层 {BASE} 连不上——检查:①服务是否在跑 ②本机与服务器是否同网可达(ping) ③系统代理是否劫持内网(本 skill 已绕过,若仍失败多为网络不通)"}


def get_listing(sku: str) -> dict:
    return api("GET", f"/listings/{sku}", params={"store": STORE})


def sku_exists(sku: str) -> bool:
    o = get_listing(sku)
    if o.get("success"):
        return True
    blob = json.dumps(o)
    return "NOT_FOUND" not in blob and "not found" not in blob.lower()


def put_listing(sku: str, product_type: str, attributes: dict, *, requirements: str = "LISTING",
                mode: str | None = None) -> dict:
    body = {"sku": sku, "product_type": product_type, "attributes": attributes, "requirements": requirements}
    if mode:
        body["mode"] = mode
    return api("POST", "/listings", params={"store": STORE}, body=body)


def patch_listing(sku: str, product_type: str, patches: list) -> dict:
    return api("PATCH", f"/listings/{sku}", params={"store": STORE},
               body={"product_type": product_type, "patches": patches})


def upload_image_cos(path_or_bytes, key_prefix: str = "amazon") -> str:
    """本地图/字节 → 中间层 /amazon/images/upload → COS 公网 URL。
    **运营端无需任何 COS 凭证**;COS 在中间层(服务端)持有。"""
    import requests  # 仅上传时用
    data = path_or_bytes if isinstance(path_or_bytes, (bytes, bytearray)) else open(path_or_bytes, "rb").read()
    r = requests.post(f"{BASE}/api/v1/amazon/images/upload", proxies={"http": None, "https": None},
                      files={"file": ("img.png", bytes(data), "image/png")}, timeout=120)
    try:
        o = r.json()
    except Exception:
        raise RuntimeError(f"图片上传失败 HTTP {r.status_code}: {r.text[:150]}")
    if not o.get("success"):
        raise RuntimeError("图片上传失败:" + str(o.get("message") or o.get("detail")))
    return o["data"]["url"]


def issues_of(resp: dict) -> tuple[str, list]:
    if not resp.get("success"):
        return ("ERROR", [{"severity": "ERROR", "message": resp.get("message") or resp.get("detail") or "fail"}])
    d = resp.get("data", {}) or {}
    return (d.get("status", ""), d.get("issues", []) or [])
