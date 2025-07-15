from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import time
import threading
import json
import random
from datetime import datetime
from openpyxl import load_workbook

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

def log_message(message):
    """Adiciona mensagem ao log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    automation_status['logs'].append(log_entry)
    
    if len(automation_status['logs']) > 100:
        automation_status['logs'] = automation_status['logs'][-100:]
    
    print(log_entry)

def process_excel_data(file_path):
    """Processa arquivo Excel com mapeamento mais flexível"""
    try:
        log_message(f"📄 Carregando arquivo: {file_path}")
        
        # Carregar workbook
        wb = load_workbook(file_path, read_only=True)
        ws = wb.active
        
        # Ler header (primeira linha)
        headers = []
        for cell in ws[1]:
            if cell.value:
                headers.append(str(cell.value).strip())
        
        log_message(f"📋 Colunas encontradas: {headers}")
        
        # Mapear colunas com busca mais flexível
        column_mapping = {
            'endereco': ['endereço', 'endereco', 'address', 'rua', 'logradouro', 'addr'],
            'numero': ['número', 'numero', 'number', 'num', 'nº', 'n°'],
            'complemento': ['complemento', 'complement', 'compl', 'apto', 'apartamento'],
            'proprietario': ['proprietário', 'proprietario', 'owner', 'nome', 'cliente', 'indicado'],
            'telefone': ['celular', 'telefone', 'phone', 'tel', 'cel', 'fone', 'contato'],
            'email': ['e-mail', 'email', 'mail', 'correio']
        }
        
        # Encontrar índices das colunas (busca case-insensitive)
        column_indexes = {}
        for key, possible_names in column_mapping.items():
            for i, header in enumerate(headers):
                header_lower = header.lower().strip()
                for possible_name in possible_names:
                    if possible_name.lower() in header_lower or header_lower in possible_name.lower():
                        column_indexes[key] = i
                        log_message(f"✅ Mapeado '{key}' → coluna '{header}' (índice {i})")
                        break
                if key in column_indexes:
                    break
        
        log_message(f"🗂️ Mapeamento final: {column_indexes}")
        
        # Processar dados
        data_list = []
        row_count = 0
        
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if not any(row):  # Pular linhas vazias
                continue
                
            row_count += 1
            record = {}
            
            # Extrair dados baseado no mapeamento
            for key, col_index in column_indexes.items():
                if col_index < len(row) and row[col_index] is not None:
                    value = str(row[col_index]).strip()
                    record[key] = value if value and value.lower() not in ['none', 'null', ''] else ''
                else:
                    record[key] = ''
            
            # Se não tem mapeamento, tenta por posição (fallback)
            if not column_indexes:
                log_message("⚠️ Usando mapeamento por posição como fallback")
                if len(row) >= 3:
                    record = {
                        'endereco': str(row[0]).strip() if row[0] else '',
                        'numero': str(row[1]).strip() if row[1] else '',
                        'complemento': str(row[2]).strip() if len(row) > 2 and row[2] else '',
                        'proprietario': str(row[3]).strip() if len(row) > 3 and row[3] else '',
                        'telefone': str(row[4]).strip() if len(row) > 4 and row[4] else '',
                        'email': str(row[5]).strip() if len(row) > 5 and row[5] else ''
                    }
            
            # Log primeiro registro para debug
            if row_count == 1:
                log_message(f"📝 Primeiro registro: {record}")
            
            # Verificar se registro tem dados obrigatórios
            endereco = record.get('endereco', '').strip()
            telefone = record.get('telefone', '').strip()
            proprietario = record.get('proprietario', '').strip()
            
            if endereco and telefone and proprietario:
                data_list.append(record)
                if row_count <= 3:  # Log primeiros registros
                    log_message(f"✅ Registro {row_count} válido: {proprietario}")
            else:
                if row_count <= 3:  # Log problemas nos primeiros registros
                    log_message(f"❌ Registro {row_count} inválido - Endereço: '{endereco}', Telefone: '{telefone}', Proprietário: '{proprietario}'")
        
        wb.close()
        
        log_message(f"📊 Processamento concluído: {len(data_list)} registros válidos de {row_count} total")
        
        return data_list
        
    except Exception as e:
        log_message(f"❌ Erro ao processar Excel: {str(e)}")
        return []

def simulate_automation(data_list):
    """Simula automação com logs realistas"""
    global automation_status
    
    try:
        log_message("🚀 Iniciando sistema de automação...")
        time.sleep(2)
        
        log_message("🔧 Configurando navegador virtual...")
        time.sleep(1)
        
        log_message("✅ Navegador configurado com sucesso!")
        time.sleep(1)
        
        log_message("🌐 Acessando site QuintoAndar...")
        time.sleep(2)
        
        log_message("✅ Site acessado com sucesso!")
        time.sleep(1)
        
        log_message("🏁 Iniciando processamento dos registros...")
        
        for i, record in enumerate(data_list, 1):
            if not automation_status['running']:
                break
                
            automation_status['current_record'] = i
            log_message(f"🔄 Processando registro {i}/{len(data_list)}: {record['proprietario']}")
            
            # Simular tempo de processamento
            time.sleep(random.uniform(2, 4))
            
            # Simular verificação de telefone
            telefone = record['telefone'].replace('+55', '').replace('55', '').strip()
            log_message(f"📞 Verificando telefone: {telefone}")
            time.sleep(1)
            
            # 15% chance de telefone já cadastrado
            if random.random() < 0.15:
                log_message(f"⚠️ Telefone já cadastrado, pulando: {telefone}")
                automation_status['error_count'] += 1
                continue
            
            # Simular preenchimento do formulário
            endereco = f"{record['endereco']}, {record['numero']}"
            log_message(f"📍 Preenchendo endereço: {endereco}")
            time.sleep(1)
            
            log_message(f"👤 Preenchendo proprietário: {record['proprietario']}")
            time.sleep(0.5)
            
            if record.get('email'):
                log_message(f"📧 Preenchendo email: {record['email']}")
                time.sleep(0.5)
            
            # Simular submissão
            log_message("📤 Enviando formulário...")
            time.sleep(1)
            
            # 90% chance de sucesso
            if random.random() < 0.90:
                log_message(f"✅ Cadastro realizado com sucesso: {record['proprietario']}")
                automation_status['success_count'] += 1
            else:
                log_message(f"❌ Erro ao submeter formulário: {record['proprietario']}")
                automation_status['error_count'] += 1
            
            # Pausa entre registros
            time.sleep(1)
        
        log_message(f"🏁 Automação finalizada!")
        log_message(f"📊 Resultados: ✅ {automation_status['success_count']} sucessos | ❌ {automation_status['error_count']} erros")
        log_message("💼 Sistema pronto para nova automação!")
        
    except Exception as e:
        log_message(f"❌ Erro na automação: {str(e)}")
    finally:
        automation_status['running'] = False

def run_automation(file_path):
    """Executa a automação (versão demo)"""
    global automation_status

    try:
        automation_status['running'] = True
        automation_status['current_record'] = 0
        automation_status['success_count'] = 0
        automation_status['error_count'] = 0
        automation_status['logs'] = []

        # Processar dados do Excel
        data_list = process_excel_data(file_path)
        automation_status['total_records'] = len(data_list)

        if not data_list:
            log_message("❌ Nenhum dado válido encontrado no arquivo Excel")
            return

        log_message(f"📊 {len(data_list)} registros encontrados para processamento")
        
        # Simular automação
        simulate_automation(data_list)

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
    return jsonify(automation_status)

@app.route('/stop')
def stop_automation():
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
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'running': automation_status['running'],
        'mode': 'demo'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port,
        threaded=True
    )
