"""
Testes com os dados reais: importa a planilha oficial (pasta data/ na raiz do
repositório) num banco temporário e confere, pela API, todos os exercícios,
apelidos e grupos musculares. Se a planilha não estiver na pasta, os testes
são pulados.

Quando sair uma versão nova da planilha, atualize SPREADSHEET abaixo.
"""

import unicodedata
from io import StringIO
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.core.management import call_command
from rest_framework.test import APITestCase

from .models import ExerciseAlias

SPREADSHEET = Path(settings.BASE_DIR).parent / 'data' / 'alternafit_banco_exercicios_v2.3.xlsx'

# Exercícios que, de propósito, não têm alternativa sem equipamento (justificado na planilha).
KNOWN_EXCEPTIONS = {'Rosca de Bíceps com Autorresistência'}

EXERCISE_FIELDS = {
    'codigo', 'nome', 'nomeEn', 'descricao', 'dificuldade', 'padraoMovimento', 'gruposMusculares',
    'gruposPrincipais', 'gruposAuxiliares', 'precisaEquipamento', 'semEquipamento', 'equipamentos',
    'dica', 'videoUrl', 'apelidos', 'passos', 'fontes', 'alternativas',
}
ALTERNATIVE_FIELDS = {
    'codigo', 'nome', 'ordemPrioridade', 'semEquipamento', 'dificuldade', 'dica', 'videoUrl', 'observacao',
}


def fold(text):
    text = unicodedata.normalize('NFKD', text.strip().lower())
    return ''.join(ch for ch in text if not unicodedata.combining(ch))


@skipUnless(SPREADSHEET.exists(), f'planilha oficial não encontrada em {SPREADSHEET}')
class RealDataTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('importar_planilha', str(SPREADSHEET), stdout=StringIO())

    def setUp(self):
        self.exercises = self.client.get('/api/exercicios/').json()
        self.by_code = {e['codigo']: e for e in self.exercises}

    def search(self, term):
        return [e['codigo'] for e in self.client.get('/api/exercicios/', {'busca': term}).json()]

    def test_catalog_is_not_empty(self):
        self.assertGreater(len(self.exercises), 0)

    def test_every_exercise_has_the_fields_the_app_uses(self):
        for e in self.exercises:
            with self.subTest(exercicio=e['nome']):
                self.assertEqual(set(e), EXERCISE_FIELDS)
                for alternative in e['alternativas']:
                    self.assertEqual(set(alternative), ALTERNATIVE_FIELDS)

    def test_every_detail_page_matches_the_list(self):
        for code, e in self.by_code.items():
            with self.subTest(exercicio=e['nome']):
                response = self.client.get(f'/api/exercicios/{code}/')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), e)

    def test_every_alternative_points_to_an_existing_exercise(self):
        for e in self.exercises:
            for alternative in e['alternativas']:
                with self.subTest(exercicio=e['nome'], alternativa=alternative['nome']):
                    self.assertIn(alternative['codigo'], self.by_code)
                    self.assertEqual(self.by_code[alternative['codigo']]['nome'], alternative['nome'])

    def test_app_rules(self):
        for e in self.exercises:
            with self.subTest(exercicio=e['nome']):
                self.assertTrue(2 <= len(e['alternativas']) <= 4, f'{len(e["alternativas"])} alternativas')
                if e['nome'] not in KNOWN_EXCEPTIONS:
                    self.assertTrue(any(a['semEquipamento'] for a in e['alternativas']),
                                    'nenhuma alternativa sem equipamento')
                orders = [a['ordemPrioridade'] for a in e['alternativas']]
                self.assertEqual(orders, sorted(orders), 'alternativas fora de ordem')

    def test_muscular_groups_are_consistent(self):
        for e in self.exercises:
            with self.subTest(exercicio=e['nome']):
                self.assertGreaterEqual(len(e['gruposPrincipais']), 1)
                self.assertEqual(e['gruposMusculares'], e['gruposPrincipais'] + e['gruposAuxiliares'])

    def test_equipment_flags_are_consistent(self):
        for e in self.exercises:
            with self.subTest(exercicio=e['nome']):
                self.assertEqual(e['semEquipamento'], e['equipamentos'] == [])
                self.assertEqual(e['precisaEquipamento'], not e['semEquipamento'])
                self.assertIn(e['dificuldade'], (1, 2, 3))

    def test_texts_and_links_look_right(self):
        for e in self.exercises:
            with self.subTest(exercicio=e['nome']):
                self.assertEqual(e['nome'], e['nome'].strip())
                self.assertNotIn('<', e['nome'])
                self.assertTrue(e['dica'], 'sem dica de execução')
                if e['videoUrl']:
                    self.assertTrue(e['videoUrl'].startswith('https://'))
                    self.assertNotIn('exemplo.com', e['videoUrl'])
                for source in e['fontes']:
                    self.assertTrue(source['url'].startswith('http'))

    def test_no_two_exercises_have_the_same_name_ignoring_accents(self):
        names = [fold(e['nome']) for e in self.exercises]

        self.assertEqual(len(names), len(set(names)))

    def test_searching_each_exact_name_finds_that_exercise_first(self):
        for code, e in self.by_code.items():
            with self.subTest(exercicio=e['nome']):
                self.assertEqual(self.search(e['nome'])[0], code)

    def test_searching_each_name_without_accents_finds_that_exercise_first(self):
        for code, e in self.by_code.items():
            with self.subTest(exercicio=e['nome']):
                self.assertEqual(self.search(fold(e['nome']))[0], code)

    def test_searching_each_alias_finds_its_exercise_first(self):
        for alias in ExerciseAlias.objects.all():
            with self.subTest(apelido=alias.alias):
                self.assertEqual(self.search(alias.alias)[0], alias.exercise_id)

    def test_searching_each_english_name_finds_the_exercise(self):
        for code, e in self.by_code.items():
            if e['nomeEn']:
                with self.subTest(exercicio=e['nome'], ingles=e['nomeEn']):
                    self.assertIn(code, self.search(e['nomeEn']))

    def test_every_muscular_group_filter_works(self):
        groups = self.client.get('/api/grupos-musculares/').json()
        self.assertGreater(len(groups), 0)
        for group in groups:
            with self.subTest(grupo=group['nome']):
                results = self.client.get('/api/exercicios/', {'grupo': group['nome']}).json()
                self.assertGreater(len(results), 0, 'grupo sem nenhum exercício')
                for e in results:
                    self.assertIn(group['nome'], e['gruposMusculares'])
                is_primary = [group['nome'] in e['gruposPrincipais'] for e in results]
                self.assertEqual(is_primary, sorted(is_primary, reverse=True), 'auxiliares antes dos principais')
