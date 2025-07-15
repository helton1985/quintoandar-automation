from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import time
import threading
import json
from datetime import datetime
from openpyxl import load_workbook

app = Flask(__name__)
app.secret_key = 'helton1985_21081985@_secret_key_production'

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
    
    # Manter apenas últimos 50 logs
    if len(automation_status['logs']) > 50:
        automation_status['logs'] = automation_status['logs'][-50:]

def allowed_file(filename):
    """Verifica se arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_excel_data(file_path):
    """Processa arquivo Excel"""
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
        
        # Mapeamento simples
        column_mapping = {}
        for i, header in enumerate(headers):
            if header:
                header_lower = header.lower()
                if 'endereco' in header_lower or 'endereço' in header_lower:
                    column_mapping['endereco'] = i
                elif 'numero' in header_lower or 'número' in header_lower:
                    column_mapping['numero'] = i
                elif 'complemento' in header_lower:
                    column_mapping['complemento'] = i
                elif 'proprietario' in header_lower or 'proprietário' in header_lower or 'nome' in header_lower:
                    column_mapping['proprietario'] = i
                elif 'telefone' in header_lower or 'celular' in header_lower or 'phone' in header_lower:
                    column_mapping['telefone'] = i
                elif 'email' in header_lower or 'e-mail' in header_lower:
                    column_mapping['email'] = i
        
        log_message(f"🗂️ Mapeamento: {column_mapping}")
        
        # Processar dados
        records = []
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if not row:
                continue
            
            record = {}
            for field, col_idx in column_mapping.items():
                if col_idx < len(row) and row[col_idx]:
                    record[field] = str(row[col_idx]).strip()
                else:
                    record[field] = ''
            
            # Validar registro
            if record.get('proprietario') and record.get('endereco'):
                records.append(record)
        
        log_message(f"📊 {len(records)} registros válidos encontrados")
        return records
        
    except Exception as e:
        log_message(f"❌ Erro ao processar Excel: {str(e)}")
        return []

def process_automation(records):
    """Processa automação"""
    global automation_status
    
    log_message(f"🚀 Iniciando automação com {len(records)} registros")
    
    # Verificar telefones duplicados
    phones = [r.get('telefone', '') for r in records if r.get('telefone')]
    phone_counts = {}
    for phone in phones:
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
        
        log_message(f"📋 Processando {i}/{len(records)}: {record.get('proprietario')}")
        
        # Simular processamento
        time.sleep(2)
        
        # Verificar dados
        if record.get('telefone') in duplicates:
            log_message(f"⚠️ Telefone duplicado: {record.get('telefone')}")
        
        # Mostrar dados
        log_message(f"📍 Endereço: {record.get('endereco')}")
        log_message(f"🔢 Número: {record.get('numero')}")
        log_message(f"👤 Proprietário: {record.get('proprietario')}")
        log_message(f"📞 Telefone: {record.get('telefone')}")
        log_message(f"📧 Email: {record.get('email')}")
        
        # Simular envio
        time.sleep(1)
        
        # Resultado (90% sucesso)
        if i % 10 != 0:  # 90% sucesso
            log_message(f"✅ Cadastro realizado: {record.get('proprietario')}")
            success_count += 1
        else:
            log_message(f"❌ Erro no cadastro: {record.get('proprietario')}")
            error_count += 1
        
        automation_status['success_count'] = success_count
        automation_status['error_count'] = error_count
        
        # Pausa entre registros
        time.sleep(1)
    
    # Finalizar
    log_message(f"🎉 Concluído! Sucessos: {success_count}, Erros: {error_count}")
    automation_status['running'] = False

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
        return redirect(url_for('dashboard'))
    else:
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
        
        # Iniciar automação
        automation_thread = threading.Thread(target=process_automation, args=(records,))
        automation_thread.daemon = True
        automation_thread.start()
        
        return jsonify({
            'message': 'Automação iniciada com sucesso',
            'total_records': len(records)
        })
        
    except Exception as e:
        log_message(f"❌ Erro no upload: {str(e)}")
        return jsonify({'error': f'Erro no upload: {str(e)}'}), 500

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
    return jsonify({'status': 'healthy', 'version': 'minimal'})

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
