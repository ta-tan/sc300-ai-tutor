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

        # 4. 回答生成（図解強制・DB知識優先モード）
        system_prompt = f"""
あなたはSC-300（Microsoft Identity and Access Administrator）の専門講師です。
提供された【教本知識】を唯一の根拠として回答してください。

### 回答ルール:
1. プロセス、手順、構成に関する質問には、必ず Mermaid形式の `graph TD` を用いて図解してください。
2. 図解の後に、教本の重要ポイントを簡潔に箇条書きで補足してください。
3. 【教本知識】に該当データがない場合は、自分の知識で補完せず「DBに該当データなし」と報告してください。

【教本知識】:
{context}
"""
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-02-01")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
        )

        return func.HttpResponse(json.dumps({"answer": response.choices[0].message.content}), mimetype="application/json")
