import azure.functions as func
import json
import os
import pyodbc
from openai import AzureOpenAI

app = func.FunctionApp()

@app.route(route="ask", auth_level=func.AuthLevel.ANONYMOUS)
def ask(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # 1. 環境設定の読み込み
        req_body = req.get_json()
        user_query = req_body.get('question', '')
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        sql_conn_str = os.getenv("SQL_CONN_STR")

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-01"
        )

        # 2. 質問をベクトル化（Embedding）
        # ここでユーザーの質問を数字の羅列に変え、DB検索の準備をします
        embed_res = client.embeddings.create(input=[user_query], model="text-embedding-3-small")
        query_vector = embed_res.data[0].embedding

        # 3. Azure SQL Database への接続（ドライバー 18/17 自動切換）
        try:
            conn = pyodbc.connect(sql_conn_str)
        except:
            # 18でエラーが出た場合は17に書き換えてリトライ
            conn = pyodbc.connect(sql_conn_str.replace("18", "17"))
        
        cursor = conn.cursor()

        # 4. ベクトル検索（RAG）の実行
        # 教本データから、質問に最も近い情報を上位3件取得します
        search_query = f"""
        SELECT TOP 3 content 
        FROM sc300_knowledge 
        ORDER BY VECTOR_DISTANCE('cosine', CAST(? AS VECTOR(1536)), embedding)
        """
        cursor.execute(search_query, (json.dumps(query_vector),))
        rows = cursor.fetchall()
        context = "\n".join([row[0] for row in rows])

        # 5. AIによる最終回答の生成
        # DBから取得した「知識（context）」を元に回答させます
        system_prompt = f"""
        あなたはSC-300試験の専門講師です。
        以下の【参考知識】のみに基づいて回答してください。
        回答には必ずMermaid記法（graph TDなど）を使った図解を含めてください。
        
        【参考知識】:
        {context}
        """

        response = client.chat.completions.create(
            model="gpt-4o", # 先ほど作成したデプロイ名に合わせてください
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
        )

        answer = response.choices[0].message.content

        return func.HttpResponse(
            json.dumps({"answer": answer}),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"answer": f"エラーが発生しました: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
