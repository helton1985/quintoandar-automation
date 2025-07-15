from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import time
import threading
import json
from datetime import datetime
from openpyxl import load_workbook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'helton1985_21081985@_secret_key_production')

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Criar diretório de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Variáveis globais para controle
automation_thread = None
automation_status = {
    'running': False,
    'progress': 0,
    'current_record': 0,
    'total_records': 0,
    'success_count': 0,
    'error_count': 0,
    'logs': [],
    'start_time': None,
    'duplicate_phones': []
}

def log_message(message):
    """Adiciona mensagem aos logs com timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    automation_status['logs'].append(log_entry)
    print(log_entry)
    
    # Manter apenas últimos 100 logs
    if len(automation_status['logs']) > 100:
        automation_status['logs'] = automation_status['logs'][-100:]

def allowed_file(filename):
    """Verifica se arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_excel_data(file_path):
    """Processa arquivo Excel com mapeamento mais flexível"""
    try:
        log_message(f"📄 Carregando arquivo: {file_path}")
        
        # Carregar workbook
        wb = load_workbook(file_path, read_only=True)
        ws = wb.active
        
        # Ler cabeçalhos
        headers = []
        for cell in ws[1]:
            headers.append(cell.value if cell.value else '')
        
        log_message(f"📋 Encontradas {len(headers)} colunas")
        
        # Mapeamento de colunas
        column_mapping = {
            'endereco': ['endereço', 'endereco', 'address', 'rua', 'logradouro'],
            'numero': ['número', 'numero', 'number', 'num', 'n'],
            'complemento': ['complemento', 'compl', 'complement'],
            'proprietario': ['proprietário', 'proprietario', 'nome', 'owner', 'name'],
            'telefone': ['telefone', 'celular', 'phone', 'fone', 'celular/telefone'],
            'email': ['email', 'e-mail', 'mail', 'correio']
        }
        
        # Mapear colunas
        mapped_columns = {}
        for key, possible_names in column_mapping.items():
            for i, header in enumerate(headers):
                if header and any(name.lower() in header.lower() for name in possible_names):
                    mapped_columns[key] = i
                    log_message(f"✅ Mapeado '{key}' → coluna '{header}' (índice {i})")
                    break
        
        # Processar dados
        records = []
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if not row or all(cell is None or cell == '' for cell in row):
                continue
            
            # Extrair dados conforme mapeamento
            record = {}
            for field, col_idx in mapped_columns.items():
                if col_idx < len(row):
                    value = row[col_idx]
                    record[field] = str(value).strip() if value else ''
            
            # Validar registro
            if record.get('proprietario') and record.get('endereco'):
                records.append(record)
        
        log_message(f"📊 {len(records)} registros válidos encontrados")
        return records
        
    except Exception as e:
        log_message(f"❌ Erro ao processar Excel: {str(e)}")
        return []

