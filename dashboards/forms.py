from django import forms
from blogs.models import Blog, Category, Profile, Tag
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'


FEATURE_TOGGLE_GROUPS = ('Admin', 'Manager', 'Editor')


def _user_can_feature(user):
    """Only Admin/Manager/Editor (or superuser) can mark a post as featured."""
    if user is None or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=FEATURE_TOGGLE_GROUPS).exists()


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
            'short_description', 'blog_body', 'status',
            'is_featured', 'feature_requested',
        )
        labels = {
            'feature_requested': 'Suggest as Featured',
        }
        help_texts = {
            'feature_requested': 'Tick to ask an editor to review this post for the homepage Featured section.',
        }

    def __init__(self, *args, **kwargs):
        # Pull the requesting user out of kwargs so views can pass it in.
        self._request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                t.name for t in self.instance.tags.all()
            )

        if _user_can_feature(self._request_user):
            # Editors/Managers/Admins control the real flag — they don't need
            # to "suggest" their own posts.
            self.fields.pop('feature_requested', None)
        else:
            # Authors can't flip is_featured; they only get the suggestion field.
            self.fields.pop('is_featured', None)

    def save(self, commit=True):
        # Defence in depth: even if the field was tampered with client-side,
        # never let a non-privileged user flip is_featured.
        if not _user_can_feature(self._request_user):
            if self.instance.pk:
                # Editing an existing post: keep whatever value is already saved.
                original = type(self.instance).objects.filter(pk=self.instance.pk).values_list('is_featured', flat=True).first()
                self.instance.is_featured = bool(original)
            else:
                # Brand-new post: force off.
                self.instance.is_featured = False
        else:
            # Once an editor actually features a post, clear any pending request.
            if self.instance.is_featured:
                self.instance.feature_requested = False
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
