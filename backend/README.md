# Backend do alternafit

Este é o "servidor" do alternafit. Ele faz três coisas:

- **guarda os exercícios** num banco de dados MySQL;
- oferece uma **área de administração** (o Django Admin), onde dá para ver, revisar e editar os dados pelo navegador;
- oferece uma **API**, que é o endereço que o app React consulta para mostrar os exercícios e as alternativas.

Se você nunca mexeu com Django, tudo bem: este guia foi escrito pensando nisso. É só seguir os passos na ordem.

## Como as peças se encaixam

```
Planilha (data/*.xlsx) → comando importar_planilha → MySQL → API do Django → app React
```

1. O time organiza os exercícios numa **planilha** (pasta `data/` na raiz do repositório).
2. Um comando lê a planilha e grava tudo no **MySQL**.
3. O Django lê o banco e entrega os dados pela **API**, já no formato que o React espera.
4. O **app React** (na raiz do repositório) mostra tudo na tela.

## O que você precisa ter instalado

| Programa | Para quê | Onde baixar |
|---|---|---|
| Python 3.11 ou mais novo | rodar o Django | https://www.python.org/downloads/ |
| MySQL 8.4 (Community Server) | o banco de dados | https://dev.mysql.com/downloads/mysql/ |
| Git | baixar e enviar o código | https://git-scm.com/downloads |
| Node.js 18 ou mais novo | rodar o app React junto | https://nodejs.org/ |

No Windows, dá para instalar o Git e o Node pelo terminal:

```
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
```

Depois de instalar qualquer programa, **feche e abra o terminal de novo**. Senão ele não encontra os comandos novos.

## Primeira vez: deixando tudo pronto

Os comandos abaixo são para o **PowerShell do Windows**. No Mac ou no Linux, troque `venv\Scripts\python.exe` por `venv/bin/python`.

### 1. Baixe o projeto

```
git clone https://github.com/Vlad-lll/-alternafit.git alternafit
cd alternafit
```

O `alternafit` no fim do primeiro comando dá um nome normal para a pasta (o repositório começa com um hífen, o que confunde alguns comandos).

### 2. Crie o banco de dados

Abra o **MySQL Command Line Client** (ele vem com o MySQL), entre com a senha do usuário `root` e rode:

```sql
CREATE DATABASE alternafit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'alternafit_user'@'localhost' IDENTIFIED BY 'troque_por_uma_senha';
GRANT ALL PRIVILEGES ON alternafit.* TO 'alternafit_user'@'localhost';
GRANT ALL PRIVILEGES ON test_alternafit.* TO 'alternafit_user'@'localhost';
```

- A primeira linha cria o banco. O `utf8mb4` garante que acentos sejam salvos corretamente.
- A segunda cria um usuário só para o app. **Troque a senha** e guarde-a, você vai precisar dela no passo 4.
- As duas últimas dão permissão a esse usuário no banco do app e no banco temporário que os testes automáticos criam.

### 3. Prepare o ambiente Python

```
cd backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

O `venv` é uma "caixinha" com as bibliotecas só deste projeto, para não misturar com outros projetos do seu computador. O `requirements.txt` lista as versões exatas que o projeto usa.

Não precisa "ativar" o venv: chamando `venv\Scripts\python.exe` direto, você já usa o Python certo.

### 4. Configure o arquivo `.env`

O `.env` guarda as configurações secretas (como a senha do banco). Ele **nunca vai para o GitHub**: cada pessoa tem o seu.

```
copy .env.example .env
```

Abra o `.env` num editor e preencha:

- `DB_PASSWORD`: a senha que você criou no passo 2, logo depois do `=`, sem aspas.
- `DJANGO_SECRET_KEY`: uma chave secreta. Gere uma com o comando abaixo e cole entre as aspas simples:

```
venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### 5. Crie as tabelas no banco

```
venv\Scripts\python.exe manage.py migrate
```

O Django lê os arquivos da pasta `migrations/` (um "roteiro" de como o banco deve ser) e cria todas as tabelas. Cada linha terminando em `OK` é um passo que deu certo.

### 6. Crie o seu usuário de administrador

```
venv\Scripts\python.exe manage.py createsuperuser
```

Ele pede um nome de usuário, um e-mail (pode deixar em branco) e uma senha. A senha não aparece enquanto você digita, é normal.

### 7. Carregue os exercícios da planilha

Primeiro uma **simulação**, que mostra o que vai acontecer sem gravar nada:

```
venv\Scripts\python.exe manage.py importar_planilha "..\data\alternafit_banco_exercicios_v2.3.xlsx" --dry-run
```

Se o relatório estiver ok, rode de verdade (o mesmo comando, sem o `--dry-run`):

```
venv\Scripts\python.exe manage.py importar_planilha "..\data\alternafit_banco_exercicios_v2.3.xlsx"
```

### 8. Ligue o servidor

```
venv\Scripts\python.exe manage.py runserver
```

Pronto! Com o terminal aberto, acesse:

- **Admin:** http://127.0.0.1:8000/admin/ (entre com o usuário do passo 6)
- **API:** http://127.0.0.1:8000/api/exercicios/

Para desligar o servidor, aperte `Ctrl+C` no terminal.

### 9. Rodando o app React junto

Deixe o Django ligado e abra **outro terminal**, na pasta raiz do repositório (não na `backend`):

```
npm install
npm run dev
```

Acesse http://localhost:5173. O app busca os dados em `http://127.0.0.1:8000/api`. Se precisar apontar para outro endereço, crie a variável `VITE_API_URL` (por exemplo, num arquivo `.env.local` na raiz).

