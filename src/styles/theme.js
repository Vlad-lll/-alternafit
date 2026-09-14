export const cores = {
  fundo: "#0E1420",
  cardFundo: "#161D2E",
  cardFundoAlt: "#10182A",
  borda: "#232B3D",
  texto: "#F3F5F9",
  textoSecundario: "#8A93A8",
  navy: "#4C7FE3",
  navySoft: "#6E97EA",
  navyTint: "rgba(76,127,227,0.14)",
  navyTexto: "#FFFFFF",
  orange: "#F5821F",
  orangeTint: "rgba(245,130,31,0.14)",
  perigo: "#F14E4E",
};

export const fonte =
  "'Segoe UI', Roboto, -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif";

/** Fundo do badge, translúcido: laranja pra sem equipamento, azul pra com equipamento. */
export function corBadgeFundo(semEquipamento) {
  return semEquipamento ? cores.orangeTint : cores.navyTint;
}

/** Cor do texto do badge, combinando com o fundo. */
export function corBadgeTexto(semEquipamento) {
  return semEquipamento ? cores.orange : cores.navySoft;
}
