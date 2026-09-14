/**
 * SERVICE LAYER
 * Isola toda a "busca de dados" num só lugar. Hoje ele só repassa
 * para o mock em src/data/exercicios.js. Quando a API do Django
 * estiver pronta, troca-se o corpo destas funções por fetch/axios,
 * sem precisar tocar em nenhum componente que já usa este arquivo.
 *
 * Exemplo de como ficará no futuro (comentado):
 *
 * export async function buscarExercicioPorNome(termo) {
 *   const resposta = await fetch(`${BASE_URL}/exercicios/buscar?nome=${termo}`);
 *   if (!resposta.ok) throw new Error("Erro ao buscar exercício");
 *   return resposta.json();
 * }
 */

import {
  buscarPorNome,
  buscarPorGrupoMuscular,
  GRUPOS_MUSCULARES,
} from "../data/exercicios";

// const BASE_URL = "http://localhost:8000/api"; // usar quando o Django estiver no ar

export async function buscarExercicioPorNome(termo) {
  return Promise.resolve(buscarPorNome(termo));
}

export async function buscarExerciciosPorGrupoMuscular(grupo) {
  return Promise.resolve(buscarPorGrupoMuscular(grupo));
}

export async function obterGruposMusculares() {
  return Promise.resolve(GRUPOS_MUSCULARES);
}
