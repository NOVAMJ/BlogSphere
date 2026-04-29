from django import forms
from blogs.models import Blog, Category, Profile, Tag
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'


class BlogPostForm(forms.ModelForm):
    tags_input = forms.CharField(
        label='Tags',
        required=False,
        help_text='Comma-separated tags (e.g. python, tutorial, web)',
        widget=forms.TextInput(attrs={'placeholder': 'python, tutorial, web'}),
    )

    class Meta:
        model = Blog
        fields = (
            'title', 'category', 'featured_image',
            'short_description', 'blog_body', 'status', 'is_featured',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                t.name for t in self.instance.tags.all()
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            self._save_tags(instance)
        return instance

    def save_m2m_tags(self, instance):
        self._save_tags(instance)

    def _save_tags(self, instance):
        raw = self.cleaned_data.get('tags_input', '') or ''
        names = [t.strip() for t in raw.split(',') if t.strip()]
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(name__iexact=name, defaults={'name': name})
            tags.append(tag)
        instance.tags.set(tags)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio', 'avatar', 'website')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'A short bio about yourself…'}),
        }


class AddUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
