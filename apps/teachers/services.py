import pandas as pd
import secrets
import string
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class TeacherImportService:

    def __init__(self, file_path):
        self.file_path = file_path
        self.errors = []
        self.created_count = 0
        self.updated_count = 0

    def generate_password(self, length=10):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def process(self):
        df = pd.read_csv(self.file_path)

        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    self._process_row(row, index + 2)
            except Exception as e:
                self.errors.append(f"Row {index + 2}: {str(e)}")

        return {
            'created': self.created_count,
            'updated': self.updated_count,
            'errors': self.errors,
        }

    def _process_row(self, row, row_number):
        first_name = str(row.get('first_name', '')).strip()
        last_name = str(row.get('last_name', '')).strip()
        email = str(row.get('email', '')).strip()
        phone = str(row.get('phone', '')).strip()

        if not first_name or not email:
            self.errors.append(f"Row {row_number}: Missing first_name or email")
            return

        username = email
        user = User.objects.filter(email=email).first()

        if user:
            user.first_name = first_name
            user.last_name = last_name
            user.phone = phone
            user.save()
            self.updated_count += 1
        else:
            password = self.generate_password()
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='teacher',
                phone=phone,
                must_change_password=True,
            )
            self.created_count += 1