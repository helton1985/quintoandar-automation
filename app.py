from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import time
import threading
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'helton1985_21081985@_secret_key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Variáveis globais para controle
automation_status = {
    'running': False,
    'current_record': 0,
    'total_records': 0,
    'success_count': 0,
    'error_count': 0,
    'logs': []
}

class QuintoAndarAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """Configura o driver do Chrome para produção"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Para ambientes de produção
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            
            # Tentar usar webdriver-manager primeiro, depois fallback
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            except:
                # Fallback para sistemas que já têm chromedriver instalado
                service = Service('/usr/bin/chromedriver')
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            return True
        except Exception as e:
            print(f"Erro ao configurar driver: {e}")
            return False

    def navigate_to_site(self):
        """Navega até o site do QuintoAndar"""
        try:
            self.driver.get("https://indicaai.quintoandar.com.br/")
            time.sleep(5)
            # Verificar se a página carregou
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return True
        except Exception as e:
            print(f"Erro ao navegar para o site: {e}")
            return False

    def check_phone_exists(self, phone):
        """Verifica se o telefone já está cadastrado"""
        try:
            # Limpar e formatar telefone
            phone = str(phone).replace('+55', '').replace('55', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '').strip()
            
            # Múltiplos seletores para campo de telefone
            phone_selectors = [
                "input[type='tel']",
                "input[placeholder*='telefone' i]",
                "input[placeholder*='celular' i]",
                "input[name*='phone' i]",
                "input[name*='telefone' i]",
                "input[name*='celular' i]",
                "input[id*='phone' i]",
                "input[id*='telefone' i]",
                "input[id*='celular' i]"
            ]
            
            phone_field = None
            for selector in phone_selectors:
                try:
                    phone_field = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if phone_field.is_displayed() and phone_field.is_enabled():
                        break
                except:
                    continue
            
            if not phone_field:
                log_message("❌ Campo de telefone não encontrado")
                return False
            
            # Limpar campo e inserir telefone
            phone_field.clear()
            time.sleep(1)
            phone_field.send_keys(phone)
            time.sleep(3)

            # Verificar mensagens de erro ou validação
            error_selectors = [
                ".error", ".alert", "[class*='error' i]", "[class*='alert' i]",
                ".notification", ".message", "[class*='notification' i]",
                ".warning", "[class*='warning' i]", ".invalid", "[class*='invalid' i]"
            ]
            
            for selector in error_selectors:
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in error_elements:
                        if element.is_displayed():
                            text = element.text.lower()
                            if any(phrase in text for phrase in ["já cadastrado", "já existe", "already exists", "já utilizado", "duplicado"]):
                                return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"Erro ao verificar telefone: {e}")
            return False

    def fill_property_form(self, data):
        """Preenche o formulário com os dados do imóvel"""
        try:
            # 1. Preencher endereço + número
            address_selectors = [
                "input[placeholder*='endereço' i]",
                "input[placeholder*='endereco' i]",
                "input[name*='address' i]",
                "input[name*='endereco' i]",
                "input[id*='address' i]",
                "input[id*='endereco' i]",
                "input[type='text'][placeholder*='rua' i]"
            ]
            
            address_field = None
            for selector in address_selectors:
                try:
                    address_field = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if address_field.is_displayed() and address_field.is_enabled():
                        break
                except:
                    continue
            
            if address_field:
                full_address = f"{data.get('endereco', '')}, {data.get('numero', '')}"
                address_field.clear()
                time.sleep(1)
                address_field.send_keys(full_address)
                time.sleep(4)

                # Tentar selecionar primeira sugestão
                suggestion_selectors = [
                    ".suggestion", ".autocomplete-item", "[role='option']",
                    ".dropdown-item", ".search-result", ".address-suggestion",
                    ".pac-item", ".pac-container .pac-item",
                    "[class*='suggestion' i]", "[class*='autocomplete' i]"
                ]
                
                suggestion_found = False
                for selector in suggestion_selectors:
                    try:
                        suggestions = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        visible_suggestions = [s for s in suggestions if s.is_displayed()]
                        if visible_suggestions:
                            visible_suggestions[0].click()
                            time.sleep(2)
                            suggestion_found = True
                            break
                    except:
                        continue
                
                if not suggestion_found:
                    # Tentar pressionar Enter se não houver sugestões
                    try:
                        from selenium.webdriver.common.keys import Keys
                        address_field.send_keys(Keys.ENTER)
                        time.sleep(2)
                    except:
                        pass

            # 2. Preencher complemento
            complement_selectors = [
                "input[placeholder*='complemento' i]",
                "input[name*='complement' i]",
                "input[name*='complemento' i]",
                "input[id*='complement' i]",
                "input[id*='complemento' i]"
            ]
            
            for selector in complement_selectors:
                try:
                    complement_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if complement_field.is_displayed() and complement_field.is_enabled():
                        complement_field.clear()
                        time.sleep(1)
                        complement_text = f"Apartamento {data.get('complemento', '')}" if data.get('complemento') else "Apartamento"
                        complement_field.send_keys(complement_text)
                        break
                except:
                    continue

            # 3. Preencher nome do proprietário
            owner_selectors = [
                "input[placeholder*='proprietário' i]",
                "input[placeholder*='proprietario' i]",
                "input[name*='owner' i]",
                "input[name*='proprietario' i]",
                "input[name*='nome' i]",
                "input[id*='owner' i]",
                "input[id*='proprietario' i]",
                "input[id*='nome' i]"
            ]
            
            owner_filled = False
            for selector in owner_selectors:
                try:
                    owner_field = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if owner_field.is_displayed() and owner_field.is_enabled():
                        owner_field.clear()
                        time.sleep(1)
                        owner_field.send_keys(data.get('proprietario', ''))
                        owner_filled = True
                        break
                except:
                    continue
            
            if not owner_filled:
                log_message("⚠️ Campo proprietário não encontrado")

            # 4. Preencher email se disponível
            if data.get('email'):
                email_selectors = [
                    "input[type='email']",
                    "input[placeholder*='email' i]",
                    "input[name*='email' i]",
                    "input[id*='email' i]"
                ]
                
                for selector in email_selectors:
                    try:
                        email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if email_field.is_displayed() and email_field.is_enabled():
                            email_field.clear()
                            time.sleep(1)
                            email_field.send_keys(data['email'])
                            break
                    except:
                        continue

            return True
        except Exception as e:
            print(f"Erro ao preencher formulário: {e}")
            return False

    def submit_form(self):
        """Submete o formulário"""
        try:
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".btn-submit",
                "[class*='submit' i]",
                ".submit-btn",
                "button:contains('Enviar')",
                "button:contains('Cadastrar')",
                "button:contains('Indicar')"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if submit_button.is_displayed() and submit_button.is_enabled():
                        break
                except:
                    continue
            
            if submit_button:
                submit_button.click()
                time.sleep(5)

                # Verificar sinais de sucesso
                success_selectors = [
                    ".success", ".confirmation", "[class*='success' i]",
                    ".thank-you", "[class*='thank' i]", ".completed",
                    "[class*='confirm' i]", ".done", "[class*='done' i]"
                ]
                
                for selector in success_selectors:
                    try:
                        success_indicators = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        visible_success = [s for s in success_indicators if s.is_displayed()]
                        if visible_success:
                            return True
                    except:
                        continue
                
                # Se não houver indicadores explícitos, assumir sucesso se não houver erros
                error_selectors = [".error", ".alert", "[class*='error' i]"]
                has_errors = False
                for selector in error_selectors:
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        visible_errors = [e for e in error_elements if e.is_displayed()]
                        if visible_errors:
                            has_errors = True
                            break
                    except:
                        continue
                
                return not has_errors
            
            return False
        except Exception as e:
            print(f"Erro ao submeter formulário: {e}")
            return False

    def close_driver(self):
        """Fecha o driver"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

