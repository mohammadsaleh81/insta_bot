from openai import OpenAI
import os
import json


client = OpenAI(
    base_url='https://api.avalai.ir/v1',
    api_key='aa-WRHuYP6rJKdnod0PZ7QxUgaCJrbUUuBX4Mn7L6vSAbomoIiY'
)

response = client.chat.completions.create(
    model="gpt-4o-mini",  # یا اسنپ‌شات خاص مانند gpt-4o-mini-2024-07-18
    messages=[
        {"role": "system", "content": "شما یک ربات چت پشتیبانی مشتری هستید."},
        {"role": "user", "content": "سیاست‌های بازگشت شما چیست؟"},
    ],
)

print(response.choices[0].message.content)
# #
# with open('aval.json', 'w') as f:
#     j = json.dumps(response, indent=4, ensure_ascii=False)
#     f.write(response.json())



OPENAI_API_KEY='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'
OPENAI_BASE_URL='https://openrouter.ai/api/v1'
#
#
# client = OpenAI(
#     base_url=OPENAI_BASE_URL,
#     api_key=OPENAI_API_KEY
# )
# open_response = client.chat.completions.create(
#     model="deepseek/deepseek-r1:free",
#     messages=[
#         {"role": "system", "content": "شما یک ربات چت پشتیبانی مشتری هستید."},
#         {"role": "user", "content": "سیاست‌های بازگشت شما چیست؟"},
#     ],
#     temperature=0.7,
#     max_tokens=2000,
#     timeout=120
# )
#
#
# with open('open.json', 'w') as f:
#     j = json.dumps(open_response, indent=4, ensure_ascii=False)
#     f.write(j)
#
#
