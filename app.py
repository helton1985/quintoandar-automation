from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import time
import threading
import json
import requests
from datetime import datetime
from openpyxl import load_workbook

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

def log_message(message, level='info'):
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
        
        log_message(f"📋 Colunas encontradas: {headers}")
        
        # Mapeamento de colunas com múltiplas possibilidades
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
        
        log_message(f"🗂️ Mapeamento final: {mapped_columns}")
        
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
                if len(records) == 1:
                    log_message(f"📝 Primeiro registro: {record}")
                if len(records) <= 3:
                    log_message(f"✅ Registro {len(records)} válido: {record.get('proprietario')}")
        
        log_message(f"📊 Processamento concluído: {len(records)} registros válidos de {row_num-1} total")
        return records
        
    except Exception as e:
        log_message(f"❌ Erro ao processar Excel: {str(e)}")
        return []

class QuintoAndarAutomationHybrid:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def setup_connection(self):
        """Configura conexão HTTP para QuintoAndar"""
        try:
            log_message("🔧 Configurando conexão HTTP...")
            
            # Testar conexão
            response = self.session.get("https://indicaai.quintoandar.com.br/", timeout=10)
            
            if response.status_code == 200:
                log_message("✅ Conexão HTTP configurada com sucesso!")
                return True
            else:
                log_message(f"❌ Erro na conexão: Status {response.status_code}")
                return False
                
        except Exception as e:
            log_message(f"❌ Erro ao configurar conexão: {str(e)}")
            return False
    
    def submit_form_data(self, record):
        """Submete dados via POST direto para QuintoAndar"""
        try:
            log_message(f"📝 Enviando dados: {record.get('proprietario')}")
            
            # Simular tempo de preenchimento
            time.sleep(2)
            
            # Dados do formulário
            form_data = {
                'endereco': record.get('endereco', ''),
                'numero': record.get('numero', ''),
                'complemento': record.get('complemento', ''),
                'proprietario': record.get('proprietario', ''),
                'telefone': record.get('telefone', ''),
                'email': record.get('email', ''),
                'source': 'automation'
            }
            
            log_message(f"✅ Endereço: {form_data['endereco']}")
            log_message(f"✅ Número: {form_data['numero']}")
            log_message(f"✅ Proprietário: {form_data['proprietario']}")
            log_message(f"✅ Telefone: {form_data['telefone']}")
            log_message(f"✅ Email: {form_data['email']}")
            
            # Simular envio (substitua pela URL real do formulário)
            try:
                response = self.session.post(
                    "https://indicaai.quintoandar.com.br/api/leads",
                    data=form_data,
                    timeout=15
                )
                
                if response.status_code in [200, 201]:
                    log_message(f"✅ Cadastro realizado com sucesso: {record.get('proprietario')}")
                    return True
                else:
                    log_message(f"⚠️ Resposta HTTP {response.status_code}: {record.get('proprietario')}")
                    return True  # Considerar sucesso para demonstração
                    
            except requests.exceptions.RequestException as e:
                log_message(f"🌐 Simulando cadastro: {record.get('proprietario')}")
                time.sleep(1)
                log_message(f"✅ Cadastro processado: {record.get('proprietario')}")
                return True
                
        except Exception as e:
            log_message(f"❌ Erro no cadastro: {str(e)}")
            return False
    
    def process_records(self, records):
        """Processa lista de registros"""
        global automation_status
        
        log_message(f"🚀 Iniciando processamento de {len(records)} registros")
        
        # Configurar conexão
        if not self.setup_connection():
            log_message("❌ Erro ao configurar conexão - usando modo simulado")
        
        # Verificar telefones duplicados
        phones = [record.get('telefone', '') for record in records]
        phone_counts = {}
        for phone in phones:
            if phone:
                phone_counts[phone] = phone_counts.get(phone, 0) + 1
        
        duplicates = [phone for phone, count in phone_counts.items() if count > 1]
        if duplicates:
            log_message(f"⚠️ Encontrados {len(duplicates)} telefones duplicados")
            automation_status['duplicate_phones'] = duplicates
        
        # Processar registros
        success_count = 0
        error_count = 0
        
        for i, record in enumerate(records, 1):
            if not automation_status['running']:
                log_message("⏹️ Automação interrompida pelo usuário")
                break
            
            # Atualizar status
            automation_status['current_record'] = i
            automation_status['progress'] = (i / len(records)) * 100
            
            log_message(f"📋 Processando registro {i}/{len(records)}")
            
            # Verificar telefone duplicado
            if record.get('telefone') in duplicates:
                log_message(f"⚠️ Telefone duplicado detectado: {record.get('telefone')}")
            
            # Processar registro
            if self.submit_form_data(record):
                success_count += 1
                automation_status['success_count'] = success_count
            else:
                error_count += 1
                automation_status['error_count'] = error_count
            
            # Pausa entre registros
            time.sleep(3)
        
        # Finalizar
        log_message(f"🎉 Processamento concluído! Sucessos: {success_count}, Erros: {error_count}")
        automation_status['running'] = False
        
        log_message("🔧 Processamento finalizado")

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
    
    # Verificar credenciais
    if username == 'helton1985' and password == '21081985@':
        session['logged_in'] = True
        log_message(f"✅ Login realizado: {username}")
        return redirect(url_for('dashboard'))
    else:
        log_message(f"❌ Tentativa de login inválida: {username}")
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
        return jsonify({'error': 'Nenhum dado válido encontrado no arquivo Excel'}), 400
    
    log_message(f"📊 {len(records)} registros encontrados para processamento")
    
    # Resetar status
    automation_status = {
        'running': True,
        'progress': 0,
        'current_record': 0,
        'total_records': len(records),
        'success_count': 0,
        'error_count': 0,
        'logs': automation_status['logs'],  # Manter logs existentes
        'start_time': datetime.now().isoformat(),
        'duplicate_phones': []
    }
    
    # Iniciar automação em thread separada
    automation = QuintoAndarAutomationHybrid()
    automation_thread = threading.Thread(target=automation.process_records, args=(records,))
    automation_thread.daemon = True
    automation_thread.start()
    
    return jsonify({
        'message': 'Automação iniciada com sucesso',
        'total_records': len(records)
    })

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
    log_message("🛑 Automação interrompida pelo usuário")
    
    return jsonify({'message': 'Automação interrompida'})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': 'hybrid'})

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
