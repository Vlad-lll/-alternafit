import React, { useEffect, useState } from "react";
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

export default function App() {
  const [termoBusca, setTermoBusca] = useState("Supino Reto com Barra");
  const [exercicioAtivo, setExercicioAtivo] = useState(null);
  const [naoEncontrado, setNaoEncontrado] = useState(false);

  const [grupos, setGrupos] = useState([]);
  const [grupoSelecionado, setGrupoSelecionado] = useState("Todos");
  const [exerciciosDoGrupo, setExerciciosDoGrupo] = useState([]);

  const [filtroEquipamento, setFiltroEquipamento] = useState("Todos");

  const [favoritos, setFavoritos] = useState([]);
  const [videoAberto, setVideoAberto] = useState(null);

  // Carrega o exercício inicial e a lista de grupos musculares (para os chips)
  useEffect(() => {
    buscarExercicioPorNome("Supino Reto com Barra").then(setExercicioAtivo);
    obterGruposMusculares().then(setGrupos);
  }, []);

  async function buscar(e) {
    e.preventDefault();
    const resultado = await buscarExercicioPorNome(termoBusca);
    if (resultado) {
      setExercicioAtivo(resultado);
      setNaoEncontrado(false);
      setGrupoSelecionado("Todos");
      setFiltroEquipamento("Todos");
    } else {
      setNaoEncontrado(true);
    }
  }

  async function selecionarGrupo(grupo) {
    setGrupoSelecionado(grupo);
    if (grupo === "Todos") {
      setExerciciosDoGrupo([]);
      return;
    }
    const lista = await buscarExerciciosPorGrupoMuscular(grupo);
    setExerciciosDoGrupo(lista);
  }

  function escolherExercicioDoGrupo(exercicio) {
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

        {naoEncontrado && !navegandoPorGrupo && (
          <div
            style={{
              background: cores.cardFundo,
              border: `1px solid ${cores.borda}`,
              borderRadius: 16,
              padding: 24,
              textAlign: "center",
              color: cores.textoSecundario,
              marginBottom: 30,
            }}
          >
            Nenhum exercício encontrado para "{termoBusca}". Tente outro nome
            ou navegue por grupo muscular acima.
          </div>
        )}

        {navegandoPorGrupo && (
          <section>
            <div style={{ fontSize: 13, fontWeight: 700, color: cores.textoSecundario, marginBottom: 14 }}>
              EXERCÍCIOS DE {grupoSelecionado.toUpperCase()}
            </div>

            {exerciciosDoGrupo.length === 0 ? (
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
