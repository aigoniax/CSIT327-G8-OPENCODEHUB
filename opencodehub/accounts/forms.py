from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """Custom registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )

    # Security Question Fields
    SECURITY_QUESTIONS = [
        ('', 'Select a security question'),
        ('pet', "What is your first pet's name?"),
        ('city', "In what city were you born?"),
        ('school', "What is your elementary school name?"),
        ('color', "What is your favorite color?"),
        ('food', "What is your favorite food?"),
    ]
    
    security_question = forms.ChoiceField(
        choices=SECURITY_QUESTIONS,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    security_answer = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your answer (case-insensitive)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'security_question', 'security_answer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.security_question = self.cleaned_data['security_question']
        user.security_answer = self.cleaned_data['security_answer'].lower().strip()  # Store lowercase and trimmed
        if commit:
            user.save()
        return user

class CustomLoginForm(AuthenticationForm):
    """Custom login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Check if username is actually an email
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                except User.DoesNotExist:
                    pass
            
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise forms.ValidationError("Invalid username/email or password.")
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

class CommentForm(forms.Form):
    """Form for project comments with validation"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Write a comment...',
            'rows': 3,
            'id': 'commentText',
            'style': 'border-radius: 12px;',
            'maxlength': '1000',
        }),
        max_length=1000,
        min_length=3,
        required=True,
        error_messages={
            'required': 'Comment cannot be empty.',
            'min_length': 'Comment must be at least 3 characters long.',
            'max_length': 'Comment is too long (max 1000 characters).',
        }
    )
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        # Check if empty after stripping
        if not content:
            raise forms.ValidationError('Comment cannot be empty.')
        
        # Check minimum length
        if len(content) < 3:
            raise forms.ValidationError('Comment must be at least 3 characters long.')
        
        # Check if only whitespace/special chars
        if not any(c.isalnum() for c in content):
            raise forms.ValidationError('Comment must contain at least one letter or number.')
        
        return content