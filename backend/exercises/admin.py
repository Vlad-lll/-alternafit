from django.contrib import admin

from .models import (
    Difficulty,
    Equipment,
    Exercise,
    ExerciseAlias,
    ExerciseAlternative,
    ExerciseMuscularGroup,
    ExerciseStep,
    MovementPattern,
    MuscularGroup,
    Source,
)


class EquipmentFreeFilter(admin.SimpleListFilter):
    """Filtro "sem equipamento: Sim/Não" (calculado: exercício sem nenhum equipamento cadastrado)."""

    title = 'sem equipamento'
    parameter_name = 'sem_equipamento'
    field_prefix = ''

    def lookups(self, request, model_admin):
        return [('sim', 'Sim'), ('nao', 'Não')]

    def queryset(self, request, queryset):
        lookup = f'{self.field_prefix}equipment__isnull'
        if self.value() == 'sim':
            return queryset.filter(**{lookup: True})
        if self.value() == 'nao':
            return queryset.filter(**{lookup: False}).distinct()
        return queryset


class AlternativeEquipmentFreeFilter(EquipmentFreeFilter):
    field_prefix = 'alternative__'


@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'level']


@admin.register(MuscularGroup)
class MuscularGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'code']
    list_filter = ['region']
    search_fields = ['name']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(MovementPattern)
class MovementPatternAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['author', 'title', 'source_type']
    search_fields = ['author', 'title']


class ExerciseMuscularGroupInline(admin.TabularInline):
    model = ExerciseMuscularGroup
    extra = 1
    autocomplete_fields = ['muscular_group']


class ExerciseAlternativeInline(admin.TabularInline):
    """Tabela de alternativas exibida dentro da tela de edição de um exercício."""

    model = ExerciseAlternative
    fk_name = 'exercise'
    extra = 1
    autocomplete_fields = ['alternative']


class ExerciseStepInline(admin.TabularInline):
    model = ExerciseStep
    extra = 0


class ExerciseAliasInline(admin.TabularInline):
    model = ExerciseAlias
    extra = 0


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'difficulty', 'movement_pattern', 'equipment_free', 'data_status']
    list_filter = [
        EquipmentFreeFilter, 'difficulty', 'movement_pattern', 'data_status', 'muscular_groups', 'equipment',
    ]
    search_fields = ['name', 'name_en', 'aliases__alias']
    filter_horizontal = ['equipment', 'sources']
    inlines = [ExerciseMuscularGroupInline, ExerciseAlternativeInline, ExerciseStepInline, ExerciseAliasInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('difficulty', 'movement_pattern').prefetch_related('equipment')

    @admin.display(boolean=True, description='sem equipamento')
    def equipment_free(self, obj):
        return obj.is_equipment_free


@admin.register(ExerciseAlternative)
class ExerciseAlternativeAdmin(admin.ModelAdmin):
    """Lista de todas as ligações exercício → alternativa, para revisão."""

    list_display = ['exercise', 'alternative', 'order', 'alternative_is_equipment_free', 'same_movement_pattern']
    list_filter = [AlternativeEquipmentFreeFilter]
    search_fields = ['exercise__name', 'alternative__name']
    autocomplete_fields = ['exercise', 'alternative']

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('exercise', 'alternative')
            .prefetch_related('alternative__equipment')
        )

    @admin.display(boolean=True, description='sem equipamento')
    def alternative_is_equipment_free(self, obj):
        return obj.alternative.is_equipment_free

    @admin.display(boolean=True, description='mesmo padrão de movimento')
    def same_movement_pattern(self, obj):
        return obj.exercise.movement_pattern_id == obj.alternative.movement_pattern_id
