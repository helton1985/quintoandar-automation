def setup_driver(self):
    """Configura o driver do Chrome para Heroku"""
    try:
        log_message("🔧 Configurando navegador Chrome para Heroku...")
        
        # Configurações do Chrome para Heroku
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        # Caminhos específicos do Heroku
        chrome_bin = os.environ.get('GOOGLE_CHROME_BIN', '/app/.apt/usr/bin/google-chrome')
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/app/.chromedriver/bin/chromedriver')
        
        # Configurar binário do Chrome
        chrome_options.binary_location = chrome_bin
        
        # Verificar se Chrome existe
        if not os.path.exists(chrome_bin):
            log_message(f"❌ Chrome não encontrado em: {chrome_bin}")
            # Tentar caminhos alternativos
            alternative_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/opt/google/chrome/google-chrome'
            ]
            
            for path in alternative_paths:
                if os.path.exists(path):
                    chrome_options.binary_location = path
                    log_message(f"✅ Chrome encontrado em: {path}")
                    break
            else:
                log_message("❌ Chrome não encontrado em nenhum caminho")
                return False
        
        # Configurar service do ChromeDriver
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            log_message(f"✅ ChromeDriver encontrado em: {chromedriver_path}")
        else:
            # Usar webdriver-manager como fallback
            service = Service(ChromeDriverManager().install())
            log_message("✅ ChromeDriver instalado via webdriver-manager")
        
        # Criar driver
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        log_message("✅ Chrome WebDriver configurado com sucesso!")
        return True
        
    except Exception as e:
        log_message(f"❌ Erro ao configurar Chrome: {str(e)}")
        log_message(f"❌ Detalhes: {type(e).__name__}")
        return False
