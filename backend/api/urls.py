from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from djoser.views import UserViewSet as DjoserUserViewSet
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers

from users.views import UserViewSet
from recept.views import RecipeViewSet, TagViewSet, IngredientViewSet


router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)