import requests


class AgentClient:
    def __init__(self):
        self.chat_endpoint = "https://autonome.alt.technology/apex-owfsxk/chat"
        self.session = requests.Session()
        self.session.auth = ("apex", "eUUeBYoizG")

    def send_message(self, message):
        payload = {"message": message}
        try:
            response = self.session.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            print(f"Status code: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error status: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {str(e)}")
            return None


def main():
    agent = AgentClient()
    print("Chat with agent (type 'quit' to exit)")
    print("-" * 50)
    print(f"Connecting to: {agent.chat_endpoint}")

    while True:
        user_message = input("\nYou: ")

        if user_message.lower() in ['quit', 'exit']:
            break

        response = agent.send_message(user_message)

        if response:
            agent_message = response.get('response', str(response))
            print(f"\nAgent: {agent_message}")


if __name__ == "__main__":
    main()