import azure.functions as func
import json

app = func.FunctionApp()

@app.route(route="ask", auth_level=func.AuthLevel.ANONYMOUS)
def ask(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"answer": "通信成功！DBとAIの設定をチェックしましょう。"}),
        mimetype="application/json"
    )
