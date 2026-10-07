"""
Importa a planilha de exercícios do time de Educação Física para o banco.

Uso (dentro da pasta backend/):
    venv\\Scripts\\python.exe manage.py importar_planilha "..\\data\\arquivo.xlsx" --dry-run
    venv\\Scripts\\python.exe manage.py importar_planilha "..\\data\\arquivo.xlsx"

- Pode ser rodado várias vezes: os registros são encontrados pelo nome e
  atualizados, sem duplicar.
- --dry-run simula tudo e mostra o relatório, mas não grava nada.
- Tudo acontece dentro de uma transação: se der erro no meio, o banco
  volta exatamente como estava.
"""

import re
import unicodedata
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.db import transaction
from openpyxl import load_workbook

from exercises.models import Difficulty, Equipment, Exercise, ExerciseAlternative, MuscularGroup

BODYWEIGHT_EQUIPMENT = 'Nenhum (peso do corpo)'

# Trecho que o cabeçalho de cada coluna precisa conter (em minúsculas e sem
# acentos). Serve para detectar colunas trocadas de lugar na planilha.
EXPECTED_HEADERS = {
    'Dificuldades': ['nivel', 'nome', 'descricao'],
    'Grupos Musculares': ['nome', 'descricao'],
    'Equipamentos': ['nome', 'descricao'],
    'Exercícios': [
        'codigo', 'nome', 'descricao', 'nivel', 'grupo',
        'precisa de equipamento', 'equipamento', 'dica', 'video',
    ],
    'Alternativas': [
        'exercicio original', 'codigo', 'exercicio alternativo', 'codigo',
        'ordem', 'sem equipamento',
    ],
}


def clean_name(value):
    """Texto da célula numa linha só, sem espaços sobrando."""
    if value is None:
        return ''
    return re.sub(r'\s+', ' ', str(value)).strip()


def clean_long_text(value):
    """Texto longo (descrição, dica): mantém quebras de linha, tira espaços das pontas."""
    if value is None:
        return ''
    return str(value).strip()


def fold(value):
    """Minúsculas e sem acentos, para comparar textos ("Não " vira "nao")."""
    normalized = unicodedata.normalize('NFKD', clean_name(value).lower())
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch))


def parse_yes_no(value):
    answer = fold(value)
    if answer in ('sim', 's'):
        return True
    if answer in ('nao', 'n'):
        return False
    return None


def parse_int(value):
    text = clean_name(value).replace(',', '.')
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() else None


def split_names(value):
    """"Peitoral, Tríceps" -> ["Peitoral", "Tríceps"]"""
    return [name for name in (clean_name(part) for part in clean_name(value).split(',')) if name]


