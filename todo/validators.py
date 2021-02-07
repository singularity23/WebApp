from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

def validate_sap_id(value):
    if re.match(r'^[A-Z]{2}-\d{4}$', value):
        return True

def validate_project_number(value):
    if re.match(r'^[A-Z]{2}-[A-Z]{2,3}-\d{3}$', value):
        return True