from django.contrib.auth.models import User

from model_mommy.recipe import Recipe, foreign_key, seq

from .models import Domain

user = Recipe(User)

domain = Recipe(Domain, user=foreign_key(user), name="host-%s.example.com" % seq(1))