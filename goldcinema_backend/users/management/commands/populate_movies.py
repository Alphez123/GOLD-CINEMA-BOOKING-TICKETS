from django.core.management.base import BaseCommand
from users.models import Movie
import random

class Command(BaseCommand):
    help = 'Populates the database with hardcoded movies and assigns random prices'

    def handle(self, *args, **kwargs):
        hardcoded_movies = {
            "Taylor Swift Concert Show": {
                "category": "Concert",
                "duration": "1h 30m",
                "poster": "static/images/tailor.jpg"
            },
            "Free Rock Concert": {
                "category": "Concert",
                "duration": "1h 55m",
                "poster": "static/images/freerock-concert.jpg"
            },
            "A Minecraft Movie": {
                "category": "Thriller",
                "duration": "2h 10m",
                "poster": "static/images/minecraft.jpg"
            },
            "Echoes of Light": {
                "category": "Drama",
                "duration": "1h 55m",
                "poster": "https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_UF894,1000_QL80_.jpg"
            },
            "Cold Play": {
                "category": "Play",
                "duration": "2h 10m",
                "poster": "static/images/coldplay.jpg"
            },
            "Childs Play": {
                "category": "Drama",
                "duration": "1h 55m",
                "poster": "static/images/childsplay.jpg"
            },
            "Other Movies": {
                "category": "Various",
                "duration": "Varies",
                "poster": "static/images/other-movies.jpg"
            }
        }

        for title, data in hardcoded_movies.items():
            movie, created = Movie.objects.get_or_create(title=title)
            
            # Update fields
            movie.category = data["category"]
            movie.duration = data["duration"]
            
            # Assign random price if not set or if we want to reset it
            # Prices between 500 and 1500 KSH
            if movie.price == 0.00:
                movie.price = random.randint(50, 150) * 10 # 500, 510, ... 1500
            
            # For poster, we're just storing the string path/url in the ImageField for now
            # Note: ImageField usually expects a file, but if we just want to store the path string
            # we might need to handle it differently or just rely on the fact that we are using it as a URL in template.
            # However, Django ImageField stores the path relative to MEDIA_ROOT. 
            # If these are static files, we should probably not put them in ImageField or handle it carefully.
            # But the model has ImageField. Let's just leave poster alone if it's complex, 
            # or try to set it if it's a URL.
            # Actually, the template uses {{ movie.poster.url }} which implies it expects a file.
            # But the hardcoded data has static paths. 
            # Let's skip poster update for now to avoid breaking image paths if they are not actual files in media.
            
            movie.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated "{title}" with price KSH {movie.price}'))

        self.stdout.write(self.style.SUCCESS('All movies populated/updated.'))
