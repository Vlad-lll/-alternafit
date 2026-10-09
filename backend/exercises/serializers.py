"""
Serializers: transformam os models (em inglês) no JSON que o frontend espera
(em português camelCase, o mesmo formato de src/data/exercicios.js).
"""

from rest_framework import serializers

from .models import Exercise, ExerciseAlternative, ExerciseMuscularGroup, ExerciseStep, MuscularGroup, Source


def difficulty_level(exercise):
    """O frontend recebe a dificuldade como número (1 a 3), ou null se não cadastrada."""
    return exercise.difficulty.level if exercise.difficulty else None


class MuscularGroupSerializer(serializers.ModelSerializer):
    codigo = serializers.CharField(source='code')
    nome = serializers.CharField(source='name')
    regiao = serializers.CharField(source='get_region_display')
    descricao = serializers.CharField(source='description')

    class Meta:
        model = MuscularGroup
        fields = ['id', 'codigo', 'nome', 'regiao', 'descricao']


class StepSerializer(serializers.ModelSerializer):
    ordem = serializers.IntegerField(source='order')
    descricao = serializers.CharField(source='description')
    dicaExtra = serializers.CharField(source='extra_tip')

    class Meta:
        model = ExerciseStep
        fields = ['ordem', 'descricao', 'dicaExtra']


class SourceSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source='author')
    titulo = serializers.CharField(source='title')

    class Meta:
        model = Source
        fields = ['autor', 'titulo', 'url']


class AlternativeSerializer(serializers.ModelSerializer):
    """Uma alternativa, no formato do card de alternativa do frontend."""

    codigo = serializers.IntegerField(source='alternative.id')
    nome = serializers.CharField(source='alternative.name')
    ordemPrioridade = serializers.IntegerField(source='order')
    semEquipamento = serializers.BooleanField(source='alternative.is_equipment_free')
    dificuldade = serializers.SerializerMethodField()
    dica = serializers.CharField(source='alternative.tip')
    videoUrl = serializers.CharField(source='alternative.video_url')
    observacao = serializers.CharField(source='note')

    class Meta:
        model = ExerciseAlternative
        fields = [
            'codigo', 'nome', 'ordemPrioridade', 'semEquipamento', 'dificuldade', 'dica', 'videoUrl', 'observacao',
        ]

    def get_dificuldade(self, link):
        return difficulty_level(link.alternative)


class ExerciseSerializer(serializers.ModelSerializer):
    codigo = serializers.IntegerField(source='id')
    nome = serializers.CharField(source='name')
    nomeEn = serializers.CharField(source='name_en')
    descricao = serializers.CharField(source='description')
    dificuldade = serializers.SerializerMethodField()
    padraoMovimento = serializers.SerializerMethodField()
    gruposMusculares = serializers.SerializerMethodField()
    gruposPrincipais = serializers.SerializerMethodField()
    gruposAuxiliares = serializers.SerializerMethodField()
    precisaEquipamento = serializers.SerializerMethodField()
    semEquipamento = serializers.BooleanField(source='is_equipment_free')
    equipamentos = serializers.SlugRelatedField(source='equipment', slug_field='name', many=True, read_only=True)
    dica = serializers.CharField(source='tip')
    videoUrl = serializers.CharField(source='video_url')
    apelidos = serializers.SlugRelatedField(source='aliases', slug_field='alias', many=True, read_only=True)
    passos = StepSerializer(source='steps', many=True, read_only=True)
    fontes = SourceSerializer(source='sources', many=True, read_only=True)
    alternativas = AlternativeSerializer(source='alternative_links', many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'codigo', 'nome', 'nomeEn', 'descricao', 'dificuldade', 'padraoMovimento',
            'gruposMusculares', 'gruposPrincipais', 'gruposAuxiliares',
            'precisaEquipamento', 'semEquipamento', 'equipamentos', 'dica', 'videoUrl',
            'apelidos', 'passos', 'fontes', 'alternativas',
        ]

    def get_dificuldade(self, exercise):
        return difficulty_level(exercise)

    def get_padraoMovimento(self, exercise):
        return exercise.movement_pattern.name if exercise.movement_pattern else None

    def get_gruposMusculares(self, exercise):
        # Todos os grupos, com o(s) principal(is) primeiro (ordem definida no model).
        return [link.muscular_group.name for link in exercise.muscular_group_links.all()]

    def get_gruposPrincipais(self, exercise):
        return self._groups_with_role(exercise, ExerciseMuscularGroup.Role.PRIMARY)

    def get_gruposAuxiliares(self, exercise):
        return self._groups_with_role(exercise, ExerciseMuscularGroup.Role.SECONDARY)

    def get_precisaEquipamento(self, exercise):
        return not exercise.is_equipment_free

    def _groups_with_role(self, exercise, role):
        return [link.muscular_group.name for link in exercise.muscular_group_links.all() if link.role == role]
