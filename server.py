#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LegalReader 本地后端
====================
- 托管前端 index.html
- 代理 DeepSeek API（解决浏览器 CORS 限制 + API key 本地化不暴露）
- 管理配置（config.json，与程序同目录）

零第三方依赖，仅用 Python 标准库。
兼容两种运行方式：
  1) 源码运行：python server.py
  2) PyInstaller 打包：single exe（资源走 sys._MEIPASS，配置走 exe 同目录）
"""

import http.server
import json
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

HOST = "127.0.0.1"
PORT = 8721

DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.deepseek.com/chat/completions",
    "model": "deepseek-chat",
    "temperature": 0.3,
    "courtlistener_token": "",
    "depth": "standard",
}


def app_dir():
    """可写目录：配置/日志放这里（exe 同目录 或 脚本同目录）"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def static_dir():
    """只读静态资源目录（打包后为解包临时目录）"""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(app_dir(), "config.json")


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ==================== 引注解析与真实数据库查询 ====================

UA = "LegalReader/0.2"


def http_get_json(url, timeout=15):
    """GET JSON，带 User-Agent（Crossref 等要求）"""
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def direct_url(ctype, text):
    """唯一编号类引注的直接精确 URL（无需查询，编号即定位）"""
    if ctype == "celex":
        return "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:" + urllib.parse.quote(text)
    if ctype == "ecli":
        return "https://curia.europa.eu/juris/liste.jsf?ecli=" + urllib.parse.quote(text)
    if ctype == "uk_case":
        return "https://www.bailii.org/cgi-bin/lucy_search_1.cgi?query=" + urllib.parse.quote(text)
    if ctype in ("eu_reg", "eu_article"):
        return "https://eur-lex.europa.eu/search.html?text=" + urllib.parse.quote(text)
    if ctype == "us_code":
        import re
        m = re.search(r"(\d{1,2})\s+U\.?S\.?C\.?[\s§]*(?:[^0-9]*?)(\d{1,4}[a-z]?(?:\([a-z0-9]+\))?(?:-\d+)?)", text, re.I)
        if m:
            sec = m.group(2).replace("(", "").replace(")", "")
            return "https://www.law.cornell.edu/uscode/text/" + m.group(1) + "/" + sec
    return None


def courtlistener_lookup(text, token):
    """用 CourtListener citation-lookup API 精确解析判例引注"""
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Token " + token)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data or not isinstance(data, list):
        return None
    item = data[0]
    if item.get("status") != 200:
        return None
    clusters = item.get("clusters") or []
    if not clusters:
        return None
    c = clusters[0]
    url_path = c.get("absolute_url") or ""
    return {
        "title": c.get("caseName") or c.get("caseNameFull") or text,
        "court": ((c.get("docket") or {}).get("court") or ""),
        "year": (c.get("dateFiled") or "")[:4],
        "url": "https://www.courtlistener.com" + url_path,
        "source": "CourtListener 精确验证",
        "type": "case",
        "verified": "verified",
    }


def resolve_case(text, token=None):
    """判例 → CourtListener 精确 lookup（有 token）或搜索回退"""
    if token:
        try:
            r = courtlistener_lookup(text, token)
            if r:
                return r
        except Exception:
            pass
    q = urllib.parse.quote_plus(text)
    return {
        "title": text,
        "url": "https://www.courtlistener.com/?q=" + q,
        "source": "CourtListener 判例库",
        "type": "case",
        "verified": "search",
    }


