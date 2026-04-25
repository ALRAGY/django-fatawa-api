import os
import glob
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# السكوب المطلوب يتيح لك جلب التعليقات، الرد عليها، وحذفها
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def main():
    print("=== أداة تفويض يوتيوب (YouTube OAuth) ===")
    
    # البحث عن ملف الجيسون الخاص بك في مجلد الصندوق المشترك أو المجلد الرئيسي
    possible_files = glob.glob("../shared_inbox/client_secret*.json") + glob.glob("client_secret*.json") + glob.glob("../client_secret*.json")
    
    if not possible_files:
        print("❌ خطأ: لم يتم العثور على ملف client_secret.")
        print("تأكد أن الملف يبدأ بكلمة client_secret وأنه موجود في المشروع.")
        return
        
    client_file = possible_files[0]
    print(f"تم العثور على ملف الـ Secret: {client_file}")

    flow = InstalledAppFlow.from_client_secrets_file(client_file, SCOPES)
    # سيفتح المتصفح لتسجيل الدخول (استخدم بورت 8080 لتجنب بعض مشاكل جوجل إذا تطلب الأمر، أو 0 لمنفذ عشوائي)
    credentials = flow.run_local_server(port=8080)

    print("\n\n✅✅✅ تم تسجيل الدخول بنجاح! ✅✅✅\n")
    print("انسخ كل هذا النص (JSON) وأرسله لي في المحادثة لكي أبرمج المحرك لاحقاً:\n")
    token_data = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret
    }
    
    print(json.dumps(token_data, indent=4))
    
    # حفظه مؤقتاً أيضاً
    with open("youtube_tokens.json", "w") as f:
        json.dump(token_data, f, indent=4)
    print("\n(ملاحظة لك: تم حفظ نسخة من هذه البيانات في ملف youtube_tokens.json للرجوع إليها)")

if __name__ == '__main__':
    main()
