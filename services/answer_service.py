from rag.chain import rag_chain

class AnswerService:
    def answer_question(self, question: str):
        return rag_chain.process(question)

answer_service = AnswerService()
