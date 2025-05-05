from shiny import App, ui, render

app_ui = ui.page_fluid(
    ui.input_slider("val", "Slider label", min=0, max=100, value=50),
    ui.output_text("slider_val")
)

def server(input, output, session):
    @output
    @render.text
    def slider_val():
        return f"Slider value: {input.val()}"

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()