class Command(BaseCommand):
    help = 'Importa a planilha de exercícios do time de Educação Física para o banco de dados.'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', help='Caminho do arquivo .xlsx')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a importação e mostra o relatório, sem gravar nada no banco.',
        )

    def handle(self, *args, **options):
        path = Path(options['arquivo'])
        if not path.exists():
            raise CommandError(f'Arquivo não encontrado: {path}')

        self.stats = {}
        self.warnings = []
        self.rule_problems = []

        workbook = load_workbook(path, data_only=True, read_only=True)
        try:
            with transaction.atomic():
                self.import_difficulties(self.rows(workbook, 'Dificuldades'))
                self.import_simple_table(MuscularGroup, 'Grupos Musculares', self.rows(workbook, 'Grupos Musculares'))
                self.import_simple_table(Equipment, 'Equipamentos', self.rows(workbook, 'Equipamentos'))
                sheet_exercises = self.import_exercises(self.rows(workbook, 'Exercícios'))
                self.import_alternatives(self.rows(workbook, 'Alternativas'))
                self.check_rules(sheet_exercises)
                incomplete = self.find_incomplete_exercises()
                if options['dry_run']:
                    transaction.set_rollback(True)
            ignored_steps = 'Passos de Execução' in workbook.sheetnames
        finally:
            workbook.close()

        self.print_report(options['dry_run'], incomplete, ignored_steps)

    # ------------------------------------------------------------------ leitura

    def rows(self, workbook, sheet_name):
        """Confere o cabeçalho da aba e devolve (número da linha, valores) de cada linha de dados."""
        if sheet_name not in workbook.sheetnames:
            raise CommandError(f'A planilha não tem a aba "{sheet_name}".')

        expected = EXPECTED_HEADERS[sheet_name]
        rows = workbook[sheet_name].iter_rows(values_only=True)
        header = list(next(rows, ()))
        for index, part in enumerate(expected):
            found = header[index] if index < len(header) else None
            if part not in fold(found):
                raise CommandError(
                    f'Aba "{sheet_name}", coluna {index + 1}: esperava um cabeçalho contendo '
                    f'"{part}", mas encontrou "{clean_name(found)}". As colunas mudaram de lugar?'
                )

        result = []
        for number, values in enumerate(rows, start=2):
            values = list(values) + [None] * len(expected)
            result.append((number, values[:len(expected)]))
        return result

    # --------------------------------------------------------------- importação

    def import_difficulties(self, rows):
        for number, (level_cell, name_cell, description_cell) in rows:
            name = clean_name(name_cell)
            level = parse_int(level_cell)
            if not name and level is None:
                continue
            if not name or level not in (1, 2, 3):
                self.warn(f'Dificuldades, linha {number}: precisa de nível (1 a 3) e nome. Linha ignorada.')
                continue
            _, created = Difficulty.objects.update_or_create(
                level=level,
                defaults={'name': name, 'description': clean_long_text(description_cell)},
            )
            self.count('Dificuldades', created)

    def import_simple_table(self, model, label, rows):
        for _number, (name_cell, description_cell) in rows:
            name = clean_name(name_cell)
            if not name:
                continue
            _, created = model.objects.update_or_create(
                name=name,
                defaults={'description': clean_long_text(description_cell)},
            )
            self.count(label, created)

    def import_exercises(self, rows):
        exercises = []
        seen_names = set()
        for number, values in rows:
            (_code, name_cell, description_cell, level_cell, groups_cell,
             needs_equipment_cell, equipment_cell, tip_cell, video_cell) = values
            name = clean_name(name_cell)
            if not name:
                continue
            where = f'Exercícios, linha {number} ({name})'

            if fold(name) in seen_names:
                self.warn(f'{where}: nome repetido na planilha. Esta linha sobrescreve a anterior.')
            seen_names.add(fold(name))

            difficulty = None
            if clean_name(level_cell):
                level = parse_int(level_cell)
                difficulty = Difficulty.objects.filter(level=level).first() if level else None
                if difficulty is None:
                    self.warn(f'{where}: nível "{clean_name(level_cell)}" não existe na aba Dificuldades.')

            needs_equipment = parse_yes_no(needs_equipment_cell)
            if needs_equipment is None:
                self.warn(f'{where}: "Precisa de equipamento?" vazio ou diferente de Sim/Não. Considerado "Sim".')
                needs_equipment = True

            video_url = clean_name(video_cell)
            if video_url:
                try:
                    URLValidator()(video_url)
                except ValidationError:
                    self.warn(f'{where}: link do vídeo inválido ("{video_url}"). Ignorado.')
                    video_url = ''

            exercise, created = Exercise.objects.update_or_create(
                name=name,
                defaults={
                    'description': clean_long_text(description_cell),
                    'tip': clean_long_text(tip_cell),
                    'video_url': video_url,
                    'difficulty': difficulty,
                    'is_equipment_free': not needs_equipment,
                },
            )
            self.count('Exercícios', created)

            exercise.muscular_groups.set(
                self.get_or_create_many(MuscularGroup, 'Grupos Musculares', split_names(groups_cell), where)
            )
            equipment = self.get_or_create_many(Equipment, 'Equipamentos', split_names(equipment_cell), where)
            exercise.equipment.set(equipment)

            real_equipment = [e.name for e in equipment if fold(e.name) != fold(BODYWEIGHT_EQUIPMENT)]
            if exercise.is_equipment_free and real_equipment:
                self.warn(
                    f'{where}: marcado como "não precisa de equipamento", mas lista '
                    f'equipamentos: {", ".join(real_equipment)}.'
                )

            exercises.append(exercise)
        return exercises

    def import_alternatives(self, rows):
        for number, values in rows:
            original_cell, _code, alternative_cell, _alternative_code, order_cell, equipment_free_cell = values
            original_name = clean_name(original_cell)
            alternative_name = clean_name(alternative_cell)
            # Linhas vazias e os textos de instrução no fim da aba só têm a coluna A.
            if not (alternative_name or clean_name(order_cell) or clean_name(equipment_free_cell)):
                continue
            where = f'Alternativas, linha {number}'
            if not original_name or not alternative_name:
                self.warn(f'{where}: falta o exercício original ou o alternativo. Linha ignorada.')
                continue
            if fold(original_name) == fold(alternative_name):
                self.warn(f'{where}: "{original_name}" não pode ser alternativa de si mesmo. Linha ignorada.')
                continue

            equipment_free = parse_yes_no(equipment_free_cell)
            original = self.find_or_create_incomplete(original_name, None, where)
            alternative = self.find_or_create_incomplete(alternative_name, equipment_free, where)

            if equipment_free is not None and alternative.is_equipment_free != equipment_free:
                in_sheet = 'Sim' if equipment_free else 'Não'
                in_exercise = 'Sim' if alternative.is_equipment_free else 'Não'
                self.warn(
                    f'{where}: "{alternative}" está como sem equipamento = {in_sheet} aqui, mas o '
                    f'exercício está com {in_exercise}. Vale o que está no exercício.'
                )

            order = parse_int(order_cell)
            if order is None or order < 1:
                self.warn(f'{where}: ordem de prioridade vazia ou inválida. Usando 1.')
                order = 1

            _, created = ExerciseAlternative.objects.update_or_create(
                exercise=original,
                alternative=alternative,
                defaults={'order': order},
            )
            self.count('Alternativas', created)

    # ----------------------------------------------------------------- apoio

    def get_or_create_many(self, model, label, names, where):
        objects = []
        for name in names:
            obj, created = model.objects.get_or_create(name=name)
            if created:
                self.count(label, True)
                self.warn(f'{where}: "{name}" não estava na aba {label}. Criado automaticamente.')
            objects.append(obj)
        return objects

    def find_or_create_incomplete(self, name, equipment_free, where):
        exercise = Exercise.objects.filter(name=name).first()
        if exercise:
            return exercise
        exercise = Exercise.objects.create(name=name, is_equipment_free=bool(equipment_free))
        self.count('Exercícios', True)
        self.warn(f'{where}: "{name}" não está na aba Exercícios. Criado só com o nome (incompleto).')
        return exercise

    def check_rules(self, sheet_exercises):
        for exercise in sheet_exercises:
            links = list(exercise.alternative_links.select_related('alternative'))
            if not links:
                self.rule_problems.append(f'"{exercise}" não tem nenhuma alternativa cadastrada.')
            elif not any(link.alternative.is_equipment_free for link in links):
                self.rule_problems.append(f'"{exercise}" não tem nenhuma alternativa sem equipamento.')

    def find_incomplete_exercises(self):
        incomplete = []
        for exercise in Exercise.objects.prefetch_related('muscular_groups', 'equipment'):
            missing = []
            if not exercise.description:
                missing.append('descrição')
            if not exercise.tip:
                missing.append('dica')
            if exercise.difficulty_id is None:
                missing.append('dificuldade')
            if not exercise.muscular_groups.all():
                missing.append('grupos musculares')
            if not exercise.is_equipment_free and not exercise.equipment.all():
                missing.append('equipamentos')
            if missing:
                incomplete.append(f'{exercise}: falta {", ".join(missing)}')
        return incomplete

    def count(self, label, created):
        entry = self.stats.setdefault(label, {'criados': 0, 'atualizados': 0})
        entry['criados' if created else 'atualizados'] += 1

    def warn(self, message):
        self.warnings.append(message)

    # ---------------------------------------------------------------- relatório

    def print_report(self, dry_run, incomplete, ignored_steps):
        out = self.stdout
        out.write('')
        out.write('========== RELATÓRIO DA IMPORTAÇÃO ==========')
        if dry_run:
            out.write(self.style.WARNING('SIMULAÇÃO (--dry-run): nada foi gravado no banco.'))
        else:
            out.write(self.style.SUCCESS('Importação concluída e gravada no banco.'))

        out.write('\nRegistros:')
        for label in ['Dificuldades', 'Grupos Musculares', 'Equipamentos', 'Exercícios', 'Alternativas']:
            entry = self.stats.get(label, {'criados': 0, 'atualizados': 0})
            out.write(f'  {label}: {entry["criados"]} criados, {entry["atualizados"]} atualizados')

        self.write_list(f'Avisos da leitura ({len(self.warnings)}):', self.warnings)
        self.write_list(f'Regras do app não atendidas ({len(self.rule_problems)}):', self.rule_problems)
        self.write_list(f'Exercícios com dados faltando ({len(incomplete)}):', incomplete)

        if ignored_steps:
            out.write('\nA aba "Passos de Execução" foi ignorada: a tabela de passos ainda não existe no banco.')

    def write_list(self, title, items):
        self.stdout.write(f'\n{title}')
        if not items:
            self.stdout.write('  (nenhum)')
        for item in items:
            self.stdout.write(self.style.WARNING(f'  - {item}'))
