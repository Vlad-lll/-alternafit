/**
 * DADOS
 * A partir daqui o formato segue exatamente a planilha que o time de
 * Educação Física está preenchendo (abas: Dificuldades, Grupos Musculares,
 * Equipamentos, Exercícios, Alternativas, Passos de Execução).
 *
 * O exercício "Supino Reto com Barra" usa o exemplo real já preenchido na
 * planilha. Os outros dois ("Agachamento Livre" e "Puxada Alta") ainda são
 * dados fictícios meus, só pra a tela não ficar vazia enquanto o time
 * termina de preencher o resto.
 *
 * Quando a API do Django estiver pronta, essas mesmas estruturas viram a
 * resposta do banco de dados, sem precisar mudar os componentes.
 */

export const DIFICULDADES = [
  { nivel: 1, nome: "Iniciante", descricao: "Movimento simples, baixo risco de lesão, ideal para quem nunca treinou" },
  { nivel: 2, nome: "Intermediário", descricao: "Exige coordenação, controle de peso corporal ou técnica moderada" },
  { nivel: 3, nome: "Avançado", descricao: "Exige força, equilíbrio ou mobilidade significativos, maior risco se mal executado" },
];

export function nomeDificuldade(nivel) {
  return DIFICULDADES.find((d) => d.nivel === nivel)?.nome ?? "A definir";
}

export const GRUPOS_MUSCULARES = [
  "Peitoral",
  "Deltoides",
  "Tríceps",
  "Bíceps",
  "Dorsal (Latíssimo)",
  "Trapézio",
  "Lombar",
  "Quadríceps",
  "Posterior de coxa",
  "Glúteos",
  "Panturrilha",
  "Abdômen",
  "Antebraço",
];

export const EQUIPAMENTOS = [
  "Barra reta",
  "Halteres",
  "Banco reto",
  "Banco inclinado",
  "Máquina Smith",
  "Polia (cabo)",
  "Barra fixa",
  "Kettlebell",
  "Elástico de resistência",
  "Nenhum (peso do corpo)",
];

export const EXERCICIOS = [
  {
    codigo: "EX-001",
    nome: "Supino Reto com Barra",
    descricao: "Exercício de empurro para o peitoral, feito deitado em banco reto",
    dificuldade: 2,
    gruposMusculares: ["Peitoral", "Tríceps", "Deltoides"],
    precisaEquipamento: true,
    equipamentos: ["Barra reta", "Banco reto"],
    dica: "Mantenha os cotovelos levemente para dentro (não a 90°), não trave o cotovelo no topo do movimento.",
    videoUrl: "https://exemplo.com/video-supino",
    passos: [
      {
        ordem: 1,
        descricao: "Deite no banco com os pés apoiados no chão e retire a barra do suporte",
        dicaExtra: "Mantenha as escápulas retraídas contra o banco",
      },
    ],
    alternativas: [
      {
        codigo: null, // esse exercício ainda não tem registro completo na aba Exercícios
        nome: "Flexão de Braço",
        ordemPrioridade: 1,
        semEquipamento: true,
        dificuldade: null,
        dica: null,
      },
    ],
  },
  {
    codigo: "EX-MOCK-002",
    nome: "Agachamento Livre",
    descricao: "Exercício composto para membros inferiores, feito com barra nas costas",
    dificuldade: 2,
    gruposMusculares: ["Quadríceps", "Glúteos"],
    precisaEquipamento: true,
    equipamentos: ["Barra reta"],
    dica: "Desça controlando o movimento, mantendo o peso nos calcanhares.",
    videoUrl: null,
    passos: [],
    alternativas: [
      {
        codigo: null,
        nome: "Afundo (Lunge)",
        ordemPrioridade: 1,
        semEquipamento: true,
        dificuldade: 1,
        dica: "Desça até a coxa de trás quase tocar o chão, joelho da frente alinhado ao pé.",
      },
      {
        codigo: null,
        nome: "Agachamento Búlgaro",
        ordemPrioridade: 2,
        semEquipamento: false,
        dificuldade: 3,
        dica: "Apoie o pé de trás em um banco e mantenha o tronco levemente inclinado.",
      },
      {
        codigo: null,
        nome: "Cadeira Extensora",
        ordemPrioridade: 3,
        semEquipamento: false,
        dificuldade: 1,
        dica: "Evite travar o joelho no topo do movimento.",
      },
    ],
  },
  {
    codigo: "EX-MOCK-003",
    nome: "Puxada Alta",
    descricao: "Exercício de puxada vertical, feito na polia",
    dificuldade: 1,
    gruposMusculares: ["Dorsal (Latíssimo)", "Bíceps"],
    precisaEquipamento: true,
    equipamentos: ["Polia (cabo)"],
    dica: "Puxe levando os cotovelos para baixo e para trás, sem balançar o tronco.",
    videoUrl: null,
    passos: [],
    alternativas: [
      {
        codigo: null,
        nome: "Remada Invertida",
        ordemPrioridade: 1,
        semEquipamento: true,
        dificuldade: 2,
        dica: "Use uma barra fixa na altura da cintura e puxe o peito em direção a ela.",
      },
      {
        codigo: null,
        nome: "Remada Unilateral com Halter",
        ordemPrioridade: 2,
        semEquipamento: false,
        dificuldade: 1,
        dica: "Apoie um joelho no banco e puxe o cotovelo em direção ao quadril.",
      },
    ],
  },
];

/** Busca um exercício pelo nome (ou parte dele). Case insensitive. */
export function buscarPorNome(termo) {
  const chave = termo.trim().toLowerCase();
  if (!chave) return null;
  return (
    EXERCICIOS.find((ex) => ex.nome.toLowerCase() === chave) ||
    EXERCICIOS.find((ex) => ex.nome.toLowerCase().includes(chave)) ||
    null
  );
}

/** Retorna todos os exercícios que têm o grupo muscular informado. */
export function buscarPorGrupoMuscular(grupo) {
  return EXERCICIOS.filter((ex) => ex.gruposMusculares.includes(grupo));
}

/** Rótulo do badge de uma alternativa, direto a partir do flag semEquipamento (igual à planilha). */
export function rotuloEquipamento(alternativa) {
  if (alternativa.semEquipamento) return "Calistenia (Sem Aparelho)";
  return "Precisa de equipamento";
}

export const FILTROS_EQUIPAMENTO = ["Todos", "Sem Equipamento", "Com Equipamento"];
