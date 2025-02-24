class BaseAgent:
    def answer_question(self, question: str) -> str:
        """Método base que precisa ser implementado nos agentes específicos."""
        raise NotImplementedError("Cada agente precisa implementar sua própria lógica de resposta!")
