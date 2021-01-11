from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os.path
import tkinter
from tkinter import messagebox
from tkinter import filedialog
import sqlite3
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
import urllib.request

# xpath constants
USER_SEARCH_XPATH="/html/body/div[1]/div/div/div[3]/div/div[1]/div/label/div/div[2]"
MESSAGE_BUBBLE_XPATH="/html/body/div/div/div/div[4]/div/footer/div[1]/div[2]/div/div[2]"
HEADER_BAR_XPATH="/html/body/div[1]/div/div/div[3]/div/header"
SPAN_CHAT_NAMES_XPATH="/html/body/div[1]/div/div/div[3]/div/div[2]/div[1]/div/div/div[*]/div/div/div[2]/div[1]/div[1]/span/span"
# SPAN_UNREAD_MESSAGES_TAG don't tested if someone is muted (maybe change xpath of unread tag)!!!
SPAN_UNREAD_MESSAGES_TAG="/html/body/div[1]/div/div/div[3]/div/div[2]/div[1]/div/div/div[*]/div/div/div[2]/div[2]/div[2]/span[1]/div/span"

# join bot path with db path
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# db_path = os.path.join(BASE_DIR, "db.sqlite3")

def showMessage(kind, title, message):
    root = tkinter.Tk()
    root.withdraw()
    if kind == "info":
        messagebox.showinfo(title, message)
    elif kind == "warning":
        messagebox.showwarning(title, message)
    else:
        messagebox.showerror(title, message)
    root.destroy()

class BotConfig(object):
    chrome_options = None
    driver = None
    timeout = 10
    contacts = []

    def __init__(self, wait=60, session=None):
        chromedriver_path="/home/luizboina/Projects/whatsapp-supermarket-bot/chromedriver"
        self.chrome_options = Options()
        # self.chrome_options.add_argument("--no-sandbox") 
        # self.chrome_options.add_argument("--disable-dev-shm-using") 
        # self.chrome_options.add_argument("--headless") 
        if session:
            self.chrome_options.add_argument(
                "--user-data-dir={}".format(session))

        try:
            self.driver = webdriver.Chrome(executable_path=chromedriver_path,
                                           options=self.chrome_options)
            self.driver.get('https://web.whatsapp.com')
            WebDriverWait(self.driver, wait).until(EC.presence_of_element_located(
                (By.XPATH, HEADER_BAR_XPATH)))
        except (NoSuchElementException, TimeoutException) as e:
            title="Impossível conectar com o Dispositivo"
            message=u"Não foi possível conectar com o dispositivo, verifique se o dispositivo está ligado e possuí conexão à internet"
            showMessage("error", title, message)
        except (WebDriverException) as e:
            title="Impossível abrir navegador"
            message=u"Não foi possível conectar com o dispositivo, verifique se o chrome esta instalado na mesma versão que o chromedriver"
            showMessage("error", title, message)


# return list of contact
    def get_contacts(self):
        return self.contacts

# return to main to unselect chat used to prevent bot don't reply
    def goto_main(self):
        try:
            self.driver.refresh()
            Alert(self.driver).accept()
        except Exception as e:
            print(e)
        WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH, HEADER_BAR_XPATH)))

    # Getting usernames which has unread messages
    def unread_usernames(self, scrolls=100):
        # self.goto_main()
        initial = 10
        usernames = []
        for i in range(0, scrolls):
            self.driver.execute_script(
                "document.getElementById('pane-side').scrollTop={}".format(initial))
            for unread_tag in self.driver.find_elements_by_xpath(SPAN_UNREAD_MESSAGES_TAG):
                #get username
                name = unread_tag.find_element_by_xpath('./../../../../../div[1]/div/span/span').get_attribute('innerHTML')
                usernames.append(name)
            initial += 10
        # Remove duplicates
        usernames = list(set(usernames))
        print(usernames)
        return usernames

    def send_message(self, message):
        if message is None:
            return
        # send_msg = self.driver.find_elements_by_xpath(MESSAGE_BUBBLE_XPATH)
        send_msg = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH, MESSAGE_BUBBLE_XPATH)))
        messages = message.split("\n")
        for msg in messages:
            print(msg,'\n')
            send_msg.send_keys(msg)
            send_msg.send_keys(Keys.SHIFT+Keys.ENTER)
        send_msg.send_keys(Keys.ENTER)

    def get_unread_last_message(self, name):
        # opening chat
        search = self.driver.find_element_by_xpath(USER_SEARCH_XPATH)
        search.send_keys(name+Keys.ENTER)
        time.sleep(0.5)

        # get unread messages
        text_bubbles = self.driver.find_elements_by_class_name(
            "message-in")  # message-in = receiver, message-out = sender
        tmp_queue = []
        try:
            for bubble in text_bubbles:
                msg_texts = bubble.find_elements_by_class_name("copyable-text")
                for msg in msg_texts:
                    tmp_queue.append(msg.text.lower())

            if len(tmp_queue) > 0:
                return tmp_queue[-1]  # Send last message in list

        except StaleElementReferenceException as e:
            print(str(e))
            # Something went wrong, either keep polling until it comes back or figure out alternative
        return False

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    # Get all the contacts
    # def whatsapp_contacts():
    #     contacts = driver.find_elements_by_class_name("chat-title")

    #     return [contact.text for contact in contacts]


