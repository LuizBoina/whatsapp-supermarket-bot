import csv
import os.path
import tkinter
from tkinter import messagebox
from tkinter import filedialog
import sqlite3
from bot import BotConfig, Bot, showMessage

########################################    HANDLE BOT    ########################################

def handleBot():
    botConfig = None
    try:
        botConfig = BotConfig(session="whatsapp_session")
        Bot(botConfig)
    except WebDriverException as e:
        showMessage("warning", "Janela fechada",u"Por favor, abra novamente o aplicativo e não feche a aba!")
    finally:
        print('entrou block finally main')
        if botConfig:
            botConfig.close_driver()

########################################    HANDLE DB    ########################################

def handleDB():
    root = tkinter.Tk() 
    root.withdraw()
    root.title('Importar planilha')
    file = filedialog.askopenfile(initialdir =  "/home/boina", parent=root,mode='rb',title='Selecionar a planilha de produtos'
        , filetypes = (("CSV Files","*.csv"), ("Excel files", "*.xlsx *.xls")))
    if file:
        with open(file.name, newline='') as products_path:
            db_path = "products.db"
            products = csv.DictReader(products_path, delimiter=';')
            to_db = [(prod["name"], prod["price"], prod["quantity"]) for prod in products]
            if not os.path.exists(db_path):
                os.mknod(db_path)
            sql_create_products_table = """ CREATE TABLE IF NOT EXISTS products (
                                    name TEXT NOT NULL,
                                    code INTEGER PRIMARY KEY,
                                    price FLOAT,
                                    quantity INTEGER
                                ); """
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(sql_create_products_table)
            cur.executemany("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?);", to_db)
            con.commit()
            con.close()
        messagebox.showinfo("Operação finalizada com sucesso",
                                u"Agora basta rodar o bot")
        root.destroy()

    else:
        root.withdraw()
        messagebox.showwarning("Arquivo não selecionado",
                                u"Por favor, abra novamente o aplicativo e selecione um arquivo válido para adicionar produtos!")
        root.destroy()
    root.mainloop()

########################################    MAIN    ##############################################

if __name__ == "__main__":
    root = tkinter.Tk() 
    root.title('Menu Bot') 
    tkinter.Button(root, text='Rodar Whatsapp Bot', width=25, command=lambda: (root.destroy(), handleBot())).pack()
    tkinter.Button(root, text='Adicionar/Modificar produtos', width=25, command=lambda: (root.destroy(), handleDB())).pack()
    root.mainloop()