class MockAggregatorAdapter:
    def fetch_state_space(self):
        return {"mocked": True, "lights_on": True, "machines": [], "users_in_space": []}

    def generate_telegram_connect_token(self, user_id):
        return f"mock-token-{user_id}"

    def disconnect_telegram(self, user_id):
        pass

    def onboard_signal(self, user_id):
        pass

    def notification_test(self, user_id):
        pass

    def checkout(self, user_id):
        pass

    def get_chores(self):
        return {"chores": ["mocked-chore-1", "mocked-chore-2"]}
