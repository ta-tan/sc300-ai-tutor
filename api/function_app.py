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

        # STEP 3: DB 接続テスト（ここが本丸）
        status_log.append("3. DB接続開始...")
        try:
            conn = pyodbc.connect(sql_conn_str)
            status_log.append("OK (Driver 17/18 成功)")
        except Exception as db_e:
            return func.HttpResponse(json.dumps({"answer": f"【DB接続失敗】\nログ: {' -> '.join(status_log)}\nエラー内容: {str(db_e)}"}), mimetype="application/json")

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
