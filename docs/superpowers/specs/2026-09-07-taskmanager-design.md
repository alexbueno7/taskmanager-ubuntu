# taskmanager-ubuntu — Design Spec (2026-09-07)

## Objetivo
.deb instalável Ubuntu 26.04, estilo Gerenciador Tarefas Windows.
Mostra processos usuário com %CPU, %MEM. Permite encerrar/forçar por linha.

## Decisões travadas
- Stack: Python3 + Tkinter (ttk.Treeview) + psutil
- Pacote: taskmanager-ubuntu, v1.0.0-1, arch all
- Escopo: só processos do usuário atual, sem pkexec/root
- Recursos v1: listar PID/Nome/CPU%/MEM%/Usuário/Estado, buscar, ordenar por coluna, auto-refresh 2s, encerrar SIGTERM, forçar SIGKILL, detalhes duplo-clique, barra total CPU/MEM

## Arquitetura
Script único `src/taskmanager-ubuntu.py`:
- Coletor: `psutil.process_iter(['pid','name','username','cpu_percent','memory_info','memory_percent','status'])`, filtro `username == getpass.getuser()`, primeiro `cpu_percent()` warm-up
- UI: Tkinter `after(2000, refresh)`, sem thread v1
- Killer: `proc.terminate()` → confirmação → após 2s se vivo `proc.kill()`. `AccessDenied/NoSuchProcess/Zombie` tratados com ignore + messagebox

## Pacote .deb
```
taskmanager-ubuntu_1.0.0-1_all/
  DEBIAN/control  (Package, Version 1.0.0-1, Architecture all, Depends: python3, python3-tk, python3-psutil, Maintainer, Description)
  usr/bin/taskmanager-ubuntu (chmod 755)
  usr/share/applications/taskmanager-ubuntu.desktop
  usr/share/icons/hicolor/48x48/apps/taskmanager-ubuntu.png (gerado via Tk? v1 usa ícone padrão sistema)
  usr/share/doc/taskmanager-ubuntu/changelog.gz (mínimo)
```
Build: `dpkg-deb --build <dir> <saida>.deb`. Teste: `sudo dpkg -i`, `dpkg -l`, menu app, `apt remove`.

## Fluxos
1. Abrir → warm-up CPU → lista 2s → ordena → render
2. Buscar texto filtra nome/PID em memória
3. Seleciona linha → Encerrar → confirma → SIGTERM → refresh. Forçar → SIGKILL direto com confirma
4. Duplo-clique → popup detalhes (cmdline, cwd, create_time, memória MB)

## Erros
- psutil.AccessDenied / NoSuchProcess durante iter → pula linha
- Kill falha → messagebox erro, sem crash
- psutil ausente → messagebox instrução `sudo apt install python3-psutil`

## Testes
- `python3 src/taskmanager-ubuntu.py` abre e lista
- Cria `sleep 1000 &` → aparece → Encerrar remove → Forçar mata `-9`
- `dpkg-deb --build` gera .deb → instala → aparece no menu → desinstala limpo

## Fora escopo v1
Gráficos históricos, árvore processos, root/pkexec, daemon/serviço, i18n completo.
