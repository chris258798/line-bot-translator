import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# 讀取環境變數（也就是你記事本裡的那三把鑰匙）
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設定 Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    # 告訴 AI 它的任務是什麼
    prompt = f"""
    你是一個專業的雙向翻譯助理。
    請判斷以下句子的語言：
    如果輸入的是中文，請翻譯成自然口語的印尼文。
    如果輸入的是印尼文，請翻譯成繁體中文。
    請「只」回傳翻譯後的結果，不要加上任何解釋、引言或多餘的文字。

    需要翻譯的句子：
    {user_text}
    """

    try:
        # 呼叫 Gemini 進行翻譯
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
    except Exception as e:
        translated_text = "翻譯發生錯誤，請稍後再試。"

    # 將翻譯結果傳回 LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
