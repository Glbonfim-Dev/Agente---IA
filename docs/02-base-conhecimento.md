# Base de Conhecimento

## Dados Utilizados

Descreva se usou os arquivos da pasta `data`, por exemplo:

| Arquivo | Formato | Utilização no Agente |
|---------|---------|---------------------|
| `historico_atendimento.csv` | CSV | Contextualizar interações anteriores |
| `perfil_investidor.json` | JSON | Personalizar recomendações |
| `produtos_financeiros.json` | JSON | Sugerir produtos adequados ao perfil |
| `transacoes.csv` | CSV | Analisar padrão de gastos do cliente |

---

## Estratégia de Integração

### Como os dados são carregados?
> Descreva como seu agente acessa a base de conhecimento.

Os JSON/CSV são carregados no início da sessão e incluídos no contexto do prompt

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

SYSTEM
Regras permanentes, segurança e comportamento do agente.

DEVELOPER
Instruções da aplicação e formato da tarefa.

CONTEXT / TOOL RESULT
Dados recuperados do banco, API, planilha ou documento.

USER
Pergunta atual do usuário.

---

## Exemplo de Contexto Montado

> Mostre um exemplo de como os dados são formatados para o agente.

```
TAREFA
Analise o desempenho do usuário entre 01/07/2026 e 22/07/2026.

REGRAS
- Use apenas os dados incluídos neste contexto.
- Não invente causas para os resultados.
- Não faça previsões de lucro futuro.
- Não recomende aumento de valores.
- Informe limitações da amostra.
- Destaque sinais de perseguição de perdas.

<perfil_usuario>
Nível: intermediário
Moeda: BRL
Banca atual: R$ 1.200,00
Limite semanal: R$ 150,00
</perfil_usuario>

<indicadores_calculados>
Total de apostas: 42
Valor apostado: R$ 840,00
Retorno total: R$ 781,20
Resultado líquido: -R$ 58,80
ROI: -7,00%
Taxa de acerto: 45,24%
Drawdown máximo: -R$ 126,00
</indicadores_calculados>

<desempenho_por_mercado>
1. Mais de 2,5 gols
   Apostas: 16
   Resultado: +R$ 28,40
   ROI: +8,88%

2. Resultado final
   Apostas: 14
   Resultado: -R$ 71,20
   ROI: -25,43%

3. Ambas marcam
   Apostas: 8
   Resultado: +R$ 4,00
   ROI: +2,50%

4. Apostas múltiplas
   Apostas: 4
   Resultado: -R$ 20,00
   ROI: -25,00%
</desempenho_por_mercado>

<sinais_de_risco>
- Em 3 ocasiões, o valor apostado aumentou mais de 50% após uma perda.
- Severidade estimada: média.
</sinais_de_risco>

<qualidade_dos_dados>
Confiança: moderada
Apostas não liquidadas: 2
Limitações:
- A amostra por mercado é pequena.
- Duas apostas ainda podem alterar o resultado.
- Desempenho passado não prevê resultados futuros.
</qualidade_dos_dados>

FORMATO DA RESPOSTA
1. Resumo do período
2. Mercado com maior perda
3. Padrões observados
4. Alertas de risco
5. Limitações da análise
```
