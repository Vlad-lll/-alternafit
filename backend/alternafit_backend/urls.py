from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from exercises.views import ExerciseViewSet, MuscularGroupViewSet

# O router cria automaticamente as URLs de lista (/api/exercicios/) e de
# detalhe (/api/exercicios/<codigo>/) para cada viewset registrado.
router = DefaultRouter()
router.register('exercicios', ExerciseViewSet, basename='exercicio')
router.register('grupos-musculares', MuscularGroupViewSet, basename='grupo-muscular')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