def log_message(message):
    """Adiciona mensagem ao log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    automation_status['logs'].append(log_entry)
    
    # Manter apenas os últimos 100 logs para evitar uso excessivo de memória
    if len(automation_status['logs']) > 100:
        automation_status['logs'] = automation_status['logs'][-100:]
    
    print(log_entry)

def process_excel_data(file_path):
    """Processa arquivo Excel e retorna dados"""
    try:
        # Tentar ler Excel com diferentes engines
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except:
            try:
                df = pd.read_excel(file_path, engine='xlrd')
            except:
                df = pd.read_excel(file_path)

        # Mapear colunas da planilha com mais variações
        column_mapping = {
            'endereco': ['Endereço', 'endereco', 'address', 'Address', 'ENDERECO', 'ENDEREÇO', 'Rua', 'rua'],
            'numero': ['Número', 'numero', 'number', 'Number', 'NUMERO', 'NÚMERO', 'Num', 'num', 'Nº'],
            'complemento': ['Complemento', 'complemento', 'complement', 'Complement', 'COMPLEMENTO', 'Compl', 'compl'],
            'proprietario': ['Proprietário', 'proprietario', 'owner', 'Owner', 'nome', 'Nome', 'PROPRIETARIO', 'PROPRIETÁRIO', 'NOME'],
            'telefone': ['Celular', 'Telefone', 'celular', 'telefone', 'phone', 'Phone', 'CELULAR', 'TELEFONE', 'Tel', 'tel', 'Cel', 'cel'],
            'email': ['E-mail', 'Email', 'email', 'EMAIL', 'E-MAIL', 'Mail', 'mail', 'E_mail']
        }

        data_list = []
        for index, row in df.iterrows():
            record = {}
            for key, possible_columns in column_mapping.items():
                record[key] = ''
                for col in possible_columns:
                    if col in df.columns and pd.notna(row[col]) and str(row[col]).strip():
                        record[key] = str(row[col]).strip()
                        break

            # Filtrar registros válidos (obrigatórios: endereço, telefone, proprietário)
            if record.get('endereco') and record.get('telefone') and record.get('proprietario'):
                data_list.append(record)

        return data_list
    except Exception as e:
        log_message(f"❌ Erro ao processar Excel: {str(e)}")
        return []

def run_automation(file_path):
    """Executa a automação de cadastros"""
    global automation_status

    try:
        # Reset status
        automation_status['running'] = True
        automation_status['current_record'] = 0
        automation_status['success_count'] = 0
        automation_status['error_count'] = 0
        automation_status['logs'] = []

        log_message("🚀 Iniciando automação de cadastros...")

        # Processar dados do Excel
        data_list = process_excel_data(file_path)
        automation_status['total_records'] = len(data_list)

        if not data_list:
            log_message("❌ Nenhum dado válido encontrado no arquivo Excel")
            return

        log_message(f"📊 {len(data_list)} registros encontrados para processamento")

        # Configurar automação
        automation = QuintoAndarAutomation()
        if not automation.setup_driver():
            log_message("❌ Erro ao configurar navegador Chrome")
            return

        if not automation.navigate_to_site():
            log_message("❌ Erro ao acessar o site QuintoAndar")
            automation.close_driver()
            return

        log_message("✅ Navegador configurado e site acessado com sucesso")

        # Processar cada registro
        for i, record in enumerate(data_list, 1):
            if not automation_status['running']:  # Verificar se foi cancelado
                break
                
            automation_status['current_record'] = i
            log_message(f"🔄 Processando registro {i}/{len(data_list)}: {record['proprietario']}")

            try:
                # Verificar se telefone já existe
                if automation.check_phone_exists(record['telefone']):
                    log_message(f"⚠️ Telefone já cadastrado, pulando: {record['telefone']}")
                    automation_status['error_count'] += 1
                    continue

                # Preencher formulário
                if automation.fill_property_form(record):
                    if automation.submit_form():
                        log_message(f"✅ Cadastro realizado com sucesso: {record['proprietario']}")
                        automation_status['success_count'] += 1
                    else:
                        log_message(f"❌ Erro ao submeter formulário: {record['proprietario']}")
                        automation_status['error_count'] += 1
                else:
                    log_message(f"❌ Erro ao preencher formulário: {record['proprietario']}")
                    automation_status['error_count'] += 1

                # Pausa entre registros
                time.sleep(3)

            except Exception as e:
                log_message(f"❌ Erro no cadastro: {record['proprietario']} - {str(e)}")
                automation_status['error_count'] += 1
                continue

        automation.close_driver()
        log_message(f"🏁 Automação finalizada! ✅ Sucessos: {automation_status['success_count']} | ❌ Erros: {automation_status['error_count']}")

    except Exception as e:
        log_message(f"❌ Erro geral na automação: {str(e)}")
    finally:
        automation_status['running'] = False
        # Limpar arquivo após processamento
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

# ========== ROTAS FLASK ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if username == 'helton1985' and password == '21081985@':
        session['logged_in'] = True
        session.permanent = True
        return redirect(url_for('dashboard'))
    else:
        return render_template('index.html', error='Credenciais inválidas. Verifique usuário e senha.')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado. Faça login primeiro.'}), 401

    if automation_status['running']:
        return jsonify({'error': 'Automação já está em execução. Aguarde finalizar.'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo foi selecionado.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo foi selecionado.'}), 400

    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Apenas arquivos Excel (.xlsx, .xls) são permitidos.'}), 400

    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Verificar se arquivo foi salvo corretamente
        if not os.path.exists(file_path):
            return jsonify({'error': 'Erro ao salvar arquivo. Tente novamente.'}), 500

        # Iniciar automação em thread separada
        thread = threading.Thread(target=run_automation, args=(file_path,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True, 
            'message': 'Arquivo carregado com sucesso! Automação iniciada.'
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@app.route('/status')
def status():
    """Retorna status atual da automação"""
    return jsonify(automation_status)

@app.route('/stop')
def stop_automation():
    """Para a automação em execução"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    automation_status['running'] = False
    log_message("⏹️ Automação interrompida pelo usuário")
    return jsonify({'success': True, 'message': 'Automação interrompida com sucesso'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check para monitoramento"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'running': automation_status['running']
    })

# ========== CONFIGURAÇÃO DE PRODUÇÃO ==========

if __name__ == '__main__':
    # Configuração para produção
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port,
        threaded=True
    )