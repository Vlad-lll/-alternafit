import React from "react";
import { cores } from "../styles/theme";

export default function ModalVideo({ video, onClose }) {
  if (!video) return null;
  const { nome, url } = video;

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 50,
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: cores.cardFundo,
          border: `1px solid ${cores.borda}`,
          borderRadius: 20,
          padding: 28,
          maxWidth: 420,
          width: "100%",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 40, marginBottom: 12 }}>🎬</div>
        <h3 style={{ color: cores.texto, fontSize: 18, fontWeight: 800, marginBottom: 8 }}>
          Vídeo de execução
        </h3>

        {url ? (
          <p style={{ color: cores.textoSecundario, fontSize: 14, marginBottom: 20 }}>
            Vídeo de <strong style={{ color: cores.texto }}>{nome}</strong> cadastrado
            pelo time.
          </p>
        ) : (
          <p style={{ color: cores.textoSecundario, fontSize: 14, marginBottom: 20 }}>
            Ainda não tem vídeo cadastrado para{" "}
            <strong style={{ color: cores.texto }}>{nome}</strong>.
          </p>
        )}

        <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              style={{
                background: cores.navy,
                color: cores.navyTexto,
                borderRadius: 12,
                padding: "10px 22px",
                fontWeight: 800,
                fontSize: 14,
                textDecoration: "none",
              }}
            >
              Abrir vídeo
            </a>
          )}
          <button
            onClick={onClose}
            style={{
              background: url ? "transparent" : cores.navy,
              color: url ? cores.textoSecundario : cores.navyTexto,
              border: url ? `1px solid ${cores.borda}` : "none",
              borderRadius: 12,
              padding: "10px 22px",
              fontWeight: 800,
              fontSize: 14,
              cursor: "pointer",
            }}
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
