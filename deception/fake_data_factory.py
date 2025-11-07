"""Fake data factory for generating realistic but poisoned data."""

from faker import Faker
from typing import Dict, List, Any


class FakeDataFactory:
    """Factory for generating various types of fake data with tracking."""
    
    def __init__(self):
        self.faker = Faker()
    
    def generate_user_data(self, count: int, tracking_token: str) -> List[Dict]:
        """Generate fake user records."""
        return [{
            "id": i,
            "name": self.faker.name(),
            "email": self.faker.email(),
            "ssn": self.faker.ssn(),
            "credit_card": f"{self.faker.credit_card_number()}_{tracking_token[:4]}",
            "address": self.faker.address(),
            "tracking_token": tracking_token
        } for i in range(count)]
    
    def generate_financial_data(self, count: int, tracking_token: str) -> List[Dict]:
        """Generate fake financial records."""
        return [{
            "transaction_id": self.faker.uuid4(),
            "amount": self.faker.pydecimal(left_digits=5, right_digits=2, positive=True),
            "account": f"{self.faker.bban()}_{tracking_token[:6]}",
            "description": self.faker.bs(),
            "tracking_token": tracking_token
        } for i in range(count)]
