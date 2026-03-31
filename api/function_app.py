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
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        sql_conn_str = os.getenv("SQL_CONN_STR")

        # 1. OpenAI クライアント（回答生成用のみ使用）
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-02-01")

        # 2. DB接続（前回の「執念のドライバー18対応」を継続）
        final_conn_str = sql_conn_str.replace("17", "18")
        if "TrustServerCertificate" not in final_conn_str:
            final_conn_str += ";TrustServerCertificate=yes;"
        
        conn = pyodbc.connect(final_conn_str)
        cursor = conn.cursor()

        # 3. キーワード検索（LIKE句で部分一致検索）
        # ユーザーの質問から重要な単語を抽出して検索するのが理想ですが、まずは全文検索
        search_query = """
        SELECT TOP 3 content 
        FROM sc300_knowledge 
        WHERE content LIKE ?
        """
        # 質問文の前後を % で囲って、どこかに含まれていればヒットするようにします
        cursor.execute(search_query, (f"%{user_query[:20]}%",)) 
        rows = cursor.fetchall()
        
        # もしヒットしなかったら、とりあえず全件から3件出す（テスト用）
        if not rows:
            cursor.execute("SELECT TOP 3 content FROM sc300_knowledge")
            rows = cursor.fetchall()

        context = "\n".join([row[0] for row in rows])

        # 4. 回答生成（ここは gpt-4o に任せる）
        system_prompt = f"あなたはSC-300講師です。以下の教本知識を基にMermaid図解を交えて日本語で回答して。\n【教本知識】:\n{context}"
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
        )

        return func.HttpResponse(json.dumps({"answer": response.choices[0].message.content}), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(json.dumps({"answer": f"プランAエラー: {str(e)}"}), mimetype="application/json")
