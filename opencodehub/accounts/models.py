from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
import json

class User(AbstractUser):
    """Extended user model for OpenCodeHub"""
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Security Question for Password Reset
    security_question = models.CharField(max_length=200, blank=True, default='')
    security_answer = models.CharField(max_length=200, blank=True, default='')

    def get_profile_picture_url(self):
        """Return profile picture URL or default if none uploaded"""
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/accounts/images/default-profile.svg'

    def get_total_uploads(self):
        """Count total number of uploads (projects + versions) by this user"""
        # Count projects created by user
        projects_count = self.projects.filter(is_deleted=False).count()

        # Count versions created by user across all projects
        versions_count = ProjectVersion.objects.filter(created_by=self).count()

        return projects_count + versions_count

    @staticmethod
    def format_upload_count(count):
        """Format upload count for readability (e.g., 1.2k, 2M)"""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count / 1_000:.1f}k"
        else:
            return str(count)


class Project(models.Model):
    """Model for user projects"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    shared_with = models.ManyToManyField(User, related_name='shared_projects', blank=True)
    share_link = models.UUIDField(editable=False, unique=True, null=True, blank=True)
    allow_collaborators_delete = models.BooleanField(default=True)
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)  # ADD THIS LINE

    def get_next_version_number(self): 
        """Get the next version number for this project"""
        latest = self.versions.order_by('-version_number').first()
        if latest:
            try:
                current = int(latest.version_number.replace('v', ''))
                return f"v{current + 1}"
            except:
                return "v1"
        return "v1"
    
    def __str__(self):
        return self.title
    
    def get_shareable_link(self):
        """Generate the full shareable URL for this project"""
        if not self.share_link:
            self.share_link = uuid.uuid4()
            self.save()
        return f"/share/{self.share_link}/"

class ProjectFile(models.Model):
    """Model for files within projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='project_files/')
    file_type = models.CharField(max_length=50)
    size = models.IntegerField()
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.project.title} - {self.name}"

class ProjectVersion(models.Model):
    """Model for project version history"""
    ACTION_CHOICES = [
        ('created', 'Project Created'),
        ('file_added', 'File Added'),
        ('file_updated', 'File Updated'),
        ('file_deleted', 'File Deleted'),
        ('shared', 'Project Shared'),
        ('comment_added', 'Comment Added'),
        ('manual', 'Manual Save'),
        ('restored', 'Version Restored'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='manual')
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Version file storage
    version_file = models.FileField(upload_to='project_versions/', null=True, blank=True)
    file_size = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=50, blank=True)
    is_latest = models.BooleanField(default=False)
    # Store snapshot of files at this version
    files_snapshot = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['project', 'version_number']
    
    def __str__(self):
        return f"{self.project.title} v{self.version_number}"
    
    def save(self, *args, **kwargs):
        # Auto-mark as latest if it's the first version or explicitly set
        if not self.pk and not ProjectVersion.objects.filter(project=self.project).exists():
            self.is_latest = True
        super().save(*args, **kwargs)
    
    def get_action_display_with_icon(self):
        """Get display text for action"""
        return self.get_action_display()
    
    def create_files_snapshot(self):
        """Create a snapshot of current project files"""
        files_data = []
        for file in self.project.files.all():
            files_data.append({
                'id': file.id,
                'name': file.name,
                'file_url': file.file.url if file.file else None,
                'file_type': file.file_type,
                'size': file.size,
                'uploaded_at': file.uploaded_at.isoformat(),
            })
        self.files_snapshot = {
            'files': files_data,
            'total_files': len(files_data),
            'timestamp': timezone.now().isoformat(),
        }
        self.save()

class SharedProject(models.Model):
    """Model for tracking project sharing with permission levels"""
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Can Edit'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='shared_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_projects_new')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='view')
    shared_at = models.DateTimeField(default=timezone.now)
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects_shared_by')
    
    class Meta:
        unique_together = ['project', 'user']
        ordering = ['-shared_at']
    
    def __str__(self):
        return f"{self.project.title} shared with {self.user.username} ({self.get_permission_display()})"

class Comment(models.Model):
    """Model for project comments"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']  # ✅ DESCENDING ORDER (newest first) - ADD THE MINUS SIGN
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.project.title}"