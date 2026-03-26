"""
Test template rendering for submission #26.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.template import Template, Context
from document_tracking.models import Submission

try:
    submission = Submission.objects.select_related('doc_type', 'assigned_section').get(id=26)
    
    print("\n=== TEMPLATE RENDERING TEST ===")
    print(f"Submission: {submission.title}")
    print(f"doc_type object: {submission.doc_type}")
    print(f"doc_type.name: {submission.doc_type.name if submission.doc_type else 'None'}")
    
    # Test template rendering
    template_code = """
    {% if submission.doc_type %}
      {{ submission.doc_type.name }} ({{ submission.doc_type.prefix }})
    {% else %}
      Not specified
    {% endif %}
    """
    
    template = Template(template_code)
    context = Context({'submission': submission})
    rendered = template.render(context)
    
    print(f"\nRendered output: '{rendered.strip()}'")
    print("\n=== TEST COMPLETE ===\n")
    
except Exception as e:
    print(f"\n✗ Error: {e}\n")
    import traceback
    traceback.print_exc()
