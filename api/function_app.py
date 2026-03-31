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

        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-02-01")

        # 1. 質問をベクトル化
        embed_res = client.embeddings.create(input=[user_query], model="text-embedding-3-small")
        query_vector = embed_res.data[0].embedding

        # 2. DB接続（ドライバー18を優先し、TrustServerCertificateを追加）
        # 接続文字列の中のドライバーを18に書き換えて試行
        final_conn_str = sql_conn_str.replace("17", "18")
        if "TrustServerCertificate" not in final_conn_str:
            final_conn_str += ";TrustServerCertificate=yes;"
        
        conn = pyodbc.connect(final_conn_str)
        cursor = conn.cursor()

        # 3. ベクトル検索 (テーブル名 sc300_knowledge が存在することを前提)
        search_query = f"""
        SELECT TOP 3 content 
        FROM sc300_knowledge 
        ORDER BY VECTOR_DISTANCE('cosine', CAST(? AS VECTOR(1536)), embedding)
        """
        cursor.execute(search_query, (json.dumps(query_vector),))
        rows = cursor.fetchall()
        context = "\n".join([row[0] for row in rows])

        # 4. 回答生成
        system_prompt = f"あなたはSC-300講師です。以下の知識を基にMermaid図解を交えて回答して。\n【知識】:\n{context}"
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": user_query}]
        )

        return func.HttpResponse(json.dumps({"answer": response.choices[0].message.content}), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(json.dumps({"answer": f"最終エラー: {str(e)}"}), mimetype="application/json", status_code=200)
