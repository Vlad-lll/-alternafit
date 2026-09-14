# alternafit

Projeto de extensão, ADS. Site que sugere exercícios alternativos para quem
treina em horário de pico ou fora da academia. Toda busca sempre retorna
pelo menos uma opção sem aparelho (calistenia).

## Stack

- Frontend: React + Vite (este repositório)
- Backend (planejado): Python + Django
- Banco de dados (planejado): MySQL

## Estrutura de pastas

```
src/
  components/     componentes de UI (Header, SearchBar, CardAlternativa etc.)
  data/           mock data dos exercícios, usado enquanto o backend não existe
  services/       camada de acesso a dados (api.js), isolada dos componentes
  styles/         cores e fontes centralizadas (theme.js)
  App.jsx         componente principal, junta tudo
  main.jsx        ponto de entrada do Vite
```

A ideia de manter `services/api.js` separado é simples: hoje ele só lê o
mock em `data/exercicios.js`, mas quando a API do Django estiver pronta,
basta trocar o corpo das funções desse arquivo por chamadas `fetch`, sem
mexer em nenhum componente.

## Formato dos dados

O formato de `data/exercicios.js` segue exatamente a planilha que o time de
Educação Física está preenchendo (abas Dificuldades, Grupos Musculares,
Equipamentos, Exercícios, Alternativas, Passos de Execução). O exercício
"Supino Reto com Barra" usa o único exemplo já preenchido na planilha; os
outros dois exercícios ainda são fictícios, só para preencher a tela
enquanto o time termina de cadastrar o resto.

Quando novas linhas forem preenchidas na planilha, é só seguir o mesmo
formato de objeto em `EXERCICIOS` para adicioná-las aqui (ou, melhor ainda,
já ligar direto na API quando o Django estiver pronto).

## Como rodar localmente

Pré-requisito: Node.js instalado (versão 18 ou superior).

```bash
npm install
npm run dev
```

O terminal vai mostrar um endereço tipo `http://localhost:5173`, é só abrir
no navegador.

## Design mobile-first

O uso principal do site é pelo celular, então as telas foram pensadas
primeiro pra tela pequena:

- Container centralizado com largura máxima de 480px (em vez de ocupar a
  tela toda no PC), simulando a proporção de um app mesmo no navegador
- Listas em coluna única (exercícios e alternativas), pensadas pra rolagem
  vertical com o dedão, em vez de grade em várias colunas
- Botões, chips e o ícone de favoritar com área de toque mínima de
  40 a 48px, seguindo a recomendação de acessibilidade para toque

## Funcionalidades atuais

- Busca de exercício por nome
- Navegação por grupo muscular (chips)
- Filtro de alternativas por tipo de equipamento
- Favoritar exercícios (estado local, ainda não salva no banco)
- Modal simulado de vídeo de execução

## Próximos passos

- Substituir o mock de `data/exercicios.js` pela planilha real dos alunos
  de Educação Física
- Trocar `services/api.js` por chamadas reais à API Django
- Persistir favoritos e treino semanal no banco (MySQL)
