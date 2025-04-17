# app.R
library(shiny)

ui <- fluidPage(
  titlePanel("Hello from Raspberry Pi"),
  sidebarLayout(
    sidebarPanel(
      sliderInput("num",
                  "Escolha um número:",
                  min = 1,
                  max = 100,
                  value = 30)
    ),
    mainPanel(
      textOutput("resultado")
    )
  )
)

server <- function(input, output) {
  output$resultado <- renderText({
    paste("O número escolhido foi:", input$num)
  })
}

shinyApp(ui = ui, server = server)
