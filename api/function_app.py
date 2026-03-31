import azure.functions as func
import json
import os
import pyodbc
from openai import AzureOpenAI

app = func.FunctionApp()

@app.route(route="ask", auth_level=func.AuthLevel.ANONYMOUS)
def ask(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        user_query = req_body.get('question', '')
        
        # 環境変数取得
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        sql_conn_str = os.getenv("SQL_CONN_STR")

        # 1. 接続文字列のクレンジング（本気設定）
        # ドライバーを18に強制し、証明書を信頼し、タイムアウトを明示的に短く(10秒)設定
        conn_str = sql_conn_str.replace("{ODBC Driver 17 for SQL Server}", "{ODBC Driver 18 for SQL Server}")
        if "TrustServerCertificate" not in conn_str:
            conn_str += ";TrustServerCertificate=yes;"
        if "LoginTimeout" not in conn_str:
            conn_str += ";LoginTimeout=10;" # 長すぎる待機をカット

        # 2. DB接続（ここで落ちたらエラーを即座に返す）
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
        except Exception as conn_e:
            return func.HttpResponse(json.dumps({"answer": f"【DB接続致命的エラー】: {str(conn_e)}"}), mimetype="application/json")

        # 3. 簡易キーワード検索
        cursor.execute("SELECT TOP 3 content FROM sc300_knowledge WHERE content LIKE ?", (f"%{user_query}%",))
        rows = cursor.fetchall()
        context = "\n".join([row[0] for row in rows]) if rows else "該当知識なし"

        # 4. 回答生成
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-02-01")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"あなたはSC-300講師です。知識に基づいて回答して。\n【知識】:{context}"},
                {"role": "user", "content": user_query}
            ]
        )

        return func.HttpResponse(json.dumps({"answer": response.choices[0].message.content}), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(json.dumps({"answer": f"本気デバッグエラー: {str(e)}"}), mimetype="application/json")
        
# 質問文からキーワードだけ抜く（簡易版）
keyword = "条件付きアクセス" 
cursor.execute("SELECT TOP 3 content FROM sc300_knowledge WHERE content LIKE ?", (f"%{keyword}%",))
