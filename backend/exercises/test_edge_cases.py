"""
Bateria de testes de uso anormal: entradas estranhas na API, métodos errados,
ações "sem sentido" no Admin e planilhas quebradas no importador.

A regra é sempre a mesma: o sistema pode recusar, mas tem que recusar de forma
educada (lista vazia, 404, 405, mensagem de erro). Nunca pode quebrar com erro
500 nem apagar dados por engano.
"""

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from openpyxl import Workbook
from rest_framework.test import APITestCase

from users.models import User

from .management.commands.importar_planilha import SHEETS
from .models import (
    Difficulty,
    Equipment,
    Exercise,
    ExerciseAlias,
    ExerciseAlternative,
    ExerciseMuscularGroup,
    MovementPattern,
    MuscularGroup,
)

PRIMARY = ExerciseMuscularGroup.Role.PRIMARY
SECONDARY = ExerciseMuscularGroup.Role.SECONDARY


def create_catalog():
    """Catálogo pequeno usado pelos testes de API e de Admin."""
    level = Difficulty.objects.create(name='Iniciante', level=1)
    push = MovementPattern.objects.create(code='EMPURRAR_HORIZONTAL', name='Empurrar horizontal')
    chest = MuscularGroup.objects.create(name='Peitoral')
    glutes = MuscularGroup.objects.create(name='Glúteos')
    bar = Equipment.objects.create(name='Barra reta')

    bench = Exercise.objects.create(name='Supino Reto com Barra', name_en='Barbell Bench Press',
                                    difficulty=level, movement_pattern=push)
    bench.equipment.set([bar])
    ExerciseMuscularGroup.objects.create(exercise=bench, muscular_group=chest, role=PRIMARY)

    push_up = Exercise.objects.create(name='Flexão de Braço', difficulty=level, movement_pattern=push)
    ExerciseMuscularGroup.objects.create(exercise=push_up, muscular_group=chest, role=PRIMARY)
    ExerciseAlias.objects.create(exercise=push_up, alias='Push-up')

    bridge = Exercise.objects.create(name='Elevação Pélvica', difficulty=level)
    ExerciseMuscularGroup.objects.create(exercise=bridge, muscular_group=glutes, role=PRIMARY)

    ExerciseAlternative.objects.create(exercise=bench, alternative=push_up, order=1)
    return {'bench': bench, 'push_up': push_up, 'bridge': bridge, 'chest': chest, 'level': level}


# =============================================================================
# API: entradas estranhas
# =============================================================================

WEIRD_SEARCHES = [
    '',                                     # busca vazia
    '   ',                                  # só espaços
    'a' * 5000,                             # texto enorme
    '%', '_', '%%%', '\\',                  # caracteres especiais do SQL LIKE
    "'", '"', '`',                          # aspas soltas
    "' OR 1=1 --",                          # tentativa de SQL injection
    "'; DROP TABLE exercises_exercise; --",
    '<script>alert(1)</script>',            # tentativa de injetar código na página
    '{{7*7}}', '${7*7}',                    # tentativas de injetar template
    '../../etc/passwd',
    '💪🏋️', '😀' * 200,                      # emojis
    '​',                               # caractere invisível
    '\x00',                                 # caractere nulo
    '\n\t\r',                               # quebras de linha e tab
    '12345', '-1', '0',                     # números
    'SELECT * FROM users_user',
    'ñ ç ã ß ø',                            # letras de outros idiomas
]


class WeirdApiInputTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.data = create_catalog()

    def test_weird_searches_never_break(self):
        for term in WEIRD_SEARCHES:
            with self.subTest(busca=repr(term[:30])):
                response = self.client.get('/api/exercicios/', {'busca': term})
                self.assertEqual(response.status_code, 200)
                self.assertIsInstance(response.json(), list)

    def test_sql_injection_does_not_touch_the_database(self):
        self.client.get('/api/exercicios/', {'busca': "'; DROP TABLE exercises_exercise; --"})

        self.assertEqual(Exercise.objects.count(), 3)

    def test_like_wildcards_are_treated_as_plain_text(self):
        for term in ['%', '_', '%%%', '\\']:
            with self.subTest(busca=term):
                self.assertEqual(self.client.get('/api/exercicios/', {'busca': term}).json(), [])

    def test_blank_search_behaves_like_no_search(self):
        everything = self.client.get('/api/exercicios/').json()

        for term in ['', '   ', '\n\t\r']:
            with self.subTest(busca=repr(term)):
                self.assertEqual(self.client.get('/api/exercicios/', {'busca': term}).json(), everything)

    def test_search_ignores_case_accents_and_extra_spaces(self):
        for term in ['FLEXÃO DE BRAÇO', 'flexao de braco', '  Flexão de Braço  ', 'fLeXaO']:
            with self.subTest(busca=term):
                names = [e['nome'] for e in self.client.get('/api/exercicios/', {'busca': term}).json()]
                self.assertEqual(names[0], 'Flexão de Braço')

    def test_repeated_search_parameter_uses_the_last_one(self):
        response = self.client.get('/api/exercicios/?busca=supino&busca=flexao')

        self.assertEqual([e['nome'] for e in response.json()], ['Flexão de Braço'])

    def test_unknown_parameters_are_ignored(self):
        response = self.client.get('/api/exercicios/', {'ordenar': 'hack', 'limite': '-5', 'page': 'abc'})

        self.assertEqual(len(response.json()), 3)

    def test_weird_group_filters_never_break(self):
        for group in ['Inexistente', "' OR 1=1 --", '<b>', '💪', '\x00', '12345', 'a' * 3000]:
            with self.subTest(grupo=repr(group[:30])):
                response = self.client.get('/api/exercicios/', {'grupo': group})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), [])

    def test_group_filter_ignores_case_and_accents(self):
        for group in ['Glúteos', 'gluteos', 'GLÚTEOS', '  glúteos  ']:
            with self.subTest(grupo=group):
                names = [e['nome'] for e in self.client.get('/api/exercicios/', {'grupo': group}).json()]
                self.assertEqual(names, ['Elevação Pélvica'])

    def test_search_and_group_together(self):
        response = self.client.get('/api/exercicios/', {'busca': 'flexão', 'grupo': 'Peitoral'})

        self.assertEqual([e['nome'] for e in response.json()], ['Flexão de Braço'])

    def test_invalid_exercise_codes_return_404(self):
        for code in ['999999', '0', '-1', 'abc', '1.5', '99999999999999999999999999', '%27', 'null', 'undefined']:
            with self.subTest(codigo=code):
                self.assertEqual(self.client.get(f'/api/exercicios/{code}/').status_code, 404)

    def test_invalid_group_codes_return_404(self):
        for code in ['999999', 'abc', '-1']:
            with self.subTest(codigo=code):
                self.assertEqual(self.client.get(f'/api/grupos-musculares/{code}/').status_code, 404)

    def test_unknown_api_address_returns_404(self):
        for path in ['/api/nao-existe/', '/api/exercicios/1/alternativas/', '/api/usuarios/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_nobody_can_change_data_through_the_api(self):
        detail = f'/api/exercicios/{self.data["bench"].id}/'
        attempts = [
            ('post', '/api/exercicios/'), ('put', detail), ('patch', detail), ('delete', detail),
            ('post', '/api/grupos-musculares/'), ('delete', f'/api/grupos-musculares/{self.data["chest"].id}/'),
        ]
        for method, path in attempts:
            with self.subTest(metodo=method, path=path):
                response = getattr(self.client, method)(path, {'nome': 'Hackeado'}, format='json')
                self.assertEqual(response.status_code, 405)
        self.assertEqual(Exercise.objects.get(id=self.data['bench'].id).name, 'Supino Reto com Barra')
        self.assertEqual(Exercise.objects.count(), 3)

    def test_head_and_options_requests_work(self):
        self.assertEqual(self.client.head('/api/exercicios/').status_code, 200)
        self.assertEqual(self.client.options('/api/exercicios/').status_code, 200)

    def test_response_formats(self):
        self.assertEqual(self.client.get('/api/exercicios/', {'format': 'json'}).status_code, 200)
        self.assertEqual(self.client.get('/api/exercicios/', HTTP_ACCEPT='text/html').status_code, 200)
        self.assertEqual(self.client.get('/api/exercicios/', {'format': 'xml'}).status_code, 404)

    def test_cors_blocks_unknown_sites(self):
        response = self.client.get('/api/exercicios/', HTTP_ORIGIN='https://site-malicioso.com')

        self.assertNotIn('Access-Control-Allow-Origin', response)

    def test_cors_preflight_from_the_app(self):
        response = self.client.options(
            '/api/exercicios/', HTTP_ORIGIN='http://localhost:5173', HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://localhost:5173')

    def test_list_does_not_get_slower_with_more_exercises(self):
        """Evita o problema "N+1": o número de consultas ao banco não pode crescer com o número de exercícios."""
        with CaptureQueriesContext(connection) as small:
            self.client.get('/api/exercicios/')
        for n in range(10):
            extra = Exercise.objects.create(name=f'Exercício extra {n}')
            ExerciseMuscularGroup.objects.create(exercise=extra, muscular_group=self.data['chest'], role=SECONDARY)
            ExerciseAlternative.objects.create(exercise=extra, alternative=self.data['push_up'], order=1)
        with CaptureQueriesContext(connection) as big:
            self.client.get('/api/exercicios/')

        self.assertEqual(len(small), len(big))


# =============================================================================
# Admin: ações "sem sentido"
# =============================================================================

class WeirdAdminUsageTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.data = create_catalog()
        cls.admin = User.objects.create_superuser('admin_teste', 'admin@exemplo.com', 'senha-de-teste-123')

    def setUp(self):
        self.client.force_login(self.admin)

    def test_admin_requires_login(self):
        self.client.logout()

        response = self.client.get('/admin/exercises/exercise/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_every_admin_page_opens(self):
        pages = [
            '/admin/', '/admin/exercises/exercise/', '/admin/exercises/exercise/add/',
            f'/admin/exercises/exercise/{self.data["bench"].id}/change/',
            '/admin/exercises/exercisealternative/', '/admin/exercises/exercisealternative/add/',
            '/admin/exercises/musculargroup/', '/admin/exercises/equipment/', '/admin/exercises/difficulty/',
            '/admin/exercises/movementpattern/', '/admin/exercises/source/', '/admin/users/user/',
        ]
        for page in pages:
            with self.subTest(page=page):
                self.assertEqual(self.client.get(page).status_code, 200)

    def test_admin_filters_and_search_with_weird_values(self):
        urls = [
            '/admin/exercises/exercise/?sem_equipamento=sim',
            '/admin/exercises/exercise/?sem_equipamento=nao',
            '/admin/exercises/exercise/?sem_equipamento=talvez',
            '/admin/exercises/exercisealternative/?sem_equipamento=sim',
            '/admin/exercises/exercise/?q=%3Cscript%3E',
            "/admin/exercises/exercise/?q=' OR 1=1 --",
            '/admin/exercises/exercise/?difficulty__id__exact=abc',
            '/admin/exercises/exercise/?campo_que_nao_existe=1',
        ]
        for url in urls:
            with self.subTest(url=url):
                # 200 (página normal) ou 302 (o Admin ignora o filtro inválido e redireciona). Nunca 500.
                self.assertIn(self.client.get(url).status_code, (200, 302))

    def test_equipment_free_filter_is_correct(self):
        response = self.client.get('/admin/exercises/exercise/?sem_equipamento=sim')

        self.assertContains(response, 'Flexão de Braço')
        self.assertNotContains(response, 'Supino Reto com Barra')

    def test_exercise_cannot_be_its_own_alternative_in_admin(self):
        bench = self.data['bench']
        response = self.client.post('/admin/exercises/exercisealternative/add/', {
            'exercise': bench.id, 'alternative': bench.id, 'order': 1, 'note': '',
        })

        self.assertEqual(response.status_code, 200)  # volta para o formulário com a mensagem de erro
        self.assertFalse(ExerciseAlternative.objects.filter(exercise=bench, alternative=bench).exists())

    def test_duplicate_alternative_in_admin_is_refused(self):
        response = self.client.post('/admin/exercises/exercisealternative/add/', {
            'exercise': self.data['bench'].id, 'alternative': self.data['push_up'].id, 'order': 2, 'note': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ExerciseAlternative.objects.count(), 1)

    def test_negative_or_text_order_is_refused(self):
        for order in ['-1', 'abc', '']:
            with self.subTest(ordem=order):
                response = self.client.post('/admin/exercises/exercisealternative/add/', {
                    'exercise': self.data['push_up'].id, 'alternative': self.data['bridge'].id, 'order': order,
                })
                self.assertEqual(response.status_code, 200)
        self.assertEqual(ExerciseAlternative.objects.count(), 1)

    def test_cannot_delete_a_muscular_group_in_use(self):
        chest = self.data['chest']

        response = self.client.post(f'/admin/exercises/musculargroup/{chest.id}/delete/', {'post': 'yes'})

        self.assertEqual(response.status_code, 200)  # o Admin explica por que não pode apagar
        self.assertTrue(MuscularGroup.objects.filter(id=chest.id).exists())

    def test_cannot_delete_a_difficulty_in_use(self):
        level = self.data['level']

        self.client.post(f'/admin/exercises/difficulty/{level.id}/delete/', {'post': 'yes'})

        self.assertTrue(Difficulty.objects.filter(id=level.id).exists())

    def test_difficulty_level_outside_1_to_3_is_refused(self):
        for level in ['0', '4', '-1', '999']:
            with self.subTest(nivel=level):
                response = self.client.post('/admin/exercises/difficulty/add/', {'name': f'Nível {level}', 'level': level})
                self.assertEqual(response.status_code, 200)
        self.assertEqual(Difficulty.objects.count(), 1)

    def test_invalid_video_link_is_refused(self):
        bench = self.data['bench']
        response = self.client.post(f'/admin/exercises/exercise/{bench.id}/change/', {
            'name': bench.name, 'video_url': 'isso não é um link',
            'muscular_group_links-TOTAL_FORMS': '0', 'muscular_group_links-INITIAL_FORMS': '0',
            'alternative_links-TOTAL_FORMS': '0', 'alternative_links-INITIAL_FORMS': '0',
            'steps-TOTAL_FORMS': '0', 'steps-INITIAL_FORMS': '0',
            'aliases-TOTAL_FORMS': '0', 'aliases-INITIAL_FORMS': '0',
        })

        self.assertEqual(response.status_code, 200)
        bench.refresh_from_db()
        self.assertEqual(bench.video_url, '')


# =============================================================================
# Importador: planilhas quebradas
# =============================================================================

VALID_ROWS = {
    'nivel_dificuldade': [[1, 'Iniciante', ''], [2, 'Intermediário', ''], [3, 'Avançado', '']],
    'grupo_muscular': [[1, 'PEITORAL', 'Peitoral', 'Superior', ''], [2, 'TRICEPS', 'Tríceps', 'Superior', '']],
    'equipamento': [[1, 'Barra reta', 'Peso livre', '']],
    'padrao_movimento': [[1, 'EMPURRAR_HORIZONTAL', 'Empurrar horizontal']],
    'fonte': [[1, 'ACE', 'Push-Up', 'https://www.acefitness.org/push-up', 'Biblioteca']],
    'exercicio': [
        [10, 'Supino Reto com Barra', 'Bench Press', 'Desc', 2, 1, 'Dica', '', 'Com fonte', ''],
        [20, 'Flexão de Braço', 'Push-up', 'Desc', 2, 1, 'Dica', '', 'Com fonte', ''],
        [30, 'Flexão Diamante', 'Diamond Push-up', 'Desc', 2, 1, 'Dica', '', 'Com fonte', ''],
    ],
    'exercicio_grupo_muscular': [[10, 1, 'PRIMARIO'], [20, 1, 'PRIMARIO'], [30, 2, 'PRIMARIO']],
    'exercicio_equipamento': [[10, 1]],
    'exercicio_alternativo': [[10, 20, 1, ''], [10, 30, 2, ''], [20, 30, 1, ''], [20, 10, 2, ''],
                              [30, 20, 1, ''], [30, 10, 2, '']],
    'exercicio_passo': [[10, 1, 'Deite no banco', '']],
    'exercicio_apelido': [[20, 'Apoio']],
    'exercicio_fonte': [[20, 1]],
}


class BrokenSpreadsheetTests(APITestCase):
    """Cada teste quebra a planilha de um jeito diferente."""

    def setUp(self):
        # Um exercício que já está no banco: se a importação recusar a planilha, ele precisa continuar lá.
        Exercise.objects.create(name='Exercício que já estava no banco')
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def build(self, changes=None, drop_sheets=(), drop_columns=None, extra_columns=None):
        rows = {sheet: [list(row) for row in values] for sheet, values in VALID_ROWS.items()}
        rows.update(changes or {})
        workbook = Workbook()
        workbook.remove(workbook.active)
        for sheet, columns in SHEETS.items():
            if sheet in drop_sheets:
                continue
            columns = [c for c in columns if c not in (drop_columns or {}).get(sheet, [])]
            extra = (extra_columns or {}).get(sheet, [])
            worksheet = workbook.create_sheet(sheet)
            worksheet.append(columns + extra)
            for row in rows[sheet]:
                worksheet.append(row[:len(columns)] + ['valor extra'] * len(extra))
        path = Path(self.directory.name) / 'planilha.xlsx'
        workbook.save(path)
        return path

    def run_import(self, path, *extra):
        output = StringIO()
        call_command('importar_planilha', str(path), *extra, stdout=output)
        return output.getvalue()

    def assert_refused(self, path, message_part=''):
        output = StringIO()
        with self.assertRaises(CommandError) as raised:
            call_command('importar_planilha', str(path), stdout=output)
        self.assertIn(message_part, str(raised.exception) + output.getvalue())
        self.assertTrue(Exercise.objects.filter(name='Exercício que já estava no banco').exists())

    def test_file_does_not_exist(self):
        self.assert_refused(Path(self.directory.name) / 'nao_existe.xlsx', 'não encontrado')

    def test_file_is_not_a_spreadsheet(self):
        path = Path(self.directory.name) / 'texto.xlsx'
        path.write_text('isto é um arquivo de texto com nome de planilha', encoding='utf-8')

        self.assert_refused(path, 'não é uma planilha')

    def test_folder_instead_of_file(self):
        self.assert_refused(Path(self.directory.name), 'não é uma planilha')

    def test_old_format_spreadsheet(self):
        self.assert_refused(self.build(drop_sheets=['exercicio_alternativo']), 'exercicio_alternativo')

    def test_missing_column(self):
        self.assert_refused(self.build(drop_columns={'exercicio': ['nome']}), 'faltam as colunas')

    def test_empty_catalog_is_refused_instead_of_erasing_everything(self):
        empty = {sheet: [] for sheet in VALID_ROWS}

        self.assert_refused(self.build(changes=empty), 'nenhum exercício')

    def test_duplicate_exercise_id(self):
        rows = VALID_ROWS['exercicio'] + [[10, 'Outro Exercício', '', '', 1, 1, '', '', 'Com fonte', '']]

        self.assert_refused(self.build({'exercicio': rows}), 'repetido')

    def test_same_name_with_different_case_and_accents(self):
        rows = VALID_ROWS['exercicio'] + [[40, 'flexao de braco', '', '', 1, 1, '', '', 'Com fonte', '']]

        self.assert_refused(self.build({'exercicio': rows}), 'repetido')

    def test_reference_to_missing_muscular_group(self):
        rows = VALID_ROWS['exercicio_grupo_muscular'] + [[10, 99, 'SECUNDARIO']]

        self.assert_refused(self.build({'exercicio_grupo_muscular': rows}), 'não existe')

    def test_alternative_pointing_to_missing_exercise(self):
        rows = VALID_ROWS['exercicio_alternativo'] + [[10, 999, 3, '']]

        self.assert_refused(self.build({'exercicio_alternativo': rows}), 'não existe')

    def test_exercise_as_its_own_alternative(self):
        rows = VALID_ROWS['exercicio_alternativo'] + [[10, 10, 3, '']]

        self.assert_refused(self.build({'exercicio_alternativo': rows}), 'si mesmo')

    def test_alias_equal_to_another_exercise_name(self):
        rows = VALID_ROWS['exercicio_apelido'] + [[10, 'Flexão Diamante']]

        self.assert_refused(self.build({'exercicio_apelido': rows}), 'nome de outro exercício')

    def test_invalid_role(self):
        rows = [[10, 1, 'PRINCIPALZAO'], [20, 1, 'PRIMARIO'], [30, 2, 'PRIMARIO']]

        self.assert_refused(self.build({'exercicio_grupo_muscular': rows}), 'papel')

    def test_invalid_order(self):
        for order in [0, -3, 'primeiro', 1.5]:
            with self.subTest(ordem=order):
                rows = [[10, 20, order, '']] + VALID_ROWS['exercicio_alternativo'][1:]
                self.assert_refused(self.build({'exercicio_alternativo': rows}), 'ordem')

    def test_invalid_ids(self):
        for bad_id in ['abc', -5, 0, 2.5, '']:
            with self.subTest(id=bad_id):
                rows = VALID_ROWS['exercicio'] + [[bad_id, 'Exercício Novo', '', '', 1, 1, '', '', 'Com fonte', '']]
                self.assert_refused(self.build({'exercicio': rows}), 'id')

    def test_level_that_does_not_exist(self):
        rows = [[10, 'Supino Reto com Barra', '', '', 7, 1, '', '', 'Com fonte', '']] + VALID_ROWS['exercicio'][1:]

        self.assert_refused(self.build({'exercicio': rows}), 'nivel_id')

    def test_name_longer_than_the_database_allows(self):
        rows = [[10, 'Supino ' + 'muito ' * 40, '', '', 2, 1, '', '', 'Com fonte', '']] + VALID_ROWS['exercicio'][1:]

        self.assert_refused(self.build({'exercicio': rows}), 'caracteres')

    def test_invalid_source_url(self):
        rows = [[1, 'ACE', 'Push-Up', 'isso não é um link', 'Biblioteca']]

        self.assert_refused(self.build({'fonte': rows}), 'URL inválida')

    def test_invalid_video_url_becomes_a_warning(self):
        rows = [[10, 'Supino Reto com Barra', '', '', 2, 1, '', 'link quebrado', 'Com fonte', '']] + VALID_ROWS['exercicio'][1:]

        output = self.run_import(self.build({'exercicio': rows}))

        self.assertIn('link de vídeo inválido', output)
        self.assertEqual(Exercise.objects.get(id=10).video_url, '')

    def test_extra_spaces_and_numbers_as_decimals_are_accepted(self):
        rows = [[10.0, '  Supino Reto com Barra  ', '', '', 2.0, 1, '', '', 'Com fonte', '']] + VALID_ROWS['exercicio'][1:]

        self.run_import(self.build({'exercicio': rows}))

        self.assertEqual(Exercise.objects.get(id=10).name, 'Supino Reto com Barra')

    def test_extra_columns_and_blank_rows_are_ignored(self):
        rows = VALID_ROWS['exercicio'][:1] + [[None] * 10, [None] * 10] + VALID_ROWS['exercicio'][1:]

        self.run_import(self.build({'exercicio': rows}, extra_columns={'exercicio': ['_calc_qualquer', 'anotacao']}))

        self.assertEqual(Exercise.objects.count(), 3)

    def test_exercise_without_alternatives_is_imported_but_reported(self):
        rows = VALID_ROWS['exercicio_alternativo'][:4]  # o exercício 30 fica sem alternativas

        output = self.run_import(self.build({'exercicio_alternativo': rows}))

        self.assertIn('"Flexão Diamante" tem 0 alternativa(s)', output)
        self.assertTrue(Exercise.objects.filter(id=30).exists())

    def test_importing_twice_gives_the_same_result(self):
        path = self.build()

        self.run_import(path)
        first = list(Exercise.objects.order_by('id').values_list('id', 'name'))
        self.run_import(path)
        second = list(Exercise.objects.order_by('id').values_list('id', 'name'))

        self.assertEqual(first, second)
        self.assertEqual(ExerciseAlternative.objects.count(), 6)
