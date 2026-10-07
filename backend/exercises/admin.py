from django.contrib import admin

from .models import Difficulty, Equipment, Exercise, ExerciseAlternative, MuscularGroup


@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'level']


@admin.register(MuscularGroup)
class MuscularGroupAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    search_fields = ['name']


class ExerciseAlternativeInline(admin.TabularInline):
    """Tabela de alternativas exibida dentro da tela de edição de um exercício."""

    model = ExerciseAlternative
    fk_name = 'exercise'
    extra = 1
    autocomplete_fields = ['alternative']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'difficulty', 'is_equipment_free']
    list_filter = ['is_equipment_free', 'difficulty', 'muscular_groups', 'equipment']
    search_fields = ['name']
    filter_horizontal = ['muscular_groups', 'equipment']
    inlines = [ExerciseAlternativeInline]


@admin.register(ExerciseAlternative)
class ExerciseAlternativeAdmin(admin.ModelAdmin):
    """Lista de todas as ligações exercício → alternativa, para revisão."""

    list_display = ['exercise', 'alternative', 'order', 'alternative_is_equipment_free']
    list_filter = ['alternative__is_equipment_free']
    list_select_related = ['exercise', 'alternative']
    search_fields = ['exercise__name', 'alternative__name']
    autocomplete_fields = ['exercise', 'alternative']

    @admin.display(boolean=True, description='sem equipamento')
    def alternative_is_equipment_free(self, obj):
        return obj.alternative.is_equipment_free
