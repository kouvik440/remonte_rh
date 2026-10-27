from llmlingua import PromptCompressor

# Version la plus simple (LLMLingua-2 recommandée)
compressor = PromptCompressor(
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    use_llmlingua2=True,
    device_map="cpu"          # mets "cuda" si tu as une carte NVIDIA
)

prompt = """
la barre des liens est presque pareil pour toute les apllication django en react Utilise design-taste-frontend. pour ameliorer Pas de style IA générique mais quelque chose doriginal 
"""

result = compressor.compress_prompt(prompt, rate=0.5)

print("Prompt compressé :")
print(result["compressed_prompt"])
print("\nTokens originaux :", result["origin_tokens"])
print("Tokens compressés :", result["compressed_tokens"])