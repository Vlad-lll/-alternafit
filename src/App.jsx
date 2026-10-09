import React, { useEffect, useRef, useState } from "react";
import Header from "./components/Header";
import SearchBar from "./components/SearchBar";
import FiltroChips from "./components/FiltroChips";
import CardPrincipal from "./components/CardPrincipal";
import CardAlternativa from "./components/CardAlternativa";
import ModalVideo from "./components/ModalVideo";
import { cores, fonte } from "./styles/theme";
import { FILTROS_EQUIPAMENTO } from "./data/exercicios";
import {
  buscarExercicioPorNome,
  buscarExerciciosPorGrupoMuscular,
  obterGruposMusculares,
} from "./services/api";

const MENSAGEM_ERRO =
  "Não foi possível falar com o servidor. Confira sua conexão e tente de novo.";

// Os favoritos ficam salvos no próprio navegador (localStorage), sem precisar de login.
const CHAVE_FAVORITOS = "alternafit:favoritos";

function lerFavoritosSalvos() {
  try {
    const salvos = JSON.parse(localStorage.getItem(CHAVE_FAVORITOS));
    if (!Array.isArray(salvos)) return [];
    // Mantém só códigos de exercício válidos (números inteiros), sem repetição
    return [...new Set(salvos.filter((id) => Number.isInteger(id) && id > 0))];
  } catch {
    return [];
  }
}

