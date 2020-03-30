from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os.path
import tkinter
from tkinter import messagebox
import sqlite3
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert

# xpath constants
USER_SEARCH_XPATH="/html/body/div[1]/div/div/div[3]/div/div[1]/div/label/div/div[2]"
MESSAGE_BUBBLE_XPATH="/html/body/div/div/div/div[4]/div/footer/div[1]/div[2]/div/div[2]"
HEADER_BAR_XPATH="/html/body/div[1]/div/div/div[3]/div/header"
SPAN_CHAT_NAMES_XPATH="/html/body/div[1]/div/div/div[3]/div/div[2]/div[1]/div/div/div[*]/div/div/div[2]/div[1]/div[1]/span/span"
# SPAN_UNREAD_MESSAGES_TAG don't tested if someone is muted (maybe change xpath of unread tag)!!!
SPAN_UNREAD_MESSAGES_TAG="/html/body/div[1]/div/div/div[3]/div/div[2]/div[1]/div/div/div[*]/div/div/div[2]/div[2]/div[2]/span[1]/div/span"

# join bot path with db path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "../portal/db.sqlite3")


class BotConfig(object):
    chrome_options = None
    driver = None
    timeout = 10
    contacts = []

    def __init__(self, wait=60, session=None):
        self.chrome_options = Options()
        if session:
            self.chrome_options.add_argument(
                "--user-data-dir={}".format(session))

        try:
            self.driver = webdriver.Chrome("../chromedriver",
                                           options=self.chrome_options)
            self.driver.get('https://web.whatsapp.com')
            WebDriverWait(self.driver, wait).until(EC.presence_of_element_located(
                (By.XPATH, HEADER_BAR_XPATH)))
        except (NoSuchElementException, TimeoutException) as e:
            messagebox.showerror("Impossível conectar com o Dispositivo", u"Não foi possível conectar com o dispositivo, verifique se o dispositivo está ligado e possuí conexão à internet")

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
        print("ENTROU SEND_MESSAGE------------ message: ", message)
        if message is None:
            return
        # send_msg = self.driver.find_elements_by_xpath(MESSAGE_BUBBLE_XPATH)
        send_msg = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH, MESSAGE_BUBBLE_XPATH)))
        messages = message.split("\n")
        for msg in messages:
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
                    self.bot_options(action=last_message)
                    # need to refresh otherwise pin dont appears
            time.sleep(1)
            # self.poll_chat()

    def bot_options(self, action):
        conn = None
        simple_menu = {                          # function requires no extra arguments
            "ajuda": self._help_commands,
            "cadastrar": self.register_client
        }
        simple_menu_keys = simple_menu.keys()
        try:
            command_args = action.split(" ", 1)
            print("Command args: {cmd}".format(cmd=command_args))

            if len(command_args) == 1 and command_args[0] in simple_menu_keys:
                self.config.send_message(simple_menu[command_args[0]]())
            elif command_args[0] == 'produto':
                print('entrou produto')
                # product_name = (command_args[1], )
                with sqlite3.connect(db_path) as conn:
                    # where name contain some part of string in command_args[1]
                    cursor = conn.cursor()
                    _products = conn.execute(
                        "SELECT name, price FROM products_product WHERE INSTR(name, ?) > 0 AND quantity > 0", (command_args[1], ))
                    products = _products.fetchall()
                    if products:
                        message = "".join(
                            u"{name} - R${price}\n".format(name=product[0], price=product[1]) for product in products)
                        self.config.send_message(message)
                    else:
                        self.config.send_message(u"Produto indisponível")

            else:
                self.config.send_message(
                    u'Comando Inválido, digite "ajuda" para ver as opções disponíveis')
                #raise KeyError()

        except KeyError as e:  # mandar mensagem de ajuda
            print("Key Error Exception: {err}".format(err=str(e)))
            self.config.send_message(
                u'Comando Inválido, digite "ajuda" para ver as opções disponíveis')

        finally:
            if conn:
                conn.close()
            time.sleep(0.5)
            self.config.goto_main()

    def register_client(self):
        self.config.send_message("Funcionalidade em desenvolvimento!")

    def _help_commands(self):
        print("Asking for help")
        return u"Lista de comandos dísponiveis:\nAjuda: Lista de comandos disponíveis;\nCadastrar: Cadastra seu número para receber novas promoções da loja;\nProduto [nome do produto]: Lista todos as marcas desses produtos em estoque e seus respectivos preços."


def botRun():
    botConfig = None
    try:
        botConfig = BotConfig(session="whatsapp_session")
        Bot(botConfig)
    except WebDriverException as e:
        print(e)
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showwarning("Janela fechada",u"Por favor, abra novamente o aplicativo e não feche a aba!")
        root.destroy()
    finally:
        print('entrou block finally main')
        if botConfig:
            botConfig.close_driver()

def portalRun():
    print('rodar portal')

if __name__ == "__main__":
    # botRun()
    root = tkinter.Tk() 
    root.title('Menu Bot') 
    tkinter.Button(root, text='Rodar Whatsapp Bot', width=25, command=lambda: (root.destroy(), botRun())).pack()
    tkinter.Button(root, text='Adicionar/Modificar produtos', width=25, command=lambda: (root.destroy(), botRun())).pack()
    root.mainloop()