# Explorando a apuração das eleições 2026 em R
# Lê o banco SQLite gerado por banco.py (dados/apuracao.sqlite).
#
# Pacotes (Ubuntu, sem compilar nada):
#   sudo apt install r-base r-cran-tidyverse r-cran-rsqlite r-cran-dbi
# ou, dentro do R:
#   install.packages(c("tidyverse", "DBI", "RSQLite"))
#
# Rode a partir da pasta do projeto:  Rscript R/01-explorar-apuracao.R
# (ou abra no RStudio com o projeto como diretório de trabalho)

library(DBI)
library(dplyr)
library(tidyr)
library(ggplot2)

con <- dbConnect(RSQLite::SQLite(), "dados/apuracao.sqlite")

dbListTables(con)   # coletas, ufs, candidatos, apuracao, votos, v_votos, v_nacional_soma

# ------------------------------------------------------------------
# 1. Votos em formato longo: uma linha por coleta × estado × candidato
# ------------------------------------------------------------------
votos <- tbl(con, "v_votos") |>
  filter(abrangencia != "BR") |>          # BR = arquivo nacional do TSE (atrasa); usamos a soma das UFs
  collect() |>
  mutate(horario = as.POSIXct(horario))

apuracao <- tbl(con, "apuracao") |>
  filter(abrangencia != "BR") |>
  collect()

# ------------------------------------------------------------------
# 2. Placar nacional ao longo da noite (soma das UFs)
# ------------------------------------------------------------------
nacional <- votos |>
  group_by(horario, coleta_id, numero, candidato) |>
  summarise(votos = sum(votos), .groups = "drop") |>
  group_by(coleta_id) |>
  mutate(pct = 100 * votos / sum(votos)) |>     # % dos votos nominais (= válidos para presidente)
  ungroup()

cores <- c("Flavio Bolsonaro" = "#2a78d6", "Lula" = "#e34948")

nacional |>
  filter(numero %in% c(22, 13)) |>
  ggplot(aes(horario, pct, colour = candidato)) +
  geom_hline(yintercept = 50, colour = "grey60") +
  geom_line(linewidth = 1) +
  geom_point(size = 2) +
  scale_colour_manual(values = cores) +
  labs(title = "Placar ao longo da apuração", x = NULL, y = "% dos válidos", colour = NULL) +
  theme_minimal(base_size = 13) +
  theme(legend.position = "top")
ggsave("R/placar-noite.png", width = 9, height = 5, dpi = 150)

# ------------------------------------------------------------------
# 3. Crescimento entre coletas (lag): quem cada atualização favoreceu
# ------------------------------------------------------------------
lotes <- nacional |>
  filter(numero %in% c(22, 13)) |>
  select(horario, candidato, votos) |>
  arrange(horario) |>
  group_by(candidato) |>
  mutate(novos = votos - lag(votos)) |>
  ungroup() |>
  filter(!is.na(novos)) |>
  pivot_wider(id_cols = horario, names_from = candidato, values_from = novos) |>
  mutate(saldo = `Flavio Bolsonaro` - Lula,
         favorecido = if_else(saldo >= 0, "Flavio Bolsonaro", "Lula"))

print(lotes)

ggplot(lotes, aes(format(horario, "%H:%M"), saldo, fill = favorecido)) +
  geom_col(width = 0.7) +
  geom_hline(yintercept = 0, colour = "grey40") +
  scale_fill_manual(values = cores) +
  scale_y_continuous(labels = scales::label_number(scale = 1e-3, suffix = " mil", big.mark = ".")) +
  labs(title = "Saldo de votos em cada atualização", x = NULL, y = "Flávio − Lula", fill = NULL) +
  theme_minimal(base_size = 13) +
  theme(legend.position = "top")
ggsave("R/saldo-por-lote.png", width = 9, height = 5, dpi = 150)

# ------------------------------------------------------------------
# 4. O mesmo por estado (small multiples), estados com mais votos
# ------------------------------------------------------------------
lotes_uf <- votos |>
  filter(numero %in% c(22, 13)) |>
  select(horario, abrangencia, nome_uf, candidato, votos) |>
  arrange(horario) |>
  group_by(abrangencia, candidato) |>
  mutate(novos = votos - lag(votos)) |>
  ungroup() |>
  filter(!is.na(novos)) |>
  pivot_wider(id_cols = c(horario, abrangencia, nome_uf), names_from = candidato, values_from = novos) |>
  mutate(saldo = `Flavio Bolsonaro` - Lula)

top_ufs <- apuracao |>
  filter(coleta_id == max(coleta_id)) |>
  slice_max(validos, n = 9) |>
  pull(abrangencia)

lotes_uf |>
  filter(abrangencia %in% top_ufs) |>
  ggplot(aes(horario, saldo, fill = saldo >= 0)) +
  geom_col() +
  geom_hline(yintercept = 0, colour = "grey40") +
  facet_wrap(~ nome_uf) +
  scale_fill_manual(values = c(`TRUE` = "#2a78d6", `FALSE` = "#e34948"), guide = "none") +
  scale_y_continuous(labels = scales::label_number(scale = 1e-3, suffix = " mil", big.mark = ".")) +
  labs(title = "Saldo de cada atualização por estado", subtitle = "azul = Flávio, vermelho = Lula",
       x = NULL, y = NULL) +
  theme_minimal(base_size = 11)
ggsave("R/saldo-por-estado.png", width = 11, height = 7, dpi = 150)

# ------------------------------------------------------------------
# 5. Por região: onde cada candidato cresceu mais na noite
# ------------------------------------------------------------------
primeira <- min(votos$coleta_id); ultima <- max(votos$coleta_id)

votos |>
  filter(coleta_id %in% c(primeira, ultima), numero %in% c(22, 13)) |>
  group_by(regiao, candidato, coleta_id) |>
  summarise(votos = sum(votos), .groups = "drop") |>
  pivot_wider(names_from = coleta_id, values_from = votos) |>
  rename(inicio = 3, fim = 4) |>
  mutate(cresceu = fim - inicio) |>
  arrange(desc(cresceu)) |>
  print()

# ------------------------------------------------------------------
# SQL direto também funciona:
# ------------------------------------------------------------------
dbGetQuery(con, "
  SELECT nome_uf, candidato, votos, ROUND(pct_validos, 1) AS pct
  FROM v_votos
  WHERE coleta_id = (SELECT MAX(coleta_id) FROM coletas)
    AND numero IN (13, 22) AND abrangencia <> 'BR'
  ORDER BY votos DESC
  LIMIT 10")

dbDisconnect(con)
