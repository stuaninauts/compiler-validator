import os
import uuid
from pathlib import Path
from shiny import App, ui, reactive, render
from dataclasses import dataclass

# criacao dos diretorios que serao feitos os uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

def evaluate(created_filename: str, original_filename: str, etapa: str) -> EvaluateResult:
    """Executa a validação do arquivo submetido."""
    
    def validate_file() -> bool:
        """Realiza validação do arquivo """
        # TODO
        # untar, ()akefile (tambem alvo) e raiz
        return created_filename.endswith(".tgz")

    def run_tests() -> bool:
        """Realiza os testes relacionados à cada etapa"""
        print('created_filename: ', created_filename)
        # TODO
        if etapa == 'etapa1':
            #chamar script system sendboxgrupo.sh retorno 0 ou 1 arg etapa
            return True
        elif etapa == 'etapa2':
            return True
        elif etapa == 'etapa3':
            return True
        elif etapa == 'etapa4':
            return True
        elif etapa == 'etapa5':
            return True
        elif etapa == 'etapa6':
            return True
        else:
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

def save_file_to_disk(file_info, etapa) -> str:
    # TODO: remover arquivo temporario
    """Salva arquivo no disco com identificador único dentro do diretório da etapa selecionada"""
    original_name = file_info["name"]
    ext = os.path.splitext(original_name)[1]
    unique_name = f"{uuid.uuid4()}{ext}"

    path = UPLOAD_DIR / unique_name
    with open(file_info["datapath"], "rb") as src:
        with open(path, "wb") as dest:
            dest.write(src.read())

    return str(path)

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
        file_info = input.file_upload()
        if not file_info:
            return None
        filename = file_info[0]['name']
        datapath = file_info[0]['datapath']
        print(f"Arquivo recebido: {original_filename}")
        etapa = input.etapa_select()
        # created_filename = save_file_to_disk(file_info[0], etapa)
        created_filename = 'a'
        evaluate_result = evaluate(created_filename, original_filename, etapa)
        # remove_file_from_disk(filename)
        
        print(f"Arquivo salvo como: {created_filename}")
        print(f"Arquivo original: {original_filename}")
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
