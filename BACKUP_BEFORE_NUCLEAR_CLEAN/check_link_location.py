import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from accounts.models import WorkItemAttachment

s = Submission.objects.get(id=19)
print('Primary folder:', s.primary_folder.id if s.primary_folder else None)
print('File manager folder:', s.file_manager_folder.id if s.file_manager_folder else None)
print('Archive folder:', s.archive_folder.id if s.archive_folder else None)

links = WorkItemAttachment.objects.filter(link_title='fucking ehll')
print(f'\nFound {links.count()} links with title "fucking ehll"')
for l in links:
    print(f'  Link {l.id} in folder {l.folder.id} - URL: {l.link_url}')
