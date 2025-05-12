import os
import uuid
import tarfile
from pathlib import Path
from shiny import App, ui, reactive, render
from dataclasses import dataclass
import subprocess
import shutil

# TODO: comentado por enquanto (necessita de permissão de escrita no servidor)
# criacao dos diretorios que serao feitos os uploads
# UPLOADS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = Path(".")

# ====================================z
# AUXILIAR FUNCTIONS
# ====================================

# classe que contem a estrutura para as mensagens exibidas na UI
@dataclass
class EvaluateResult:
    estrutura_ok: bool
    testes_ok: bool
    mensagem_estrutura: str
    mensagem_testes: str
    etapa: str = None
    nome_arquivo: str = None

def evaluate(file_dict: dict, etapa: str, unique_dir: str) -> EvaluateResult:
    """Executa a validação do arquivo submetido."""
    def validate_file() -> bool:
        """Realiza validação do arquivo """

        # teste nome do arquivo == nome da etapa
        if file_dict['name'] != f'{etapa}.tgz':
            return False
        
        extract_succedd = extract_all_files(file_dict['datapath'], unique_dir)
        if not extract_succedd:
            return False
        
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
    
    # try: 
    estrutura_ok = validate_file()
    testes_ok = run_tests()
    # except Exception as e:
    #     print(f"Erro ao validar o arquivo: {e}")
    #     estrutura_ok = False
    #     testes_ok = False

    msg_estrutura = (
        "Estrutura do arquivo: OK!" if estrutura_ok
        else "Estrutura do arquivo: Not OK!"
    )
    msg_testes = (
        "Testes: OK!" if testes_ok
        else "Testes: Not OK!"
    )

    return EvaluateResult(estrutura_ok, testes_ok, msg_estrutura, msg_testes, etapa, file_dict['name'])

def extract_all_files(tar_file_path, extract_to):
    """Extrai o arquivo .tgz para o diretório especificado"""
    try:
        with tarfile.open(tar_file_path, 'r') as tar:
            tar.extractall(extract_to)
        return True
    except Exception as e:
        return False

def remove_file_from_disk(file_dict: dict, extracted_dir: str):
    """Remove arquivos do disco após a validação"""
    os.remove(file_dict['datapath'])
    # verificacao adicional para arquivos .tgz vazios
    if os.path.exists(extracted_dir):
        shutil.rmtree(extracted_dir)

def feedback_message(text: str, type: str) -> ui.Tag:
    """Gera mensagem de feedback na UI"""
    colors = {
        "success": ("green", "white"),
        "error": ("red", "white"),
        "warning": ("gray", "white"),
        "info": ("white", "black")
    }
    bg_color, text_color = colors.get(type, ("white", "black"))
    return ui.tags.div(
        text,
        style=f"background-color: {bg_color}; color: {text_color}; margin: 10px 0; padding: 10px;"
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
    ui.input_file(
        "file_upload",
        "Faça upload do seu entregável:",
        accept=[".tgz"],
    ),
    ui.tooltip(
        ui.input_action_button(
            "submit_button",
            "Enviar Submissão",
        ),
        "São aceitos arquivos .tgz com o nome da etapa",
        placement="right",
        ),
    ui.output_ui("div_submission_info"),
    ui.output_ui("div_file_structure"),
    ui.output_ui("div_all_tests"),
    ui.tags.div(
        [
            ui.hr(style="margin-bottom: 1.5em; margin-left: 0;"),
            ui.tags.p(
                ui.tags.img(
                    src="https://img.icons8.com/ios-filled/50/000000/scales.png",
                    style="width: 20px; height: 20px; vertical-align: middle; margin-right: 5px;"
                ),
                "Este projeto é de código aberto sob a ",
                ui.tags.a("Licença MIT", href="https://opensource.org/licenses/MIT", target="_blank")
            ),
            ui.tags.p(
                ui.tags.a(
                    ui.tags.img(
                        src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
                        style="width: 20px; height: 20px; vertical-align: middle; margin-right: 5px;"
                    ),
                    "Acesse o repositório no GitHub",
                    href="https://github.com/stuaninauts/compiler-validator",
                    target="_blank"
                )
            )
        ],
        style="position: fixed; bottom: 0; width: 100%; font-size: 0.9em; color: gray; margin-bottom: 10px"
    )
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
        # try:
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
        # except Exception as e:
        #     print(f"Erro ao processar o arquivo: {e}")
        #     return None


    @output
    @render.ui
    def div_submission_info():
        """Div relacionada ao feedback do envio"""
        res = result()
        if res is None:
            return ""
        type = "info"
        return feedback_message(f"Etapa: {res.etapa}, Arquivo: {res.nome_arquivo}", type)
    
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
