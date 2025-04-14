import os
import uuid
import tarfile
from pathlib import Path
from shiny import App, ui, reactive, render
from dataclasses import dataclass
import subprocess
import shutil

# criacao dos diretorios que serao feitos os uploads
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# ====================================
# AUXILIAR FUNCTIONS
# ====================================

# classe que contem a estrutura para as mensagens exibidas na UI
@dataclass
class EvaluateResult:
    estrutura_ok: bool
    testes_ok: bool
    mensagem_estrutura: str
    mensagem_testes: str

def evaluate(file_dict: dict, etapa: str, unique_dir: str) -> EvaluateResult:
    """Executa a validação do arquivo submetido."""
    def validate_file() -> bool:
        """Realiza validação do arquivo """

        # teste nome do arquivo == nome da etapa
        if file_dict['name'] != f'{etapa}.tgz':
            return False
        
        extract_all_files(file_dict['datapath'], unique_dir)

        # depois de extraido testa se makefile exisate e esta na raiz
        makefile_path_lower = unique_dir / 'makefile'
        makefile_path_upper = unique_dir / 'Makefile'
        if not (makefile_path_lower.exists() or makefile_path_upper.exists()):
            return False
        
        # TODO: limit size?
        
        return True

    def run_tests() -> bool:
        """Realiza os testes relacionados à cada etapa"""
        try:
            result = subprocess.run(
                ["./sendboxgrupo.sh", etapa],
                check=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    estrutura_ok = validate_file()
    testes_ok = run_tests()

    msg_estrutura = (
        "Estrutura do arquivo: OK!" if estrutura_ok
        else "Estrutura do arquivo: Not OK!"
    )
    msg_testes = (
        "Testes: OK!" if testes_ok
        else "Testes: Not OK!"
    )

    return EvaluateResult(estrutura_ok, testes_ok, msg_estrutura, msg_testes)

def extract_all_files(tar_file_path, extract_to):
    """Extrai o arquivo .tgz para o diretório especificado"""
    with tarfile.open(tar_file_path, 'r') as tar:
        tar.extractall(extract_to)

def remove_file_from_disk(file_dict: dict, extracted_dir: str):
    """Remove arquivos do disco após a validação"""
    os.remove(file_dict['datapath'])
    shutil.rmtree(extracted_dir)

def feedback_message(text: str, type: str) -> ui.Tag:
    """Gera mensagem de feedback na UI"""
    cores = {
        "success": "green",
        "error": "red",
        "warning": "gray"
    }
    cor = cores.get(type)
    return ui.tags.div(
        text,
        style=f"background-color: {cor}; color: white; margin: 10px 0; padding: 10px;"
    )

# ====================================
# UI
# ====================================
app_ui = ui.page_fluid(
    ui.panel_title("Projeto INF01147 - Compiladores"),
    ui.h4("Valide seu entregável"),
    ui.input_select(
        "etapa_select",
        "Selecione uma etapa:",
        {f"etapa{i}": f"Etapa {i}" for i in range(1, 7)},
    ),
    ui.input_file("file_upload", "Faça upload do seu entregável:", accept=[".tgz"]),
    ui.input_action_button("submit_button", "Enviar Submissão"),
    ui.output_ui("div_file_structure"),
    ui.output_ui("div_all_tests"),
)
# ====================================
# SERVER
# ====================================
def server(input, output, session):
    @reactive.Calc
    @reactive.event(input.submit_button)
    def result():
        """Quando botão de Submit é pressionado salva arquivo no disco e realiza a validação"""
        # TODO: fix submit button pressed 2 times
        file_info = input.file_upload()
        if not file_info:
            return None
        file_dict = file_info[0]
        etapa = input.etapa_select()
        unique_dir = UPLOADS_DIR / str(uuid.uuid5(uuid.NAMESPACE_DNS, file_dict['datapath']))
        evaluate_result = evaluate(file_dict, etapa, unique_dir)
        remove_file_from_disk(file_dict, unique_dir)
        
        print(f"file_dict: {file_dict}")
        print(f"Diretorio gerado: {unique_dir}")
        print(f"Etapa selecionada: {etapa}")

        return evaluate_result

    @output
    @render.ui
    def div_file_structure():
        """Div relacionada ao feedback da estrutura de arquivo"""
        res = result()
        if res is None:
            return feedback_message("Nenhum arquivo enviado.", "warning")
        type = "success" if res.estrutura_ok else "error"
        return feedback_message(res.mensagem_estrutura, type)

    @output
    @render.ui
    def div_all_tests():
        """Div relacionada ao feedback dos testes"""
        res = result()
        if res is None:
            return ""
        type = "success" if res.testes_ok else "error"
        return feedback_message(res.mensagem_testes, type)

app = App(app_ui, server)
