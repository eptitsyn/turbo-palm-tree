from openai import OpenAI
client = OpenAI(api_key="sk-RL3NxUnuEFKVOGtInMZ1L5q8l5Tmmq9BlxBNq1GhxnHHSr4t", base_url="https://neuroapi.host/v1")

response = client.responses.create(
    model="gpt-5-nano",
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)