## No dia a dia

**Ligar tudo:** um terminal com `runserver` (na pasta `backend`) e outro com `npm run dev` (na raiz).

**Pegar as novidades do time:**

```
git pull
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe manage.py migrate
```

O `pip install` só instala algo se alguém tiver adicionado uma biblioteca nova, e o `migrate` só muda o banco se alguém tiver mudado as tabelas. Rodar os dois sempre é seguro.

**Importar uma versão nova da planilha:** coloque o arquivo em `data/`, rode o `importar_planilha` com `--dry-run`, leia o relatório e depois rode sem o `--dry-run`.

> ⚠️ A importação **substitui o catálogo inteiro** pelo conteúdo da planilha. Qualquer exercício criado ou editado pelo Admin depois da última importação será perdido. Usuários e logins não são afetados.

Para ver a lista das trocas que precisam de revisão, use `--detalhes`.

**Rodar os testes automáticos:**

```
venv\Scripts\python.exe manage.py test
```

Eles conferem se a API continua entregando os dados no formato que o app espera. Rode antes de enviar mudanças para o GitHub.

**Mudou alguma tabela (`models.py`)?** Gere o roteiro da mudança e aplique:

```
venv\Scripts\python.exe manage.py makemigrations
venv\Scripts\python.exe manage.py migrate
```

Envie o arquivo novo da pasta `migrations/` junto com o seu commit, para o time ficar com o mesmo banco.

## A API

Ela só **lê** dados (ninguém consegue alterar nada por ela). Abrindo os endereços no navegador, o Django mostra uma página com o JSON formatado.

| Endereço | O que devolve |
|---|---|
| `/api/exercicios/` | todos os exercícios |
| `/api/exercicios/?busca=supino` | exercícios cujo nome, nome em inglês ou apelido contém "supino" (o nome exato vem primeiro) |
| `/api/exercicios/?grupo=Glúteos` | exercícios que trabalham o grupo (os de foco principal vêm primeiro) |
| `/api/exercicios/1/` | um exercício específico, pelo `codigo` |
| `/api/grupos-musculares/` | os grupos musculares, com a região (Superior, Core, Inferior) |

Cada exercício vem com os campos que o app usa (`nome`, `dificuldade`, `gruposMusculares`, `equipamentos`, `dica`, `videoUrl`, `alternativas`...) e alguns extras (`gruposPrincipais`, `gruposAuxiliares`, `padraoMovimento`, `apelidos`, `passos`, `fontes`).

O `codigo` de cada exercício é o mesmo `id` da planilha, então ele não muda entre uma importação e outra.

## Regras da planilha

O importador espera a planilha no formato "modelo de banco de dados" (versão 2.2 em diante):

- cada aba é uma tabela (`exercicio`, `exercicio_alternativo`, `grupo_muscular`...);
- **não renomeie abas nem colunas**, o importador procura por esses nomes;
- **nunca renumere os IDs**: eles viram os IDs do banco, e o app usa esses números para guardar os favoritos;
- colunas que começam com `_aux_` ou `_calc_` são só para conferência humana e são ignoradas;
- "sem equipamento" é calculado: um exercício é sem equipamento quando não tem nenhuma linha na aba `exercicio_equipamento` (chão e parede não contam).

Se tiver algum problema (um ID que não existe, um nome repetido...), o importador lista tudo e **não grava nada**.

## Onde fica cada coisa

```
backend/
├── manage.py                  ← o "controle remoto" do Django (todos os comandos passam por ele)
├── requirements.txt           ← bibliotecas Python do projeto
├── .env.example               ← modelo do .env (sem senhas)
├── alternafit_backend/        ← configurações gerais (settings.py) e endereços (urls.py)
├── users/                     ← usuário do sistema (logins do Admin)
└── exercises/                 ← tudo sobre exercícios
    ├── models.py              ← as tabelas do banco
    ├── serializers.py         ← "tradução" do banco para o JSON da API
    ├── views.py               ← a lógica de busca e filtros da API
    ├── admin.py               ← as telas do Django Admin
    ├── tests.py               ← testes automáticos
    ├── migrations/            ← histórico de mudanças das tabelas
    └── management/commands/
        └── importar_planilha.py   ← o importador da planilha
```

## Problemas comuns

**"O termo 'git' (ou 'node', 'npm') não é reconhecido"**
O programa foi instalado depois que o terminal foi aberto. Feche e abra o terminal de novo.

**`Access denied for user 'alternafit_user'@'localhost'`**
A senha no `.env` não bate com a do MySQL. Confira o `DB_PASSWORD` (sem espaços e sem aspas).

**`Can't connect to MySQL server on 'localhost'`**
O MySQL está desligado. No Windows, abra "Serviços", procure por MySQL (algo como `MySQL84`) e clique em "Iniciar".

**`Error: That port is already in use`**
Já tem um servidor rodando na porta 8000, talvez em outro terminal. Feche o outro ou use outra porta (`runserver 8001`); nesse caso, aponte o app para ela com o `VITE_API_URL`.

**O app abre mas não mostra nenhum exercício**
Confira se o Django está ligado (http://127.0.0.1:8000/api/exercicios/ abre?). Confira também se o app está mesmo em `http://localhost:5173`: o Django só aceita pedidos vindos desse endereço (configuração `CORS_ALLOWED_ORIGINS` no `settings.py`).

**`A planilha não tem a aba "..."`**
A planilha está num formato antigo. O importador só aceita o formato da versão 2.2 em diante.
