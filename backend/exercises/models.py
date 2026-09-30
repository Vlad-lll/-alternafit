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
    name = models.CharField('nome', max_length=100, unique=True)
    description = models.TextField('descrição', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'grupo muscular'
        verbose_name_plural = 'grupos musculares'

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField('nome', max_length=100, unique=True)
    description = models.TextField('descrição', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'equipamento'
        verbose_name_plural = 'equipamentos'

    def __str__(self):
        return self.name


class Exercise(models.Model):
    name = models.CharField('nome', max_length=150, unique=True)
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
    is_equipment_free = models.BooleanField(
        'sem equipamento',
        default=False,
        help_text='Marque se o exercício pode ser feito sem nenhum aparelho.',
    )
    muscular_groups = models.ManyToManyField(
        MuscularGroup,
        related_name='exercises',
        verbose_name='grupos musculares',
    )
    equipment = models.ManyToManyField(
        Equipment,
        related_name='exercises',
        blank=True,
        verbose_name='equipamentos',
    )
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