def resolve_academic(text):
    """论文/著作 → Crossref（DOI）+ Google Books"""
    q = urllib.parse.quote_plus(text)
    # 先 Crossref（学术论文）
    try:
        cr = http_get_json("https://api.crossref.org/works?query.bibliographic=%s&rows=3" % q)
        items = (cr.get("message") or {}).get("items") or []
        if items:
            it = items[0]
            title = (it.get("title") or [text])[0] if it.get("title") else text
            authors = ", ".join((a.get("family") or "") for a in (it.get("author") or [])[:3])
            year = ""
            for k in ("published-print", "published-online", "issued"):
                dp = (it.get(k) or {}).get("date-parts")
                if dp and dp[0]:
                    year = str(dp[0][0])
                    break
            doi = it.get("DOI")
            url = ("https://doi.org/" + doi) if doi else (it.get("URL") or "")
            return {
                "title": title,
                "authors": authors,
                "year": year,
                "url": url,
                "source": "Crossref（DOI）",
                "type": "article",
                "verified": "verified",
            }
    except Exception:
        pass
    # 再 Open Library（著作，开放图书目录）
    try:
        ol = http_get_json("https://openlibrary.org/search.json?q=%s&limit=3" % q)
        docs = ol.get("docs") or []
        if docs:
            doc = docs[0]
            key = doc.get("key") or ""
            return {
                "title": doc.get("title") or text,
                "authors": ", ".join((doc.get("author_name") or [])[:3]),
                "year": str(doc.get("first_publish_year") or ""),
                "url": ("https://openlibrary.org" + key) if key else "",
                "source": "Open Library（互联网档案馆）",
                "type": "book",
                "verified": "verified",
            }
    except Exception:
        pass
    return {"title": text, "url": "https://www.google.com/search?q=" + q, "source": "Google", "type": "other", "verified": "unverified"}


