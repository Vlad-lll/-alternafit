"""
Testes da API e do importador. Conferem o "contrato" com o frontend: se algum
nome de campo ou comportamento mudar, estes testes falham e avisam antes de
quebrar o app.

Rodar (dentro de backend/):
    venv\\Scripts\\python.exe manage.py test
"""

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from openpyxl import Workbook
from rest_framework.test import APITestCase

from .management.commands.importar_planilha import SHEETS
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
)

PRIMARY = ExerciseMuscularGroup.Role.PRIMARY
SECONDARY = ExerciseMuscularGroup.Role.SECONDARY


class ExerciseApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        intermediate = Difficulty.objects.create(name='Intermediário', level=2)
        push = MovementPattern.objects.create(code='EMPURRAR_HORIZONTAL', name='Empurrar horizontal')
        cls.chest = MuscularGroup.objects.create(name='Peitoral', region=MuscularGroup.Region.UPPER)
        triceps = MuscularGroup.objects.create(name='Tríceps')
        glutes = MuscularGroup.objects.create(name='Glúteos')
        quads = MuscularGroup.objects.create(name='Quadríceps')
        bar = Equipment.objects.create(name='Barra reta')

        cls.bench_press = Exercise.objects.create(
            name='Supino reto com barra',
            name_en='Barbell Bench Press',
            description='Empurrar a barra deitado no banco',
            tip='Não trave os cotovelos',
            video_url='https://exemplo.com/supino',
            difficulty=intermediate,
            movement_pattern=push,
        )
        cls.bench_press.equipment.set([bar])
        ExerciseMuscularGroup.objects.create(exercise=cls.bench_press, muscular_group=triceps, role=SECONDARY)
        ExerciseMuscularGroup.objects.create(exercise=cls.bench_press, muscular_group=cls.chest, role=PRIMARY)
        ExerciseStep.objects.create(exercise=cls.bench_press, order=1, description='Deite no banco')

        cls.push_up = Exercise.objects.create(name='Flexão de braço')
        ExerciseMuscularGroup.objects.create(exercise=cls.push_up, muscular_group=cls.chest, role=PRIMARY)
        ExerciseAlias.objects.create(exercise=cls.push_up, alias='Push-up')

        cls.pull_up = Exercise.objects.create(name='Barra fixa')
        # Vem antes de "Barra fixa" em ordem alfabética, mas não é o nome exato.
        Exercise.objects.create(name='Abdominal na barra fixa')

        # Glúteos: "Agachamento" (auxiliar) vem antes em ordem alfabética,
        # mas "Elevação pélvica" (principal) deve aparecer primeiro.
        squat = Exercise.objects.create(name='Agachamento')
        ExerciseMuscularGroup.objects.create(exercise=squat, muscular_group=quads, role=PRIMARY)
        ExerciseMuscularGroup.objects.create(exercise=squat, muscular_group=glutes, role=SECONDARY)
        hip_thrust = Exercise.objects.create(name='Elevação pélvica')
        ExerciseMuscularGroup.objects.create(exercise=hip_thrust, muscular_group=glutes, role=PRIMARY)

        ExerciseAlternative.objects.create(
            exercise=cls.bench_press, alternative=cls.push_up, order=1, note='Mesmo padrão de movimento'
        )

    def test_exercise_has_the_fields_the_frontend_expects(self):
        response = self.client.get(f'/api/exercicios/{self.bench_press.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['codigo'], self.bench_press.id)
        self.assertEqual(data['nome'], 'Supino reto com barra')
        self.assertEqual(data['nomeEn'], 'Barbell Bench Press')
        self.assertEqual(data['dificuldade'], 2)
        self.assertEqual(data['padraoMovimento'], 'Empurrar horizontal')
        self.assertEqual(data['equipamentos'], ['Barra reta'])
        self.assertTrue(data['precisaEquipamento'])
        self.assertFalse(data['semEquipamento'])
        self.assertEqual(data['dica'], 'Não trave os cotovelos')
        self.assertEqual(data['videoUrl'], 'https://exemplo.com/supino')
        self.assertEqual(data['passos'], [{'ordem': 1, 'descricao': 'Deite no banco', 'dicaExtra': ''}])

    def test_primary_muscular_group_comes_first(self):
        data = self.client.get(f'/api/exercicios/{self.bench_press.id}/').json()

        self.assertEqual(data['gruposMusculares'], ['Peitoral', 'Tríceps'])
        self.assertEqual(data['gruposPrincipais'], ['Peitoral'])
        self.assertEqual(data['gruposAuxiliares'], ['Tríceps'])

    def test_alternatives_have_the_fields_the_card_expects(self):
        data = self.client.get(f'/api/exercicios/{self.bench_press.id}/').json()

        self.assertEqual(data['alternativas'], [{
            'codigo': self.push_up.id,
            'nome': 'Flexão de braço',
            'ordemPrioridade': 1,
            'semEquipamento': True,
            'dificuldade': None,
            'dica': '',
            'videoUrl': '',
            'observacao': 'Mesmo padrão de movimento',
        }])

    def test_search_returns_exact_name_first(self):
        data = self.client.get('/api/exercicios/', {'busca': 'barra fixa'}).json()

        self.assertEqual([e['nome'] for e in data], ['Barra fixa', 'Abdominal na barra fixa'])

    def test_search_ignores_case(self):
        data = self.client.get('/api/exercicios/', {'busca': 'SUPINO'}).json()

        self.assertEqual([e['nome'] for e in data], ['Supino reto com barra'])

    def test_search_finds_aliases_and_english_names(self):
        by_alias = self.client.get('/api/exercicios/', {'busca': 'push-up'}).json()
        by_english = self.client.get('/api/exercicios/', {'busca': 'bench press'}).json()

        self.assertEqual([e['nome'] for e in by_alias], ['Flexão de braço'])
        self.assertEqual([e['nome'] for e in by_english], ['Supino reto com barra'])

    def test_filter_by_group_lists_primary_focus_first(self):
        data = self.client.get('/api/exercicios/', {'grupo': 'Glúteos'}).json()

        self.assertEqual([e['nome'] for e in data], ['Elevação pélvica', 'Agachamento'])

    def test_list_muscular_groups(self):
        data = self.client.get('/api/grupos-musculares/').json()

        self.assertEqual([g['nome'] for g in data], ['Glúteos', 'Peitoral', 'Quadríceps', 'Tríceps'])
        self.assertEqual(data[1]['regiao'], 'Superior')

    def test_api_is_read_only(self):
        response = self.client.post('/api/exercicios/', {'nome': 'Novo'}, format='json')

        self.assertEqual(response.status_code, 405)

    def test_frontend_dev_server_is_allowed_by_cors(self):
        response = self.client.get('/api/exercicios/', HTTP_ORIGIN='http://localhost:5173')

        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://localhost:5173')


class ImportSpreadsheetTests(APITestCase):
    """Monta uma planilha pequena no formato v2.2+ e confere a importação."""

    ROWS = {
        'nivel_dificuldade': [[1, 'Iniciante', ''], [2, 'Intermediário', ''], [3, 'Avançado', '']],
        'grupo_muscular': [[1, 'PEITORAL', 'Peitoral', 'Superior', 'Peito'], [3, 'TRICEPS', 'Tríceps', 'Superior', '']],
        'equipamento': [[1, 'Barra reta', 'Peso livre', '']],
        'padrao_movimento': [[1, 'EMPURRAR_HORIZONTAL', 'Empurrar horizontal']],
        'fonte': [[1, 'ACE', 'Push-Up', 'https://www.acefitness.org/push-up', 'Biblioteca de exercícios']],
        'exercicio': [
            [10, 'Supino Reto com Barra', 'Bench Press', 'Desc', 2, 1, 'Dica', '', 'Com fonte', ''],
            [20, 'Flexão de Braço', 'Push-up', 'Desc', 2, 1, 'Dica', '', 'Com fonte', ''],
            [30, 'Flexão Diamante', 'Diamond Push-up', 'Desc', 2, 1, 'Dica', '', 'Com fonte', ''],
        ],
        'exercicio_grupo_muscular': [
            [10, 1, 'PRIMARIO'], [10, 3, 'SECUNDARIO'], [20, 1, 'PRIMARIO'], [30, 3, 'PRIMARIO'],
        ],
        'exercicio_equipamento': [[10, 1]],
        'exercicio_alternativo': [[10, 20, 1, ''], [10, 30, 2, ''], [20, 30, 1, ''], [20, 10, 2, ''],
                                  [30, 20, 1, ''], [30, 10, 2, '']],
        'exercicio_passo': [[10, 1, 'Deite no banco', '']],
        'exercicio_apelido': [[20, 'Apoio']],
        'exercicio_fonte': [[20, 1]],
    }

    def make_workbook(self, directory):
        workbook = Workbook()
        workbook.remove(workbook.active)
        for sheet, columns in SHEETS.items():
            worksheet = workbook.create_sheet(sheet)
            worksheet.append(columns)
            for row in self.ROWS[sheet]:
                worksheet.append(row)
        path = Path(directory) / 'planilha.xlsx'
        workbook.save(path)
        return path

    def run_import(self, *extra):
        with tempfile.TemporaryDirectory() as directory:
            call_command('importar_planilha', str(self.make_workbook(directory)), *extra, stdout=StringIO())

    def test_import_creates_catalog_with_spreadsheet_ids(self):
        self.run_import()

        bench_press = Exercise.objects.get(id=10)
        self.assertEqual(bench_press.name, 'Supino Reto com Barra')
        self.assertEqual(bench_press.difficulty.level, 2)
        self.assertFalse(bench_press.is_equipment_free)
        self.assertTrue(Exercise.objects.get(id=20).is_equipment_free)
        self.assertEqual(
            list(bench_press.muscular_group_links.values_list('muscular_group__name', 'role')),
            [('Peitoral', PRIMARY), ('Tríceps', SECONDARY)],
        )
        self.assertEqual(ExerciseAlternative.objects.count(), 6)
        self.assertEqual(MuscularGroup.objects.get(id=1).region, MuscularGroup.Region.UPPER)
        self.assertEqual(Exercise.objects.get(id=20).aliases.get().alias, 'Apoio')

    def test_import_replaces_previous_catalog(self):
        Exercise.objects.create(name='Exercício antigo de teste')

        self.run_import()

        self.assertFalse(Exercise.objects.filter(name='Exercício antigo de teste').exists())
        self.assertEqual(Exercise.objects.count(), 3)

    def test_dry_run_writes_nothing(self):
        Exercise.objects.create(name='Exercício antigo de teste')

        self.run_import('--dry-run')

        self.assertEqual(list(Exercise.objects.values_list('name', flat=True)), ['Exercício antigo de teste'])
