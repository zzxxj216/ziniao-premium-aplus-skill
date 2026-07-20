# -*- coding: utf-8 -*-
"""etsy-listing skill 共享工具(自包含 / portable)。

中间层 /api/v1/etsy HTTP 封装:JSON 调用走 urllib(绕系统代理),
图片/视频 multipart 上传走 requests(trust_env=False 同样绕代理)。
配置从本 skill 目录的 .env 或环境变量读(只需 AMAZON_MCA_URL 一项)。
依赖:requests、python-dotenv(与 amazon-listing 相同,不新增)。
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error
from urllib.parse import urlencode

# 中间层是内网服务:请求绕过系统代理(挂梯子的机器会把内网 IP 发给代理导致连不上)
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

_SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
try:
    from dotenv import load_dotenv
    for p in (os.path.join(_SKILL_DIR, ".env"), os.path.join(os.getcwd(), ".env")):
        if os.path.isfile(p):
            load_dotenv(p, override=False)
except Exception:
    pass

_BASE_CONFIGURED = bool(os.getenv("AMAZON_MCA_URL") or os.getenv("TKSHOP_SERVER_URL"))
BASE = os.getenv("AMAZON_MCA_URL", os.getenv("TKSHOP_SERVER_URL", "http://192.168.110.227:8000")).rstrip("/")


def api(method: str, path: str, *, params=None, body=None, timeout=300) -> dict:
    """中间层 /api/v1/etsy{path};返回中间层统一 ApiResponse dict。"""
    url = f"{BASE}/api/v1/etsy{path}"
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
            return {"success": False, "message": f"HTTP {e.code}"}
    except urllib.error.URLError as e:
        return {"success": False, "message": f"NETWORK: {e.reason}(中间层 {BASE} 没起?)"}


def upload_file(path: str, file_path: str, *, params=None, timeout=600) -> dict:
    """multipart 上传本地文件到中间层(图片/视频)。"""
    import requests
    s = requests.Session()
    s.trust_env = False                     # 绕系统代理,同 _OPENER
    url = f"{BASE}/api/v1/etsy{path}"
    with open(file_path, "rb") as f:
        r = s.post(url, params={k: v for k, v in (params or {}).items() if v is not None},
                   files={"file": (os.path.basename(file_path), f)}, timeout=timeout)
    try:
        return r.json()
    except Exception:
        return {"success": False, "message": f"HTTP {r.status_code}: {r.text[:200]}"}


def die_if_failed(o: dict, what: str):
    if not o.get("success"):
        raise SystemExit(f"[失败] {what}:{o.get('message') or o.get('detail')}")
    return o.get("data")


def set_personalization(listing_id, payload: dict) -> dict:
    """设置个性化问题;中间层若是旧版 schema(422 校验挡住)自动降级走 /call 透传。"""
    o = api("POST", f"/listings/{listing_id}/personalization", body=payload)
    if o.get("success"):
        return o
    det = str(o.get("detail") or o.get("message") or "")
    if "string_type" in det or "'missing'" in det or "Field required" in det:
        shop = api("GET", "/shop").get("data") or {}
        sid = shop.get("shop_id")
        if sid:
            return api("POST", "/call", body={
                "method": "POST",
                "path": f"/shops/{sid}/listings/{listing_id}/personalization",
                "params": {"supports_multiple_personalization_questions": "true"},
                "body": payload})
    return o
