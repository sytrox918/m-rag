from rag.chain import rag_chain

class AnswerService:
    def answer_question(self, question: str, chat_history: list = None):
        return rag_chain.process(question, chat_history)

answer_service = AnswerService()
