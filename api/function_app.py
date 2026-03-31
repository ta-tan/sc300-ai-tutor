import azure.functions as func
import json
import os
from openai import AzureOpenAI
import pyodbc

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 環境変数の取得（後でAzure Portalで設定します）
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
SQL_CONN_STR = os.getenv("SQL_CONN_STR")

@app.route(route="ask", methods=["POST"])
def ask(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        user_query = req_body.get('text')

        # 1. OpenAIクライアントの初期化
        client = AzureOpenAI(
            azure_endpoint=OPENAI_ENDPOINT,
            api_key=OPENAI_KEY,
            api_version="2024-02-01"
        )
        
        # 2. 質問のベクトル化 (Embedding)
        emb_res = client.embeddings.create(input=[user_query], model="text-embedding-3-small")
        q_vector = emb_res.data[0].embedding
        vector_str = str(q_vector)

        # 3. Azure SQLでのベクトル検索 (RAG)
        # ドライバー 18 と 17 両方を試す安全な接続方法
        try:
            conn = pyodbc.connect(SQL_CONN_STR)
        except:
            # 18でダメなら17に置換してリトライ
            alt_conn_str = SQL_CONN_STR.replace("18", "17")
            conn = pyodbc.connect(alt_conn_str)
            
        cursor = conn.cursor()
        
        # コサイン類似度で知識DBから上位3件を取得
        cursor.execute(f"""
            SELECT TOP 3 content FROM SC300_Knowledge 
            ORDER BY VECTOR_DISTANCE('cosine', CAST(? AS VARBINARY(8000)), embedding)
        """, (vector_str,))
        
        context = "\n".join([row[0] for row in cursor.fetchall()])
        conn.close()

        # 4. 回答生成 (プロンプト)
        messages = [
            {"role": "system", "content": "あなたはSC-300（Microsoft Identity and Access Administrator）の専門講師です。参考情報をベースに回答し、フローや構造については必ずmermaid.js形式の図解を含めてください。"},
            {"role": "user", "content": f"【参考情報】\n{context}\n\n【質問】\n{user_query}"}
        ]
        
        chat_res = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        return func.HttpResponse(
            json.dumps({"answer": chat_res.choices[0].message.content}),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
