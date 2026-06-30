"""amazon-listing skill 共享工具(自包含 / portable)。

中间层 HTTP + COS 上传(内联,无主项目依赖)+ 字段助手 + 店铺选择 + 安全检查。
配置从 **本 skill 目录的 .env** 或环境变量读(见 .env.example)。
依赖:requests(标准)、qcloud_cos(COS 上传时)、Pillow(A+ 裁图时,在 aplus.py)。
"""
from __future__ import annotations
import json, os, sys, hashlib, urllib.request, urllib.error
from urllib.parse import urlencode

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

# 允许的店铺白名单(env AMAZON_ALLOWED_STORES 逗号分隔可覆盖)
ALLOWED_STORES = set((os.getenv("AMAZON_ALLOWED_STORES") or "main,qifengz,serenorch,bfpeaky").split(","))
DEFAULT_STORE = "main"


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
    if store not in ALLOWED_STORES:
        raise SystemExit(f"[拒绝] 店铺 '{store}' 不在白名单 {sorted(ALLOWED_STORES)};改 env AMAZON_ALLOWED_STORES。")
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
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"success": False, "message": f"HTTP {e.code}", "_status": e.code}
    except urllib.error.URLError as e:
        return {"success": False, "message": f"NETWORK: {e.reason}; 中间层 {BASE} 没起?"}


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
    """本地图/字节 → 腾讯 COS 公网 URL(内容哈希 key,防 URL 缓存)。COS_* 从 env 读。"""
    sid = os.getenv("COS_SECRET_ID"); sk = os.getenv("COS_SECRET_KEY")
    region = os.getenv("COS_REGION"); bucket = os.getenv("COS_BUCKET")
    base = (os.getenv("COS_BASE_URL") or (f"https://{bucket}.cos.{region}.myqcloud.com" if bucket and region else "")).rstrip("/")
    if not all([sid, sk, region, bucket, base]):
        raise RuntimeError("COS 未配全(.env 的 COS_SECRET_ID/COS_SECRET_KEY/COS_REGION/COS_BUCKET[/COS_BASE_URL])")
    data = path_or_bytes if isinstance(path_or_bytes, (bytes, bytearray)) else open(path_or_bytes, "rb").read()
    from qcloud_cos import CosConfig, CosS3Client
    client = CosS3Client(CosConfig(Region=region, SecretId=sid, SecretKey=sk, Scheme="https"))
    key = f"{key_prefix}/{hashlib.sha1(bytes(data)).hexdigest()[:12]}.png"
    client.put_object(Bucket=bucket, Body=bytes(data), Key=key, ContentType="image/png")
    return f"{base}/{key}"


def issues_of(resp: dict) -> tuple[str, list]:
    if not resp.get("success"):
        return ("ERROR", [{"severity": "ERROR", "message": resp.get("message") or resp.get("detail") or "fail"}])
    d = resp.get("data", {}) or {}
    return (d.get("status", ""), d.get("issues", []) or [])
