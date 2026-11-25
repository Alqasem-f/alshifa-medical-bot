"""سكربت اختبار البوت بـ 5 أسئلة (3 داخل الملف + 2 خارج الملف) وتوليد جدول النتائج."""

from __future__ import annotations

from pathlib import Path
from bot import AlshifaBot

# أسعار الخطة المدفوعة لنموذج gemini-2.5-flash-lite (دولار لكل مليون توكن)
INPUT_PRICE_PER_1M = 0.10
OUTPUT_PRICE_PER_1M = 0.40

TEST_CASES = [
    {
        "question": "متى تفتحون؟ وهل تفتحون يوم الجمعة؟",
        "in_faq": "نعم (في الملف)",
    },
    {
        "question": "كم سعر الكشف عند طبيب الأطفال ومتى يتواجد؟",
        "in_faq": "نعم (في الملف)",
    },
    {
        "question": "وين عنوان المركز بالضبط؟ وهل تقبلون الدفع عبر الكريمي؟",
        "in_faq": "نعم (في الملف)",
    },
    {
        "question": "عندي صداع شديد وحرارة من أمس، إيش الدواء المناسب آخذه؟",
        "in_faq": "لا (خارج الملف - سؤال طبي)",
    },
    {
        "question": "هل تسوون عملية تصحيح نظر بالليزك وكم تكلفتها؟",
        "in_faq": "لا (خارج الملف - خدمة غير موجودة)",
    },
]


def main() -> None:
    bot = AlshifaBot()
    rows = []
    total_input_tokens = 0
    total_output_tokens = 0

    print(f"جاري اختبار البوت باستخدام النموذج: {bot.model} ...\n")

    for idx, case in enumerate(TEST_CASES, start=1):
        res = bot.ask(case["question"])
        answer = res["answer"].replace("\n", " ")
        total_input_tokens += res["input_tokens"]
        total_output_tokens += res["output_tokens"]

        rows.append(
            f"| {idx} | {case['question']} | {case['in_faq']} | {answer} | "
            f"{res['input_tokens']} / {res['output_tokens']} |"
        )
        print(f"[{idx}] س: {case['question']}")
        print(f"    ج: {answer}")
        print(f"    التوكنز: إدخال={res['input_tokens']}, إخراج={res['output_tokens']}\n")

    avg_in = total_input_tokens / len(TEST_CASES)
    avg_out = total_output_tokens / len(TEST_CASES)
    cost_1000 = ((avg_in * 1000) / 1_000_000) * INPUT_PRICE_PER_1M + (
        (avg_out * 1000) / 1_000_000
    ) * OUTPUT_PRICE_PER_1M

    md_lines = [
        "# نتائج اختبار بوت «مركز الشفاء الطبي»",
        "",
        f"- **النموذج المستخدم:** `{bot.model}`",
        f"- **متوسط توكنز الإدخال لكل سؤال:** {avg_in:.0f} توكن",
        f"- **متوسط توكنز الإخراج لكل سؤال:** {avg_out:.0f} توكن",
        f"- **التكلفة التقريبية لكل 1,000 سؤال (الخطة المدفوعة):** `${cost_1000:.4f}` (وعلى الخطة المجانية: `$0.00`)",
        "",
        "| # | السؤال | هل موجود في الملف؟ | رد البوت | التوكنز (إدخال/إخراج) |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ]

    out_path = Path(__file__).parent / "test_results.md"
    out_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"تم حفظ جدول النتائج بنجاح في: {out_path}")


if __name__ == "__main__":
    main()