class Bot(object):
    def __init__(self, botConfig):
        self.config = botConfig
        self.init_bot()

    def init_bot(self):
        # bot stay in loop
        while True:
            # get all clients that have unread messages
            unread_clients_name = self.config.unread_usernames()
            # for each client in "unread_clients_name" the bot will read the last message and do some logic stuff
            if unread_clients_name:
                for client_name in unread_clients_name:
                    last_message = self.config.get_unread_last_message(
                        client_name)
                    self.bot_action(action=last_message)
                    # need to refresh otherwise pin dont appears
            time.sleep(1)
            # self.poll_chat()

    def bot_action(self, action):
        conn = None
        simple_menu = {                          # function requires no extra arguments
            "ajuda": self._help_commands,
            "filiais": self.send_shops,
            "cadastrar": self.register_client,
            "decadastrar": self.unregister_client,
        }
        simple_menu_keys = simple_menu.keys()
        try:
            command_args = action.split(" ")
            print("Command args: {cmd}".format(cmd=command_args))

            if len(command_args) == 1 and command_args[0] in simple_menu_keys:
                self.config.send_message(simple_menu[command_args[0]]())
            elif command_args[0] == 'produto':
                print('entrou produto')
                with sqlite3.connect('products.db') as conn:
                    # where name contain some part of string in command_args[1]
                    cursor = conn.cursor()
                    _products = conn.execute(
                        "SELECT name, price FROM products WHERE name LIKE {} AND quantity > 0;".format("'"+command_args[1].upper()+"%'"))
                    products = _products.fetchall()
                    if products:
                        header = "Consulta na filial Casagrande Hiper - Araçá\n"
                        message = "".join(
                            u"{name} - *R${price}*\n".format(name=product[0], price=product[1]) for product in products)
                        self.config.send_message(message)
                        message = header + message
                    else:
                        self.config.send_message(u"Produto indisponível")
            elif command_args[0] == 'loja':
                print('entrou loja')
                self.config.send_message(u"Loja selecionada com sucesso!")

            else:
                self.config.send_message(self._help_commands())
                #raise KeyError()

        except KeyError as e:  # mandar mensagem de ajuda
            print("Key Error Exception: {err}".format(err=str(e)))
            self.config.send_message(self._help_commands())
        except sqlite3.OperationalError as e:
            showMessage("error", "Erro ao recuperar dados", u"Por favor, verifique se o arquivo 'products.db' foi criado e esta atualizado")

        finally:
            if conn:
                conn.close()
            time.sleep(0.5)
            self.config.goto_main()

    def register_client(self):
        self.config.send_message("Número cadastrado com sucesso! Você irá receber promoções de nossas filiais todos os dias")

    def unregister_client(self):
        self.config.send_message("Cadastrado cancelado com sucesso! Você não irá receber mais promoções de nossas filiais")

    def send_shops(self):
        self.config.send_message("Lista de nossas filiais:\n" \
                                    "1 - Casagrande Hiper - Araçá\n" \
                                    "2 - Casagrande - Interlagos\n" \
                                    "3 - Casagrande - BNH\n" \
                                    "4 - Casagrande - Aviso\n" \
                                    "5 - Casagrande - Centro"
        )

    def _help_commands(self):
        print("Asking for help")
        return u"Bem Vindo ao chatbot do Casagrande! Siga as instruções abaixo para obter o que deseja.\n" \
                   "Lista de comandos dísponiveis:\n" \
                   "*Ajuda*: Lista de comandos disponíveis;\n" \
                   "*Filiais*: Lista as filiais disponíveis na região;\n" \
                   "*Cadastrar*: Cadastra seu número para receber novas promoções das filiais;\n" \
                   "*Cancelar*: Cancela o recebimento de novas promoções das filiais;\n" \
                   "*Produto* _[nome do produto]_ _[número da filial]_: Lista todos os produtos em estoque e seus respectivos preços da filial selecionada."