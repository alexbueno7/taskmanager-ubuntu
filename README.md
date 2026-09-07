# taskmanager-ubuntu

Gerenciador de tarefas estilo Windows para Ubuntu. Lista processos do usuário com %CPU e %MEM, permite encerrar (SIGTERM) ou forçar (SIGKILL) cada um.

Stack: Python 3 + Tkinter + psutil. Sem root, sem daemon.

## Instalar

```bash
sudo dpkg -i build/taskmanager-ubuntu_1.0.0-1_all.deb
sudo apt -f install  # se faltar dependência
```

Ou compile você mesmo: `bash build-deb.sh` e o `.deb` sai em `build/`.

## Usar

```bash
taskmanager-ubuntu  # ou menu "Gerenciador de Tarefas"
```

Busca filtra por nome/PID, clique no cabeçalho ordena, duplo-clique mostra detalhes, refresh a cada 2s.

## Dev

```bash
python3 -m pytest -v
python3 -m src        # abre a GUI (precisa de display)
bash build-deb.sh
```
