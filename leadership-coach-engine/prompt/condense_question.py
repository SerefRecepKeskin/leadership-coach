from llama_index.core.prompts import PromptTemplate

CONDENSE_QUESTION_PROMPT = PromptTemplate("""
    Verilen konuşma geçmişi ve yeni bir soru göz önüne alındığında, soruyu kendi içinde anlamlı ve özlü bir şekilde yeniden ifade et.
    Orijinal anlamı koru ve gerektiğinde ilgili bağlamı dahil et.
    Giriş dili ne olursa olsun yeniden ifade edilmiş soruyu HER ZAMAN Türkçe olarak sağla.

    Sohbet Geçmişi:
    {chat_history}

    Yeni Soru:
    {question}

    Yeniden İfade Edilmiş Soru (Türkçe):
    """
)