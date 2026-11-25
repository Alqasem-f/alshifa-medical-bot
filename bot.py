"""بوت الأسئلة الشائعة لمركز الشفاء الطبي باستخدام Gemini API."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

# تحميل المتغيرات البيئية من ملف .env إن وُجد
load_dotenv()

FAQ_PATH = Path(__file__).parent / "faq.json"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")


def load_faq(path: Path = FAQ_PATH) -> dict[str, Any]:
    """قراءة ملف الأسئلة الشائعة بصيغة JSON."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_system_instruction(faq_data: dict[str, Any]) -> str:
    """بناء تعليمات النظام الصارمة لمنع الاختراع والالتزام بملف الأسئلة فقط."""
    center_name = faq_data["center_name"]
    phone = faq_data["contact_phone"]
    landline = faq_data["landline"]

    faq_lines = []
    for item in faq_data["faqs"]:
        faq_lines.append(f"س{item['id']}: {item['question']}\nج{item['id']}: {item['answer']}")
    faq_text = "\n\n".join(faq_lines)

    return f"""أنت مساعد خدمة العملاء الرسمي لـ «{center_name}» في {faq_data["city"]}.

القواعد الصارمة التي يجب الالتزام بها دائماً دون استثناء:
1. أجب باللغة العربية الواضحة والمهذبة والمختصرة.
2. اعتمد في إجاباتك **حصراً وفقط** على المعلومات الواردة في «ملف الأسئلة الشائعة» أدناه.
3. يُمنع منعاً باتاً اختراع أي معلومة، أو التخمين، أو تقديم أي تشخيص طبي أو وصفة دوائية أو نصيحة طبية غير مذكورة نصاً في الملف.
4. إذا كان سؤال الزائر غير موجود في الملف، أو يطلب استشارة طبية/تشخيصاً/دواءً، أو يسأل عن خدمة أو سعر غير مذكور في الملف، أجب فقط بالصيغة التالية:
   «ما عندي معلومة حول هذا الموضوع، يُرجى التواصل معنا مباشرة على الرقم {phone} أو الهاتف الثابت {landline} لمساعدتك.»
5. لا تذكر للمستخدم كلمة "الملف" أو "النظام"؛ أجب بشكل طبيعي كموظف استقبال للمركز.

--- ملف الأسئلة الشائعة لـ {center_name} ---
{faq_text}
--- نهاية الملف ---
"""


class AlshifaBot:
    """بوت سطر أوامر يجيب عن أسئلة زوار مركز الشفاء الطبي من ملف FAQ فقط."""

    def __init__(self, model: str = DEFAULT_MODEL, faq_path: Path = FAQ_PATH) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "لم يتم العثور على GEMINI_API_KEY. "
                "يرجى إضافته في ملف .env أو كمتغير بيئي قبل التشغيل."
            )

        self.model = model
        self.faq_data = load_faq(faq_path)
        self.system_instruction = build_system_instruction(self.faq_data)
        self.client = genai.Client(api_key=api_key)

    def ask(self, question: str) -> dict[str, Any]:
        """إرسال سؤال للنموذج وإرجاع الرد مع إحصائيات التوكنز."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=question.strip(),
            config=types.GenerateContentConfig(
    system_instruction=self.system_instruction,
    temperature=0.0,
    max_output_tokens=1024,
),
            )
        

        usage = response.usage_metadata
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0

        return {
            "answer": (response.text or "").strip(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }


def run_cli() -> None:
    """تشغيل واجهة سطر الأوامر التفاعلية."""
    try:
        bot = AlshifaBot()
    except ValueError as err:
        print(f"خطأ في الإعداد: {err}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"مرحباً بك في بوت «{bot.faq_data['center_name']}» (النموذج: {bot.model})")
    print("اكتب سؤالك بالعربية، أو اكتب (خروج) للإنهاء.")
    print("=" * 60)

    while True:
        try:
            question = input("\nسؤالك: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nشكراً لتواصلك مع مركز الشفاء الطبي. مع السلامة!")
            break

        if not question:
            continue
        if question.lower() in {"خروج", "exit", "quit", "q"}:
            print("شكراً لتواصلك مع مركز الشفاء الطبي. مع السلامة!")
            break

        try:
            result = bot.ask(question)
            print(f"البوت: {result['answer']}")
        except Exception as exc:
            print(f"حدث خطأ أثناء الاتصال بالنموذج: {exc}", file=sys.stderr)


if __name__ == "__main__":
    run_cli()