def resolve_citation(text, ctype, token=None):
    """统一入口：解析单个引注，返回结构化结果"""
    try:
        u = direct_url(ctype, text)
        if u:
            return {"text": text, "type": ctype, "title": text, "url": u, "source": "官方数据库", "direct": True, "verified": "exact"}
        if ctype in ("us_case", "case_name"):
            r = resolve_case(text, token)
            r["text"] = text
            return r
        if ctype in ("article", "book", "other", "journal", "paper"):
            r = resolve_academic(text)
            r["text"] = text
            return r
        return {"text": text, "type": ctype, "title": text,
                "url": "https://www.google.com/search?q=" + urllib.parse.quote_plus(text),
                "source": "Google", "type": "other", "verified": "unverified"}
    except Exception as e:
        return {"text": text, "type": ctype, "error": str(e)}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    # ---- 响应辅助 ----
    def _send_bytes(self, data, code=200, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, obj, code=200):
        self._send_bytes(json.dumps(obj, ensure_ascii=False).encode("utf-8"), code)

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except Exception:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    # ---- CORS 预检 ----
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ---- GET ----
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._serve_index()
        elif path == "/api/health":
            self._send_json({"ok": True, "version": "0.2.0"})
        elif path == "/api/config":
            cfg = load_config()
            self._send_json({
                "has_key": bool(cfg.get("api_key")),
                "has_courtlistener_token": bool(cfg.get("courtlistener_token")),
                "model": cfg.get("model"),
                "base_url": cfg.get("base_url"),
                "temperature": cfg.get("temperature", 0.3),
                "depth": cfg.get("depth", "standard"),
            })
        else:
            self._send_json({"error": "not_found"}, 404)

    def _serve_index(self):
        p = os.path.join(static_dir(), "index.html")
        try:
            with open(p, "rb") as f:
                data = f.read()
        except Exception as e:
            self._send_json({"error": "index_not_found", "message": str(e)}, 500)
            return
        self._send_bytes(data, 200, "text/html; charset=utf-8")

    # ---- POST ----
    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/config":
            self._handle_config()
        elif path == "/api/chat":
            self._handle_chat()
        elif path == "/api/citations":
            self._handle_citations()
        else:
            self._send_json({"error": "not_found"}, 404)

    def _handle_config(self):
        body = self._read_body()
        cfg = load_config()
        if "api_key" in body:
            cfg["api_key"] = (body.get("api_key") or "").strip()
        if "courtlistener_token" in body:
            cfg["courtlistener_token"] = (body.get("courtlistener_token") or "").strip()
        if "base_url" in body and body.get("base_url"):
            cfg["base_url"] = body["base_url"].strip()
        if "model" in body and body.get("model"):
            cfg["model"] = body["model"].strip()
        if "temperature" in body:
            try:
                cfg["temperature"] = float(body["temperature"])
            except Exception:
                pass
        if "depth" in body and body.get("depth"):
            cfg["depth"] = body["depth"].strip()
        save_config(cfg)
        self._send_json({
            "has_key": bool(cfg.get("api_key")),
            "has_courtlistener_token": bool(cfg.get("courtlistener_token")),
            "model": cfg.get("model"),
            "base_url": cfg.get("base_url"),
            "temperature": cfg.get("temperature", 0.3),
            "depth": cfg.get("depth", "standard"),
        })

    def _handle_chat(self):
        body = self._read_body()
        cfg = load_config()
        api_key = cfg.get("api_key", "")
        if not api_key:
            self._send_json({"error": "no_api_key", "message": "尚未配置 API Key"}, 400)
            return

        base_url = cfg.get("base_url") or DEFAULT_CONFIG["base_url"]
        model = body.get("model") or cfg.get("model") or DEFAULT_CONFIG["model"]
        messages = body.get("messages", [])
        temperature = body.get("temperature", cfg.get("temperature", 0.3))
        max_tokens = int(body.get("max_tokens", 8192))
        response_format = body.get("response_format")
        stream = bool(body.get("stream", False))

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        # deepseek-reasoner 不支持 temperature / response_format；流式时不加 response_format（靠 prompt 保证 JSON）
        if model != "deepseek-reasoner":
            if temperature is not None:
                payload["temperature"] = temperature
            if response_format and not stream:
                payload["response_format"] = response_format

        req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(base_url, data=req_body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", "Bearer " + api_key)

        try:
            if stream:
                self._stream_chat(req)
            else:
                with urllib.request.urlopen(req, timeout=600) as resp:
                    data = resp.read()
                    ctype = resp.headers.get("Content-Type", "application/json")
                    self._send_bytes(data, resp.status, ctype)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            ctype = e.headers.get("Content-Type", "application/json")
            self._send_bytes(err_body, e.code, ctype)
        except urllib.error.URLError as e:
            self._send_json({"error": "network", "message": "无法连接模型服务：" + str(e.reason)}, 502)
        except Exception as e:
            self._send_json({"error": "proxy_error", "message": str(e)}, 502)

    def _stream_chat(self, req):
        """流式转发 DeepSeek SSE（逐块透传）"""
        try:
            resp = urllib.request.urlopen(req, timeout=600)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self._send_bytes(err_body, e.code, e.headers.get("Content-Type", "application/json"))
            return
        except urllib.error.URLError as e:
            self._send_json({"error": "network", "message": "无法连接模型服务：" + str(e.reason)}, 502)
            return
        except Exception as e:
            self._send_json({"error": "proxy_error", "message": str(e)}, 502)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with resp:
            while True:
                chunk = resp.read(2048)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                except Exception:
                    break

    def _handle_citations(self):
        body = self._read_body()
        cites = body.get("citations") or []
        cfg = load_config()
        token = (cfg.get("courtlistener_token") or "").strip()
        results = [resolve_citation(c.get("text", ""), c.get("type", "other"), token) for c in cites]
        self._send_json({"results": results})


def open_browser():
    def _open():
        try:
            webbrowser.open("http://%s:%d/" % (HOST, PORT))
        except Exception:
            pass
    threading.Timer(0.8, _open).start()


def main():
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print("=" * 48)
    print("  LegalReader 法律文件解读工具 已启动")
    print("  访问地址: http://%s:%d/" % (HOST, PORT))
    print("  关闭本窗口即退出程序")
    print("=" * 48)
    open_browser()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