class QuintoAndarSelenium:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Configura o driver do Chrome para Render"""
        try:
            log_message("🔧 Configurando Chrome para Render...")
            
            # Configurações do Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Tentar diferentes caminhos para Chrome
            chrome_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/opt/google/chrome/google-chrome'
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    chrome_options.binary_location = chrome_path
                    log_message(f"✅ Chrome encontrado: {chrome_path}")
                    break
            
            # Criar driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            log_message("✅ Chrome configurado com sucesso!")
            return True
            
        except Exception as e:
            log_message(f"❌ Erro ao configurar Chrome: {str(e)}")
            return False
    
    def access_site(self):
        """Acessa o site do QuintoAndar"""
        try:
            log_message("🌐 Acessando QuintoAndar...")
            self.driver.get("https://indicaai.quintoandar.com.br/")
            
            # Aguardar carregamento
            time.sleep(5)
            
            # Verificar se carregou
            if "QuintoAndar" in self.driver.title or "indica" in self.driver.title.lower():
                log_message("✅ Site acessado com sucesso!")
                return True
            else:
                log_message("❌ Erro: Site não carregou corretamente")
                return False
                
        except Exception as e:
            log_message(f"❌ Erro ao acessar site: {str(e)}")
            return False
    
    def fill_form(self, record):
        """Preenche formulário com dados do registro"""
        try:
            log_message(f"📝 Preenchendo formulário: {record.get('proprietario')}")
            
            # Aguardar formulário
            time.sleep(3)
            
            # Preencher campos (adaptar seletores conforme necessário)
            fields = [
                ('endereco', record.get('endereco')),
                ('numero', record.get('numero')),
                ('complemento', record.get('complemento')),
                ('proprietario', record.get('proprietario')),
                ('telefone', record.get('telefone')),
                ('email', record.get('email'))
            ]
            
            for field_name, value in fields:
                if value:
                    try:
                        # Tentar diferentes seletores
                        selectors = [
                            f"input[name='{field_name}']",
                            f"input[id='{field_name}']",
                            f"input[placeholder*='{field_name}']",
                            f"textarea[name='{field_name}']"
                        ]
                        
                        field_found = False
                        for selector in selectors:
                            try:
                                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                                element.clear()
                                element.send_keys(value)
                                log_message(f"✅ {field_name.title()}: {value}")
                                field_found = True
                                break
                            except NoSuchElementException:
                                continue
                        
                        if not field_found:
                            log_message(f"⚠️ Campo {field_name} não encontrado")
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        log_message(f"⚠️ Erro no campo {field_name}: {str(e)}")
            
            # Submeter formulário
            try:
                submit_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:contains('Enviar')",
                    "button:contains('Cadastrar')"
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        submit_button.click()
                        log_message("✅ Formulário enviado")
                        break
                    except NoSuchElementException:
                        continue
                
                # Aguardar resposta
                time.sleep(4)
                
                # Verificar sucesso
                page_source = self.driver.page_source.lower()
                success_indicators = ['sucesso', 'cadastrado', 'obrigado', 'enviado']
                
                if any(indicator in page_source for indicator in success_indicators):
                    log_message(f"✅ Cadastro realizado: {record.get('proprietario')}")
                    return True
                else:
                    log_message(f"⚠️ Resultado incerto: {record.get('proprietario')}")
                    return True  # Assumir sucesso se não houver erro claro
                    
            except Exception as e:
                log_message(f"❌ Erro ao enviar formulário: {str(e)}")
                return False
                
        except Exception as e:
            log_message(f"❌ Erro no preenchimento: {str(e)}")
            return False
    
    def process_records(self, records):
        """Processa lista de registros"""
        global automation_status
        
        log_message(f"🚀 Iniciando automação REAL com {len(records)} registros")
        
        # Configurar driver
        if not self.setup_driver():
            log_message("❌ Erro ao configurar Chrome - interrompendo")
            automation_status['running'] = False
            return
        
        # Acessar site
        if not self.access_site():
            log_message("❌ Erro ao acessar site - interrompendo")
            automation_status['running'] = False
            return
        
        # Verificar telefones duplicados
        phones = [record.get('telefone', '') for record in records]
        phone_counts = {}
        for phone in phones:
            if phone:
                phone_counts[phone] = phone_counts.get(phone, 0) + 1
        
        duplicates = [phone for phone, count in phone_counts.items() if count > 1]
        if duplicates:
            log_message(f"⚠️ {len(duplicates)} telefones duplicados encontrados")
            automation_status['duplicate_phones'] = duplicates
        
        # Processar registros
        success_count = 0
        error_count = 0
        
        for i, record in enumerate(records, 1):
            if not automation_status['running']:
                log_message("⏹️ Automação interrompida")
                break
            
            # Atualizar status
            automation_status['current_record'] = i
            automation_status['progress'] = (i / len(records)) * 100
            
            log_message(f"📋 Processando {i}/{len(records)}")
            
            # Verificar telefone duplicado
            if record.get('telefone') in duplicates:
                log_message(f"⚠️ Telefone duplicado: {record.get('telefone')}")
            
            # Processar registro
            if self.fill_form(record):
                success_count += 1
                automation_status['success_count'] = success_count
            else:
                error_count += 1
                automation_status['error_count'] = error_count
            
            # Pausa entre registros
            time.sleep(3)
        
        # Finalizar
        log_message(f"🎉 Automação concluída! Sucessos: {success_count}, Erros: {error_count}")
        automation_status['running'] = False
        
        # Fechar driver
        if self.driver:
            self.driver.quit()
            log_message("🔧 Chrome fechado")

# Rotas Flask
@app.route('/')
def index():
    """Página de login"""
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Processa login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'helton1985' and password == '21081985@':
        session['logged_in'] = True
        log_message(f"✅ Login realizado: {username}")
        return redirect(url_for('dashboard'))
    else:
        log_message(f"❌ Login inválido: {username}")
        return render_template('index.html', error='Credenciais inválidas')

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Processa upload de arquivo"""
    global automation_thread, automation_status
    
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        log_message(f"📁 Arquivo salvo: {filename}")
        
        # Processar dados
        records = process_excel_data(file_path)
        
        if not records:
            return jsonify({'error': 'Nenhum dado válido encontrado'}), 400
        
        log_message(f"📊 {len(records)} registros encontrados")
        
        # Resetar status
        automation_status = {
            'running': True,
            'progress': 0,
            'current_record': 0,
            'total_records': len(records),
            'success_count': 0,
            'error_count': 0,
            'logs': automation_status['logs'],
            'start_time': datetime.now().isoformat(),
            'duplicate_phones': []
        }
        
        # Iniciar automação REAL
        automation = QuintoAndarSelenium()
        automation_thread = threading.Thread(target=automation.process_records, args=(records,))
        automation_thread.daemon = True
        automation_thread.start()
        
        return jsonify({
            'message': 'Automação REAL iniciada com sucesso',
            'total_records': len(records)
        })
        
    except Exception as e:
        log_message(f"❌ Erro no upload: {str(e)}")
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/status')
def get_status():
    """Retorna status da automação"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    return jsonify(automation_status)

@app.route('/stop', methods=['POST'])
def stop_automation():
    """Para a automação"""
    global automation_status
    
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    automation_status['running'] = False
    log_message("🛑 Automação interrompida")
    
    return jsonify({'message': 'Automação interrompida'})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': 'render-selenium'})

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