export default function App() {
  const [termoBusca, setTermoBusca] = useState("Supino Reto com Barra");
  const [exercicioAtivo, setExercicioAtivo] = useState(null);
  // Mensagem mostrada quando a busca não encontra nada (ou quando a busca está vazia)
  const [aviso, setAviso] = useState(null);

  const [grupos, setGrupos] = useState([]);
  const [grupoSelecionado, setGrupoSelecionado] = useState("Todos");
  const [exerciciosDoGrupo, setExerciciosDoGrupo] = useState([]);

  const [filtroEquipamento, setFiltroEquipamento] = useState("Todos");

  const [favoritos, setFavoritos] = useState(lerFavoritosSalvos);
  const [videoAberto, setVideoAberto] = useState(null);

  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);
  // Guarda a última consulta feita, para o botão "Tentar de novo" repetir exatamente ela
  const ultimaConsulta = useRef(null);
  // Número da consulta mais recente. Com internet lenta, uma resposta antiga pode chegar
  // depois de uma nova; esse número permite ignorar respostas que já ficaram velhas.
  const idConsulta = useRef(0);

  /**
   * Roda uma consulta à API mostrando "Carregando..." e, se falhar, a mensagem de erro.
   * A consulta recebe a função aindaAtual(), que diz se ela ainda é a mais recente.
   */
  async function comCarregamento(consulta) {
    const id = ++idConsulta.current;
    const aindaAtual = () => id === idConsulta.current;
    ultimaConsulta.current = consulta;
    setCarregando(true);
    setErro(null);
    try {
      await consulta(aindaAtual);
    } catch {
      if (aindaAtual()) setErro(MENSAGEM_ERRO);
    } finally {
      if (aindaAtual()) setCarregando(false);
    }
  }

  // Carrega o exercício inicial e a lista de grupos musculares (para os chips)
  function carregarInicio() {
    comCarregamento(async (aindaAtual) => {
      const [exercicio, listaGrupos] = await Promise.all([
        buscarExercicioPorNome("Supino Reto com Barra"),
        obterGruposMusculares(),
      ]);
      setGrupos(listaGrupos);
      if (aindaAtual()) setExercicioAtivo(exercicio);
    });
  }

  useEffect(carregarInicio, []);

  // Salva os favoritos no navegador sempre que a lista muda
  useEffect(() => {
    try {
      localStorage.setItem(CHAVE_FAVORITOS, JSON.stringify(favoritos));
    } catch {
      // Navegador sem armazenamento (ex.: modo privado): os favoritos valem só nesta visita.
    }
  }, [favoritos]);

  function buscar(e) {
    e.preventDefault();
    const termo = termoBusca.trim();
    if (!termo) {
      setAviso("Digite o nome de um exercício para buscar.");
      return;
    }
    comCarregamento(async (aindaAtual) => {
      const resultado = await buscarExercicioPorNome(termo);
      if (!aindaAtual()) return;
      if (resultado) {
        setExercicioAtivo(resultado);
        setAviso(null);
        setGrupoSelecionado("Todos");
        setFiltroEquipamento("Todos");
      } else {
        setAviso(
          `Nenhum exercício encontrado para "${termo}". Tente outro nome ou navegue por grupo muscular acima.`
        );
      }
    });
  }

  function selecionarGrupo(grupo) {
    setAviso(null);
    if (grupo === "Todos") {
      // Saindo de um grupo: descarta a resposta do grupo que ainda estava chegando
      if (grupoSelecionado !== "Todos") {
        idConsulta.current += 1;
        setCarregando(false);
      }
      setGrupoSelecionado(grupo);
      setExerciciosDoGrupo([]);
      return;
    }
    setGrupoSelecionado(grupo);
    comCarregamento(async (aindaAtual) => {
      setExerciciosDoGrupo([]);
      const lista = await buscarExerciciosPorGrupoMuscular(grupo);
      if (aindaAtual()) setExerciciosDoGrupo(lista);
    });
  }

  function escolherExercicioDoGrupo(exercicio) {
    setAviso(null);
    setExercicioAtivo(exercicio);
    setTermoBusca(exercicio.nome);
    setGrupoSelecionado("Todos");
    setFiltroEquipamento("Todos");
  }

  function toggleFavorito(id) {
    setFavoritos((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  }

  const alternativasFiltradas =
    exercicioAtivo?.alternativas.filter((alt) => {
      if (filtroEquipamento === "Todos") return true;
      if (filtroEquipamento === "Sem Equipamento") return alt.semEquipamento;
      return !alt.semEquipamento;
    }) ?? [];

  const navegandoPorGrupo = grupoSelecionado !== "Todos";

  return (
    <div
      style={{
        minHeight: "100vh",
        background: cores.fundo,
        fontFamily: fonte,
        color: cores.texto,
        paddingBottom: 60,
      }}
    >
      <Header totalFavoritos={favoritos.length} />

      {/* maxWidth reduzido de proposito: a ideia e simular um app de celular
          mesmo quando visto num navegador de PC, ja que o uso principal e mobile */}
      <main style={{ maxWidth: 480, margin: "0 auto", padding: "0 18px" }}>
        <section style={{ textAlign: "center", padding: "48px 0 32px" }}>
          <h1
            style={{
              fontSize: "clamp(26px, 4.5vw, 38px)",
              fontWeight: 900,
              lineHeight: 1.15,
              margin: "0 0 10px",
            }}
          >
            Aparelho ocupado? <span style={{ color: cores.orange }}>A gente resolve</span>
          </h1>
          <p style={{ color: cores.textoSecundario, fontSize: 15, maxWidth: 480, margin: "0 auto" }}>
            Busque um exercício e veja alternativas equivalentes, sempre com
            pelo menos uma opção sem aparelho.
          </p>

          <SearchBar valor={termoBusca} onChange={setTermoBusca} onSubmit={buscar} />

          <div style={{ marginTop: 20, maxWidth: 480, marginInline: "auto" }}>
            <FiltroChips
              titulo="Ou navegue por grupo muscular"
              opcoes={["Todos", ...grupos]}
              selecionado={grupoSelecionado}
              onSelecionar={selecionarGrupo}
            />
          </div>
        </section>

        {erro && (
          <div
            style={{
              background: cores.cardFundo,
              border: `1px solid ${cores.perigo}`,
              borderRadius: 16,
              padding: 24,
              textAlign: "center",
              color: cores.texto,
              marginBottom: 30,
            }}
          >
            <p style={{ margin: "0 0 14px" }}>{erro}</p>
            <button
              onClick={() => comCarregamento(ultimaConsulta.current)}
              style={{
                background: cores.navy,
                color: cores.navyTexto,
                border: "none",
                borderRadius: 12,
                padding: "10px 22px",
                minHeight: 44,
                fontWeight: 800,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              Tentar de novo
            </button>
          </div>
        )}

        {carregando && (
          <div style={{ textAlign: "center", color: cores.textoSecundario, fontSize: 14, marginBottom: 24 }}>
            Carregando...
          </div>
        )}

        {aviso && !erro && (
          <div
            style={{
              background: cores.cardFundo,
              border: `1px solid ${cores.borda}`,
              borderRadius: 16,
              padding: 24,
              textAlign: "center",
              color: cores.textoSecundario,
              marginBottom: 30,
              // Quebra palavras enormes (ex.: alguém colou um texto gigante) para não estourar a tela
              overflowWrap: "anywhere",
            }}
          >
            {aviso}
          </div>
        )}

        {navegandoPorGrupo && (
          <section>
            <div style={{ fontSize: 13, fontWeight: 700, color: cores.textoSecundario, marginBottom: 14 }}>
              EXERCÍCIOS DE {grupoSelecionado.toUpperCase()}
            </div>

            {carregando || erro ? null : exerciciosDoGrupo.length === 0 ? (
              <div style={{ color: cores.textoSecundario, fontSize: 14 }}>
                Nenhum exercício cadastrado nesse grupo ainda.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {exerciciosDoGrupo.map((ex) => (
                  <button
                    key={ex.codigo}
                    onClick={() => escolherExercicioDoGrupo(ex)}
                    style={{
                      textAlign: "left",
                      background: cores.cardFundo,
                      border: `1px solid ${cores.borda}`,
                      borderRadius: 16,
                      padding: 18,
                      minHeight: 44,
                      cursor: "pointer",
                      color: cores.texto,
                    }}
                  >
                    <div style={{ fontWeight: 800, fontSize: 16 }}>{ex.nome}</div>
                    <div style={{ fontSize: 12.5, color: cores.textoSecundario, marginTop: 4 }}>
                      {ex.alternativas.length} alternativas disponíveis
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {!navegandoPorGrupo && exercicioAtivo && (
          <section style={{ display: "flex", flexDirection: "column", gap: 22 }}>
            <CardPrincipal
              exercicio={exercicioAtivo}
              totalAlternativasVisiveis={alternativasFiltradas.length}
              onVerVideo={setVideoAberto}
            />

            <FiltroChips
              titulo="Filtrar alternativas por equipamento"
              opcoes={FILTROS_EQUIPAMENTO}
              selecionado={filtroEquipamento}
              onSelecionar={setFiltroEquipamento}
            />

            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: cores.textoSecundario, marginBottom: 14 }}>
                ALTERNATIVAS SUGERIDAS
              </div>

              {alternativasFiltradas.length === 0 ? (
                <div style={{ color: cores.textoSecundario, fontSize: 14 }}>
                  Nenhuma alternativa desse tipo para este exercício. Tente
                  outro filtro de equipamento.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  {alternativasFiltradas.map((alt) => (
                    <CardAlternativa
                      key={alt.codigo || alt.nome}
                      exercicio={alt}
                      favoritos={favoritos}
                      onToggleFavorito={toggleFavorito}
                      onVerVideo={setVideoAberto}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      <ModalVideo video={videoAberto} onClose={() => setVideoAberto(null)} />
    </div>
  );
}
