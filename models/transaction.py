from datetime import datetime
import json
import os
from pathlib import Path

class Transaction:
    TYPE_INCOME = 'income'
    TYPE_EXPENSE = 'expense'

    def __init__(self, transaction_data):
        self.id = transaction_data.get('id')
        self.project_id = transaction_data.get('project_id')
        self.amount = transaction_data.get('amount')
        self.type = transaction_data.get('type')
        self.category = transaction_data.get('category')
        self.description = transaction_data.get('description')
        self.created_by = transaction_data.get('created_by')
        self.created_at = transaction_data.get('created_at')

    @staticmethod
    def _get_storage_path(project_id):
        storage_dir = Path.home() / '.accounting_app' / 'transactions'
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / f'project_{project_id}.json'

    @staticmethod
    def _load_local_transactions(project_id):
        storage_path = Transaction._get_storage_path(project_id)
        if storage_path.exists():
            with open(storage_path, 'r') as f:
                return json.load(f)
        return []

    @staticmethod
    def _save_local_transactions(project_id, transactions):
        storage_path = Transaction._get_storage_path(project_id)
        with open(storage_path, 'w') as f:
            json.dump(transactions, f, indent=2)

    @staticmethod
    def create_transaction(project_id, amount, type, category, description, created_by):
        transaction_data = {
            'id': str(int(datetime.utcnow().timestamp() * 1000)),  # Generate local ID
            'project_id': project_id,
            'amount': amount,
            'type': type,
            'category': category,
            'description': description,
            'created_by': created_by,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Load existing transactions
        transactions = Transaction._load_local_transactions(project_id)
        transactions.append(transaction_data)
        
        # Save updated transactions
        Transaction._save_local_transactions(project_id, transactions)
        return Transaction(transaction_data)

    @staticmethod
    def get_project_transactions(project_id):
        transactions = Transaction._load_local_transactions(project_id)
        return [Transaction(t) for t in transactions]

    @staticmethod
    def get_project_balance(project_id):
        transactions = Transaction._load_local_transactions(project_id)
        balance = 0
        for t in transactions:
            if t['type'] == Transaction.TYPE_INCOME:
                balance += t['amount']
            else:
                balance -= t['amount']
        return balance
