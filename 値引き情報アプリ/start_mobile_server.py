#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スマートフォンでアクセスできるようにする簡易HTTPサーバー起動スクリプト
"""

import http.server
import socketserver
import socket
import webbrowser
import os
import sys

# ポート番号
PORT = 8000

# HTMLファイル名
HTML_FILE = "supermarket_app_map_clickable_list.html"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """カスタムHTTPリクエストハンドラー"""
    def end_headers(self):
        # CORSヘッダーを追加（モバイルアクセス用）
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def get_local_ip():
    """ローカルIPアドレスを取得"""
    try:
        # 一時的なソケットを作成してローカルIPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    # HTMLファイルの存在確認
    if not os.path.exists(HTML_FILE):
        print(f"エラー: {HTML_FILE} が見つかりません。")
        print("まず generate_map.py を実行してHTMLファイルを生成してください。")
        sys.exit(1)
    
    # ローカルIPアドレスを取得
    local_ip = get_local_ip()
    
    # サーバーを起動
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 60)
        print("📱 スマートフォンでアクセスできるサーバーを起動しました！")
        print("=" * 60)
        print()
        print(f"🖥️  パソコン（ローカル）でアクセス:")
        print(f"   http://localhost:{PORT}/{HTML_FILE}")
        print()
        print(f"📱 スマートフォンでアクセス:")
        print(f"   http://{local_ip}:{PORT}/{HTML_FILE}")
        print()
        print("⚠️  重要:")
        print("   1. スマートフォンとパソコンが同じWiFiネットワークに接続されていることを確認してください")
        print("   2. ファイアウォールの警告が出た場合は「許可」を選択してください")
        print("   3. サーバーを停止するには Ctrl+C を押してください")
        print()
        print("=" * 60)
        print()
        
        # ブラウザで自動的に開く（オプション）
        try:
            webbrowser.open(f"http://localhost:{PORT}/{HTML_FILE}")
        except:
            pass
        
        # サーバーを起動（Ctrl+Cで停止）
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()
            print("\nサーバーを停止しました。")

if __name__ == "__main__":
    main()

