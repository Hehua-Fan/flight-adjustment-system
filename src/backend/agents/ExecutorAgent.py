from autoagentsai import ChatClient

class ExecutorAgent:
    def __init__(self):
        self.client = ChatClient(
            agent_id="agent_1234567890",
            personal_auth_key="sk-proj-1234567890",
            personal_auth_secret="sk-proj-1234567890",
            base_url="https://uat.autoagents.cn"
        )

    def invoke(self, prompt: str):
        content = ""
        for event in self.client.invoke(prompt):
            print(event.content, end="", flush=True)
            content += event.content
        return content
    

if __name__ == "__main__":
    executor_agent = ExecutorAgent()
    response = executor_agent.invoke("Hello, how are you?")
    print(response)