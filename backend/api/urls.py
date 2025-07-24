from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from users.views import UserAvatarAPIView, CustomUserViewSet
from recept.views import RecipeViewSet, TagViewSet, IngredientViewSet
from rest_framework.routers import DefaultRouter
from djoser.views import UserViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', UserAvatarAPIView.as_view(), name='user-avatar'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)