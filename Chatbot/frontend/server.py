#!/usr/bin/env python3
"""
간단한 HTTP 서버 - index.html을 기본 페이지로 서빙
"""
import http.server
import socketserver
import os
import webbrowser
from urllib.parse import urlparse

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # CORS 헤더 추가
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # 루트 경로(/)로 접속하면 index.html로 리다이렉트
        parsed_path = self.path.split('?')[0]  # 쿼리 문자열 제거
        
        if parsed_path == '/' or parsed_path == '':
            self.path = '/index.html'
        elif parsed_path.endswith('/'):
            # 디렉토리로 끝나면 index.html 추가
            self.path = parsed_path + 'index.html'
        
        return super().do_GET()
    
    def list_directory(self, path):
        # 디렉토리 리스팅을 비활성화하고 index.html로 리다이렉트
        self.path = '/index.html'
        return self.do_GET()

def main():
    # 현재 디렉토리를 서버 루트로 설정
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"서버가 시작되었습니다!")
        print(f"브라우저에서 http://localhost:{PORT} 로 접속하세요")
        print(f"서버를 중지하려면 Ctrl+C를 누르세요")
        
        # 자동으로 브라우저 열기
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버가 중지되었습니다.")
            httpd.shutdown()

if __name__ == "__main__":
    main()

