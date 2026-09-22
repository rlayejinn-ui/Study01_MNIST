# -*- coding: utf-8 -*-
"""
웹 버전을 내 컴퓨터에서 확인하기 위한 간단한 정적 파일 서버

실행 방법 (web_version 폴더 기준):
    python 개발서버.py
그다음 브라우저에서 http://localhost:8000 을 엽니다.
검사 페이지: http://localhost:8000/tests/검사.html

index.html 을 파일로 직접 열면(file://) 브라우저 보안 정책 때문에
모듈과 가중치를 불러올 수 없으므로 이 서버로 여세요.
Windows 에서는 .js 의 MIME 형식이 잘못 잡히는 경우가 있어 직접 지정합니다.
"""

import functools
import http.server
import os

포트 = 8000
폴더 = os.path.dirname(os.path.abspath(__file__))


class 처리기(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".bin": "application/octet-stream",
    }

    def end_headers(self):
        # 코드를 고친 뒤 새로고침하면 바로 반영되도록 캐시를 끕니다.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    서버 = http.server.ThreadingHTTPServer(("127.0.0.1", 포트), functools.partial(처리기, directory=폴더))
    print(f"웹 버전 개발 서버 실행 중: http://localhost:{포트}  (끝내려면 Ctrl+C)")
    서버.serve_forever()


if __name__ == "__main__":
    main()
