from django.db.models import Case, Exists, IntegerField, OuterRef, Prefetch, Q, Value, When
from rest_framework import viewsets

from .models import Exercise, ExerciseAlias, ExerciseAlternative, ExerciseMuscularGroup, MuscularGroup
from .serializers import ExerciseSerializer, MuscularGroupSerializer


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Exercícios com suas alternativas (somente leitura).

    GET /api/exercicios/                  todos os exercícios
    GET /api/exercicios/?busca=supino     nome, nome em inglês ou apelido contém "supino" (nome exato primeiro)
    GET /api/exercicios/?grupo=Glúteos    exercícios que trabalham o grupo (foco principal primeiro)
    GET /api/exercicios/<codigo>/         um exercício específico
    """

    serializer_class = ExerciseSerializer

    def get_queryset(self):
        queryset = Exercise.objects.select_related('difficulty', 'movement_pattern').prefetch_related(
            Prefetch(
                'muscular_group_links',
                queryset=ExerciseMuscularGroup.objects.select_related('muscular_group'),
            ),
            'equipment',
            'aliases',
            'steps',
            'sources',
            Prefetch(
                'alternative_links',
                queryset=ExerciseAlternative.objects.select_related('alternative__difficulty')
                .prefetch_related('alternative__equipment')
                .order_by('order'),
            ),
        )

        search = self.request.query_params.get('busca', '').strip()
        if search:
            matches = Exercise.objects.filter(
                Q(name__icontains=search) | Q(name_en__icontains=search) | Q(aliases__alias__icontains=search)
            ).values('pk')
            exact_alias = ExerciseAlias.objects.filter(exercise=OuterRef('pk'), alias__iexact=search)
            # Ordena por relevância: nome exato, depois apelido/inglês exato, depois "começa com", depois "contém".
            queryset = queryset.filter(pk__in=matches).annotate(
                relevance=Case(
                    When(name__iexact=search, then=Value(0)),
                    When(Q(name_en__iexact=search) | Exists(exact_alias), then=Value(1)),
                    When(name__istartswith=search, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).order_by('relevance', 'name')

        group = self.request.query_params.get('grupo', '').strip()
        if group:
            in_group = ExerciseMuscularGroup.objects.filter(exercise=OuterRef('pk'), muscular_group__name=group)
            queryset = queryset.filter(Exists(in_group)).annotate(
                is_primary=Exists(in_group.filter(role=ExerciseMuscularGroup.Role.PRIMARY))
            ).order_by('-is_primary', 'name')

        return queryset


class MuscularGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """Grupos musculares, usados nos chips de navegação do frontend (somente leitura)."""

    queryset = MuscularGroup.objects.all()
    serializer_class = MuscularGroupSerializer
