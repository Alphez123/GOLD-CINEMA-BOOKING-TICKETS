# users/forms.py
from django import forms
from .models import Movie

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ["title", "genre", "duration", "category", "description", "price", "poster"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "genre": forms.TextInput(attrs={"class": "input"}),
            "duration": forms.TextInput(attrs={"class": "input"}),
            "category": forms.TextInput(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 4}),
            "price": forms.NumberInput(attrs={"class": "input"}),
        }

    def clean_poster(self):
        poster = self.cleaned_data.get("poster")
        if poster:
            # simple validation: size/type (optional)
            if hasattr(poster, "content_type") and not poster.content_type.startswith("image/"):
                raise forms.ValidationError("Uploaded file must be an image.")
        return poster
