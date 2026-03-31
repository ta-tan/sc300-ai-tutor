import azure.functions as func
import json
import os
from openai import AzureOpenAI

app = func.FunctionApp()

@app.route(route="ask", auth_level=func.AuthLevel.ANONYMOUS)
def ask(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # 1. 環境変数の取得（設定ミスがあればここでエラーが出る）
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        
        # 2. クライアント初期化
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-01"
        )
        
        # 3. AIに直接質問（DB検索なしのテスト用）
        response = client.chat.completions.create(
            model="gpt-4o",  # ← ここがAzure上の「デプロイ名」と一致しているか超重要！
            messages=[
                {"role": "system", "content": "接続テストです。短く元気に返信して。"},
                {"role": "user", "content": "Azure OpenAIとの接続テストです。SC-300合格への意気込みを教えて！"}
            ]
        )

        answer = response.choices[0].message.content

        return func.HttpResponse(
            json.dumps({"answer": f"【AI接続成功！】\n{answer}"}),
            mimetype="application/json"
        )

    except Exception as e:
        # エラーが起きたら、その内容を画面に返す
        return func.HttpResponse(
            json.dumps({"answer": f"【AI接続失敗】エラー内容: {str(e)}"}),
            mimetype="application/json",
            status_code=200 # 切り分けのため、あえて200で返して画面に文字を出します
        )
