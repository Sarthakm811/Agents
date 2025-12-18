# Updated import to use the classic agents module where AgentExecutor is defined
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
# Updated to use the chat model from `langchain-ollama` which supports tool calling
from langchain_ollama import ChatOllama as Ollama  # Free local model with tool support
import sys

class DomainAwareAgent:
    """VS Code compatible domain enforcement agent"""
    
    def __init__(self, topic: str):
        self.topic = topic
        # Instantiate the Ollama LLM which now implements the required bind_tools method
        self.llm = Ollama(model="mistral:7b")  # Free local model
        
        # Define tools
        self.tools = [
            self.create_domain_check_tool(),
            self.create_terminology_correction_tool()
        ]
        
        # Create agent
        self.agent = self.build_agent()
    
    def create_domain_check_tool(self):
        """Tool to check domain violations"""
        from langchain.tools import tool
        
        @tool
        def check_domain_violations(text: str) -> str:
            """Check if text contains domain-inappropriate terminology"""
            violations = []
            
            # Domain rules (expand as needed)
            if "deep learning" in self.topic.lower():
                healthcare_terms = ["patient", "clinical", "diagnosis", "hospital"]
                for term in healthcare_terms:
                    if term in text.lower():
                        violations.append(term)
            
            if violations:
                return f"DOMAIN VIOLATIONS: {', '.join(violations)}"
            return "No domain violations found."
        
        return check_domain_violations

    def create_terminology_correction_tool(self):
        """Tool to correct domain‑inappropriate terminology.

        The implementation is intentionally simple: it looks for a few
        known healthcare‑specific terms that might appear in a computer‑science
        context and replaces them with more generic alternatives. This keeps the
        example lightweight while demonstrating how a correction tool can be
        wired into the LangChain agent.
        """
        from langchain.tools import tool

        @tool
        def correct_terminology(text: str) -> str:
            """Replace domain‑specific terms with generic equivalents.

            Args:
                text: The input text that may contain inappropriate terms.

            Returns:
                The corrected text.
            """
            corrected = text
            # Simple heuristic replacements for demonstration purposes
            replacements = {
                "patient": "data point",
                "clinical": "experimental",
                "diagnosis": "prediction",
                "hospital": "facility",
            }
            for old, new in replacements.items():
                if old in corrected.lower():
                    # Preserve original casing by using replace with case‑insensitive handling
                    corrected = corrected.replace(old, new)
                    corrected = corrected.replace(old.title(), new.title())
                    corrected = corrected.replace(old.upper(), new.upper())
            return corrected

        return correct_terminology
    
    def build_agent(self):
        """Build the LangChain agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are a domain-aware research assistant analyzing: {self.topic}
            
            DOMAIN RULES:
            1. Never mix terminology from different domains
            2. Always check for domain violations before output
            3. Correct any inappropriate terminology
            
            Current domain: {self.detect_domain(self.topic)}
            """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Bind the tools to the LLM so that the agent can invoke them.
        llm_with_tools = self.llm.bind_tools(self.tools)
        return create_tool_calling_agent(
            llm=llm_with_tools,
            prompt=prompt,
            tools=self.tools
        )
    
    def detect_domain(self, topic):
        """Simple domain detection"""
        topic_lower = topic.lower()
        if "deep learning" in topic_lower or "neural" in topic_lower:
            return "COMPUTER_SCIENCE"
        elif "quantum" in topic_lower:
            return "PHYSICS"
        elif "medical" in topic_lower or "clinical" in topic_lower:
            return "HEALTHCARE"
        else:
            return "GENERAL"
    
    def run(self, query: str):
        """Execute the agent"""
        executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return executor.invoke({"input": query})

# VS Code run configuration
if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "Deep Learning"
    agent = DomainAwareAgent(topic)
    
    # Test with problematic text
    test_text = "Deep learning improves diagnostic accuracy for patient outcomes."
    result = agent.run(f"Check this text for domain violations: {test_text}")
    print(result["output"])