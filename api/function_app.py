import azure.functions as func
import json
import os
import pyodbc
from openai import AzureOpenAI

app = func.FunctionApp()

@app.route(route="ask", auth_level=func.AuthLevel.ANONYMOUS)
def ask(req: func.HttpRequest) -> func.HttpResponse:
    status_log = []
    try:
        # STEP 1: 環境変数の読み込みチェック
        status_log.append("1. 環境変数読み込み開始...")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        sql_conn_str = os.getenv("SQL_CONN_STR")
        
        if not all([endpoint, api_key, sql_conn_str]):
            return func.HttpResponse(json.dumps({"answer": "【エラー】環境変数が空です。Azureの「構成」を確認してください。"}), mimetype="application/json")
        status_log.append("OK")

        # STEP 2: OpenAI 接続テスト
        status_log.append("2. OpenAI接続開始...")
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-02-01")
        # 疎通確認のためだけに軽く投げる
        client.models.list()
        status_log.append("OK")

        ## 3. DB 接続テスト（ドライバーのバージョンを柔軟に探す）
        status_log.append("3. DB接続開始...")
        
        # 試行するドライバーのリスト
        drivers = [
            '{ODBC Driver 18 for SQL Server}',
            '{ODBC Driver 17 for SQL Server}'
        ]
        
        conn = None
        last_error = ""
        
        for driver in drivers:
            try:
                # 接続文字列の Driver 部分を動的に差し替え
                current_conn_str = sql_conn_str.replace('{ODBC Driver 17 for SQL Server}', driver)
                # Driver 18 の場合は証明書チェックを無視する設定を追加（これ重要）
                if "18" in driver:
                    current_conn_str += ";TrustServerCertificate=yes;"
                
                conn = pyodbc.connect(current_conn_str)
                status_log.append(f"OK ({driver} で成功)")
                break
            except Exception as e:
                last_error = str(e)
                continue

        if not conn:
            return func.HttpResponse(
                json.dumps({"answer": f"【DB接続失敗】全ドライバーを試しましたが全滅しました。\n最終エラー: {last_error}"}), 
                mimetype="application/json"
            )

        # すべて突破した場合
        return func.HttpResponse(
            json.dumps({"answer": "【全開通！】通信はすべて成功しています。次はSQLのテーブル定義を確認しましょう。"}),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"answer": f"【想定外のエラー】\nログ: {' -> '.join(status_log)}\nエラー: {str(e)}"}),
            mimetype="application/json"
        )
