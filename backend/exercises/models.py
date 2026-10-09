from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Difficulty(models.Model):
    name = models.CharField('nome', max_length=50, unique=True)
    level = models.PositiveSmallIntegerField(
        'nível',
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text='De 1 (mais fácil) a 3 (mais difícil).',
    )
    description = models.TextField('descrição', blank=True)

    class Meta:
        ordering = ['level']
        verbose_name = 'dificuldade'
        verbose_name_plural = 'dificuldades'

    def __str__(self):
        return self.name


class MuscularGroup(models.Model):
    class Region(models.TextChoices):
        UPPER = 'upper', 'Superior'
        CORE = 'core', 'Core'
        LOWER = 'lower', 'Inferior'

    name = models.CharField('nome', max_length=100, unique=True)
    code = models.CharField(
        'código', max_length=50, blank=True, help_text='Identificador sem acentos, ex.: POSTERIOR_COXA.'
    )
    region = models.CharField('região', max_length=20, choices=Region.choices, blank=True)
    description = models.TextField('descrição', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'grupo muscular'
        verbose_name_plural = 'grupos musculares'

    def __str__(self):
        return self.name


class Equipment(models.Model):
    class Category(models.TextChoices):
        FREE_WEIGHT = 'free_weight', 'Peso livre'
        ACCESSORY = 'accessory', 'Acessório'
        FIXED_STRUCTURE = 'fixed_structure', 'Estrutura fixa'
        MACHINE = 'machine', 'Máquina'

    name = models.CharField('nome', max_length=100, unique=True)
    category = models.CharField('categoria', max_length=20, choices=Category.choices, blank=True)
    description = models.TextField('descrição', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'equipamento'
        verbose_name_plural = 'equipamentos'

    def __str__(self):
        return self.name


class MovementPattern(models.Model):
    """Padrão de movimento (ex.: empurrar horizontal, agachar), usado para comparar alternativas."""

    code = models.CharField('código', max_length=50, unique=True)
    name = models.CharField('nome', max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'padrão de movimento'
        verbose_name_plural = 'padrões de movimento'

    def __str__(self):
        return self.name


class Source(models.Model):
    """Fonte técnica (artigo, biblioteca de exercícios) que embasa os dados de um exercício."""

    author = models.CharField('autor / organização', max_length=200)
    title = models.CharField('título', max_length=500)
    url = models.URLField('URL', max_length=500)
    source_type = models.CharField('tipo', max_length=150, blank=True)

    class Meta:
        ordering = ['author', 'title']
        verbose_name = 'fonte'
        verbose_name_plural = 'fontes'

    def __str__(self):
        return f'{self.author} - {self.title}'


class Exercise(models.Model):
    class DataStatus(models.TextChoices):
        SOURCED = 'sourced', 'Com fonte'
        LUCAS_UNSOURCED = 'lucas_unsourced', 'Sem fonte - dado do Lucas'
        NEEDS_REVIEW = 'needs_review', 'Sem fonte específica (revisar)'

    name = models.CharField('nome', max_length=150, unique=True)
    name_en = models.CharField('nome em inglês', max_length=150, blank=True)
    # Descrição, dica e dificuldade são opcionais para permitir cadastrar
    # exercícios aos poucos (o frontend mostra "A definir" quando faltam).
    description = models.TextField('descrição', blank=True)
    tip = models.TextField('dica de execução', blank=True)
    video_url = models.URLField('URL do vídeo', max_length=500, blank=True)
    difficulty = models.ForeignKey(
        Difficulty,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='exercises',
        verbose_name='dificuldade',
    )
    movement_pattern = models.ForeignKey(
        MovementPattern,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='exercises',
        verbose_name='padrão de movimento',
    )
    data_status = models.CharField('status dos dados', max_length=30, choices=DataStatus.choices, blank=True)
    notes = models.TextField('observação interna', blank=True)
    muscular_groups = models.ManyToManyField(
        MuscularGroup,
        through='ExerciseMuscularGroup',
        related_name='exercises',
        verbose_name='grupos musculares',
    )
    equipment = models.ManyToManyField(
        Equipment,
        related_name='exercises',
        blank=True,
        verbose_name='equipamentos',
        help_text='Deixe vazio se o exercício não usa nenhum objeto (só o corpo, o chão ou a parede).',
    )
    sources = models.ManyToManyField(Source, related_name='exercises', blank=True, verbose_name='fontes')
    alternatives = models.ManyToManyField(
        'self',
        through='ExerciseAlternative',
        through_fields=('exercise', 'alternative'),
        symmetrical=False,
        related_name='alternative_to',
        verbose_name='alternativas',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'exercício'
        verbose_name_plural = 'exercícios'

    def __str__(self):
        return self.name

    @property
    def is_equipment_free(self):
        """Regra da planilha: sem equipamento = nenhum equipamento cadastrado (chão e parede não contam)."""
        return not self.equipment.all()


class ExerciseMuscularGroup(models.Model):
    """Liga um exercício a um grupo muscular, dizendo se ele é o foco principal ou auxiliar."""

    class Role(models.TextChoices):
        PRIMARY = 'primary', 'Principal'
        SECONDARY = 'secondary', 'Auxiliar'

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='muscular_group_links',
        verbose_name='exercício',
    )
    muscular_group = models.ForeignKey(
        MuscularGroup,
        on_delete=models.PROTECT,
        related_name='exercise_links',
        verbose_name='grupo muscular',
    )
    role = models.CharField('papel', max_length=20, choices=Role.choices, default=Role.PRIMARY)

    class Meta:
        # "primary" vem antes de "secondary": o grupo principal aparece primeiro.
        ordering = ['exercise', 'role', 'muscular_group__name']
        verbose_name = 'grupo muscular do exercício'
        verbose_name_plural = 'grupos musculares do exercício'
        constraints = [
            models.UniqueConstraint(
                fields=['exercise', 'muscular_group'],
                name='unique_exercise_muscular_group',
            ),
        ]

    def __str__(self):
        return f'{self.exercise} - {self.muscular_group} ({self.get_role_display()})'


class ExerciseAlternative(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='alternative_links',
        verbose_name='exercício',
    )
    alternative = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='alternative_of_links',
        verbose_name='alternativa',
    )
    order = models.PositiveSmallIntegerField(
        'ordem', default=1, help_text='Números menores aparecem primeiro.'
    )
    note = models.TextField('observação', blank=True, help_text='Comentário sobre esta troca específica.')

    class Meta:
        ordering = ['exercise', 'order']
        verbose_name = 'alternativa de exercício'
        verbose_name_plural = 'alternativas de exercícios'
        constraints = [
            models.UniqueConstraint(
                fields=['exercise', 'alternative'],
                name='unique_exercise_alternative',
            ),
            models.CheckConstraint(
                condition=~models.Q(exercise=models.F('alternative')),
                name='alternative_is_not_itself',
            ),
        ]

    def __str__(self):
        return f'{self.exercise} → {self.alternative}'


class ExerciseStep(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name='exercício',
    )
    order = models.PositiveSmallIntegerField('ordem')
    description = models.TextField('descrição')
    extra_tip = models.TextField('dica extra', blank=True)

    class Meta:
        ordering = ['exercise', 'order']
        verbose_name = 'passo de execução'
        verbose_name_plural = 'passos de execução'
        constraints = [
            models.UniqueConstraint(fields=['exercise', 'order'], name='unique_exercise_step_order'),
        ]

    def __str__(self):
        return f'{self.exercise} - passo {self.order}'


class ExerciseAlias(models.Model):
    """Outro nome pelo qual o exercício é conhecido (ex.: "Push-up"), usado na busca."""

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='aliases',
        verbose_name='exercício',
    )
    alias = models.CharField('apelido', max_length=150, unique=True)

    class Meta:
        ordering = ['alias']
        verbose_name = 'apelido'
        verbose_name_plural = 'apelidos'

    def __str__(self):
        return self.alias
