import os
import shutil
from datetime import datetime 
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import json
import re


class backup:
    def start_backup(self):        
        # Lendo json com dados        
        arquivo_json = '.\Automacao_Backup_local\dados.json'
        self.ler_json(arquivo_json)
        
        pasta_logs = self.local_logs
        
        self.logger = self.configurar_logger(pasta_logs)
        # Copia os arquivos
        self.deletar_arquivos(self.local_destino)
        
        self.copiar_arquivos()
        
        log_arquivo = self.caminho_log
        self.success
        
        if self.success == 'S':            
            assunto = "Sucesso ao realizar backup!"
            mensagem = f'Backup realizado. \nSeguem os logs em anexo.'
        else:
            assunto = "Erro ao realizar backup!"
            mensagem = f'Backup falhou. \nSeguem os logs em anexo.'  
        
        status_envio, mensagem_log = self.enviar_email(assunto, mensagem, log_arquivo)
        
        if status_envio == True:
            self.registrar_log(self.logger, f'E-mail enviado com sucesso! Retorno: {mensagem_log}', 'info') 
        else:
            self.registrar_log(self.logger, f'Erro ao enviar e-mail! Retorno: {mensagem_log}', 'error') 
        
    
    def ler_json(self, caminho_json):
        with open(caminho_json, 'r') as f:
            dados = json.load(f)
        
        # e-mails
        inform_email = dados["dados_email"]
        self.remetente = inform_email["remetente"]
        self.senha = inform_email["senha"]
        self.destinatario = inform_email["destinatario"]
        
        # arquivos
        local_arquivos = dados["caminho_arquivos"]
        self.local_logs = local_arquivos["logs"]
        self.local_origem = local_arquivos["origem"]
        self.local_destino = local_arquivos["destino"]
        
        return self.remetente, self.senha, self.destinatario, self.local_logs, self.local_origem, self.local_destino
        
    
    # Configuraçao do log
    def configurar_logger(self, pasta_logs):
        # Verifica se a pasta de logs existe, caso contrário, cria
        if not os.path.exists(pasta_logs):
            os.makedirs(pasta_logs)

        data_atual = datetime.now().strftime('%d%m%Y')
        nome_arquivo_log = f'log_{data_atual}.txt'
        
        # Configura o caminho completo para o arquivo de log
        self.caminho_log = os.path.join(pasta_logs, nome_arquivo_log)
        
        # Configuraçao do logger
        logger = logging.getLogger('meu_logger')
        logger.setLevel(logging.DEBUG)
        
        # Configuraçao do handler para gravar logs em um arquivo
        handler = logging.FileHandler(self.caminho_log)
        handler.setLevel(logging.DEBUG)
        
        # Formato dos logs
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Adiciona o handler ao logger
        logger.addHandler(handler)
        
        return logger
    

    def registrar_log(self, logger, mensagem, nivel='info'):
        if nivel == 'debug':
            self.logger.debug(mensagem)
        elif nivel == 'info':
            self.logger.info(mensagem)
        elif nivel == 'warning':
            self.logger.warning(mensagem)
        elif nivel == 'error':
            self.logger.error(mensagem)
        elif nivel == 'critical':
            self.logger.critical(mensagem)
        else:
            self.logger.info(mensagem)
            
            
    # Copia os arquivos
    def copiar_arquivos(self):
        # Verifica se o diretório de destino existe, caso contrário, cria
        origem = self.local_origem
        destino = self.local_destino
        self.success = 'N'
        
        if not os.path.exists(destino):            
            try:
                os.makedirs(destino, exist_ok=True)
                self.registrar_log(self.logger, f'Pasta nao encontrada, criando pasta em: {destino}', 'warning')
            except OSError as e:   
                self.registrar_log(self.logger, f'Pasta de destino nao foi informada!', 'error') 
                return self.success             
                
        if os.path.exists(origem):
            try:   
                # Lista todos os arquivos no diretório de origem
                arquivos = os.listdir(origem)
                
                if not arquivos:
                    self.registrar_log(self.logger, f'Nao existem arquivos para backup', 'warning') 
                    return self.success  
                                
                for arquivo in os.listdir(origem):            
                    data_backup = datetime.now().strftime('%d%m%Y_%H%M%S')           
                                
                    caminho_completo_origem = os.path.join(origem, arquivo)      
                    
                    self.registrar_log(self.logger, f'Origem do arquivo: {caminho_completo_origem}', 'info')
                    
                    # Pegar o nome do arquivo e extensao        
                    nome_arquivo_origem = os.path.basename(caminho_completo_origem)
                    nome_arquivo, extensao = os.path.splitext(nome_arquivo_origem)
                    
                    self.registrar_log(self.logger, f'Dados do arquivo - Nome: {nome_arquivo}, Extensao: {extensao}', 'info')
                    
                    # Gera o nome do arquivo de destino
                    nome_arquivo = f'{nome_arquivo}_{data_backup}{extensao}'                  
                    caminho_completo_destino = os.path.join(destino, nome_arquivo) 
                    
                    self.registrar_log(self.logger, f'Destino do backup: {caminho_completo_destino}', 'info')
                    
                    # Copia apenas arquivos, ignora subdiretórios
                    if os.path.isfile(caminho_completo_origem):                
                        try:
                            shutil.copy2(caminho_completo_origem, caminho_completo_destino)
                            self.registrar_log(self.logger, f'Arquivo copiado de "{origem}" para "{destino}" com sucesso.', 'info')
                            self.success = 'S'  
                        except IOError as e:
                            self.registrar_log(self.logger, f'Erro ao copiar arquivo: {e}', 'error') 
                
            except OSError as e:    
                self.registrar_log(self.logger, f'Pasta de destino nao foi informada! Erro: {e}', 'error')
                return self.success  
        else:
            self.registrar_log(self.logger, f'Pasta de origem nao foi informada!', 'error')            
                                                   
        return self.success                
                

    def deletar_arquivos(self, destino):
        # Verifica se a pasta existe
        if not os.path.exists(destino):
            self.registrar_log(self.logger, f'A pasta {destino} nao existe.', 'warning')
            return
        
        # Lista todos os arquivos na pasta
        arquivos = os.listdir(destino)
        
        # Itera sobre os arquivos e os deleta
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(destino, arquivo)
            try:
                # Deleta apenas arquivos, nao subpastas
                if os.path.isfile(caminho_arquivo):
                    os.remove(caminho_arquivo)
                    self.registrar_log(self.logger, f'Arquivo {caminho_arquivo} deletado com sucesso.', 'info')
                else:
                    self.registrar_log(self.logger, f'{caminho_arquivo} nao é um arquivo.', 'info')
            except Exception as e:
                self.registrar_log(self.logger, f'Erro ao deletar {caminho_arquivo}: {e}', 'error') 
                 
    
    def enviar_email(self, assunto, mensagem, caminho_arquivo_anexo):
        try: 
            remetente = self.remetente
            senha_app = self.senha  # Gerada no Google Console
            destinatario = self.destinatario  
                               
            # Criar mensagem MIME
            msg = MIMEMultipart()

            # Definir cabeçalhos de email
            msg['From'] = remetente
            msg['To'] = destinatario
            msg['Subject'] = assunto

            # Converter mensagem para formato texto
            corpo_texto = MIMEText(mensagem)

            # Adicionar corpo da mensagem à mensagem MIME
            msg.attach(corpo_texto)
            
            # Anexar arquivo txt
            with open(caminho_arquivo_anexo, 'rb') as f:
                anexo = MIMEBase('application', 'octet-stream')
                anexo.set_payload(f.read())
                anexo.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(caminho_arquivo_anexo)))
                msg.attach(anexo)
                self.registrar_log(self.logger, f'Anexando arquivo de logs {caminho_arquivo_anexo}', 'info')
                
                
            # Criar conexao com servidor SMTP do Gmail
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                # Habilitar TLS para segurança
                server.starttls()

                # Fazer login no Gmail
                server.login(remetente, senha_app)

                # Enviar email
                server.sendmail(remetente, destinatario, msg.as_string())
                self.registrar_log(self.logger, f'Enviando e-mail de: {remetente} para: {destinatario}.', 'info')
                                 
                
            # Email enviado com sucesso
            return True, "Email enviado com sucesso!"     
        except (KeyError, FileNotFoundError, smtplib.SMTPException) as e:
            # Erro ao carregar credenciais, arquivo nao encontrado ou erro ao enviar email
            erro_mensagem = f"Erro ao enviar email: {e}"
            return False, erro_mensagem
        

# Executa o programa
start = backup()
start.start_backup()
