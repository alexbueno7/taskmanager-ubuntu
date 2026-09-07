# Gerenciador de Tarefas para Ubuntu

O Ctrl+Shift+Esc que faltava no Linux: veja o que está pesando na máquina e mate qualquer processo com um clique — sem terminal, sem PID, sem `kill -9`.

## O problema

Um programa travou. No Linux, o ritual é este:

1. Abrir o terminal
2. Rodar `ps aux | grep nome-do-programa`
3. Caçar o PID certo no meio daquela lista
4. Rodar `kill 48213` e torcer
5. Se não morreu, `kill -9 48213` — torcendo mais ainda para não ter digitado o PID errado

Quem nunca decorou PID, confunde `kill` com `killall` ou tem medo de derrubar o sistema por matar o processo errado acaba refém do terminal — ou pior, reinicia a máquina inteira por causa de um app travado.

## A solução

Abra o **Gerenciador de Tarefas**, ache o vilão no topo da lista (ordenado por %CPU), selecione e clique em **Encerrar**. Pronto. Sem terminal, sem PID, sem decoreba.

- **Vê tudo de uma vez:** PID, nome, %CPU, %MEM e estado de cada processo, com totais da máquina no topo
- **Acha rápido:** busca por nome e ordenação por qualquer coluna
- **Mata com segurança:** botão Encerrar (gentil) e Forçar (definitivo), sempre com confirmação
- **Sem risco de quebrar o sistema:** mostra só os *seus* processos — nada de root, nada de senha
- **Leve:** Python + Tkinter + psutil, sem daemon, sem serviço rodando no fundo

## Instalação

```bash
bash build-deb.sh
sudo dpkg -i build/taskmanager-ubuntu_1.0.0-1_all.deb
sudo apt -f install   # só se faltar alguma dependência
```

## Uso

Pelo menu do sistema ("Gerenciador de Tarefas") ou:

```bash
taskmanager-ubuntu
```

Busca filtra por nome ou PID, clique no cabeçalho ordena, duplo-clique mostra detalhes, a lista atualiza sozinha a cada 2 segundos.

## Desenvolvimento

```bash
python3 -m pytest -v   # testes do coletor
python3 -m src         # abre a interface (precisa de display)
bash build-deb.sh      # gera o .deb em build/
```
