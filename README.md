# 🏠 Sistema de Automação QuintoAndar

Sistema para automação de cadastros no site indicaai.quintoandar.com.br

## 🚀 Deploy Online

Este sistema está pronto para deploy em plataformas como Railway, Render ou Heroku.

## 🔐 Credenciais de Acesso

- **Usuário:** helton1985
- **Senha:** 21081985@

## ✨ Funcionalidades

- ✅ Upload de planilha Excel
- ✅ Automação com Selenium WebDriver
- ✅ Verificação automática de telefones duplicados
- ✅ Preenchimento inteligente de formulários
- ✅ Monitoramento em tempo real
- ✅ Logs detalhados de cada operação
- ✅ Interface web responsiva
- ✅ Tratamento robusto de erros

## 📋 Formato da Planilha Excel

O sistema aceita planilhas com as seguintes colunas (nomes flexíveis):

| Campo | Nomes Aceitos |
|-------|---------------|
| **Endereço** | Endereço, endereco, address |
| **Número** | Número, numero, number |
| **Complemento** | Complemento, complemento |
| **Proprietário** | Proprietário, proprietario, nome |
| **Telefone** | Celular, Telefone, telefone, phone |
| **E-mail** | E-mail, Email, email |

## 🔄 Como Funciona

1. **Verificação prévia:** Sistema verifica se telefone já está cadastrado
2. **Preenchimento automático:** Combina endereço + número
3. **Seleção inteligente:** Escolhe primeira sugestão de endereço
4. **Complemento padrão:** Adiciona "Apartamento" automaticamente
5. **Submissão:** Envia formulário e verifica sucesso

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python Flask
- **Automação:** Selenium WebDriver + Chrome Headless
- **Processamento:** Pandas + OpenPyXL
- **Frontend:** HTML5, CSS3, JavaScript
- **Deploy:** Gunicorn + Railway/Heroku

## 📊 Monitoramento

- Contador de registros processados
- Taxa de sucesso vs erros
- Logs em tempo real
- Barra de progresso visual
- Status da automação

## 🌐 Deploy

Sistema otimizado para deploy em:
- Railway (Recomendado - Gratuito)
- Render (Gratuito com limitações)
- Heroku (Pago)
- Google Cloud Run

## 🔒 Segurança

- Autenticação obrigatória
- Sessões seguras
- Validação de arquivos
- Limpeza automática de uploads
- Logs sem dados sensíveis

---

**Desenvolvido para automação eficiente de cadastros imobiliários** 🏠