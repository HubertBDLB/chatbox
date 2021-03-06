# coding: utf-8
# ChatBox v3.6
# Dernière modification : 22/05/2022


# A FAIRE :
#   - Changer pseudo si déjà pris (Actuellement refuse la connection)
#   - R.S.A. (tout dépend d'Antonin)


#------------------------------------------------------------------------------------
#                                      BIBLIOTHEQUES
#------------------------------------------------------------------------------------


#_______________________________________________________________________
# Bibliothèque                              | Utilisation               |
#___________________________________________|___________________________|
import sys                                  # Quitter app & Chemins     |
import os                                   # Chemins & Commandes       |
import timeit                               # Calcul temps réponse      |
import socket                               # Lien Client - Serveur     |
import threading                            # Séparation des tâches     |
import tkinter                              # Interface                 |
import requests                             # Mises à jour              |
import webbrowser                           # Mode d'emploi             |
from platform import system                 #                           |
from subprocess import check_call           #                           |
from tkinter import simpledialog,scrolledtext,messagebox                #
#___________________________________________|___________________________|


#------------------------------------------------------------------------------------
#                                      CONSTANTES
#------------------------------------------------------------------------------------


WEBSITE_PATH = "https://hubertbdlb.github.io/chatbox/"

GITHUB_PATH = "https://raw.githubusercontent.com/HubertBDLB/ChatBox/main/"

README_PATH = "https://github.com/HubertBDLB/ChatBox/blob/main/README.md"

RAW_README_PATH = GITHUB_PATH + "README.md"

IMAGES_PATH = "images/"

VERSION = "ChatBox v3.7"

NEW_LINE_CHAR = """
"""

INVITE_MESSAGE = f"Installe {VERSION} depuis {README_PATH}"

HELP_MESSAGE = """Liste des commandes :
/help                       : Affiche ce message
/help2                      : Affiche le message d'aide concernant la syntaxe
/kick <nom>                 : Exclu un client
/ban <nom>                  : Banni un client
/blacklist                  : Affiche la liste des adresse bannies
/broadcast | /br <message>  : Envoie un message à tous les clients
/msg <nom> <message>        : Envoie un message à un client donné
/list                       : Affiche la liste des clients connectés
/stop                       : Eteint le serveur (demande confirmation)
/ip                         : Affiche l'ip et le port du serveur
/invite                     : Copie un message d'invitation dans le presse-papier
"""

SYNTAX_HELP_MESSAGE = """Avec les commandes /broadcast | /br et /msg | /w :
Avant le message :
*   : Gras
_   : Souligné
-   : Italique
[   : Gras et bleu
!   : Gros (16 -> 32)
/!\ : Gros et rouge
&   : Rouge
"""

MONO_FONT = ("Courier New",20)
BASE_FONT = "Helvetica"
DEFAULT_FONT = (BASE_FONT,16)
BOLD_FONT = (BASE_FONT,16,"bold")
BIG_FONT = (BASE_FONT,32,"bold")
UNDERLINED_FONT = (BASE_FONT,16,"underline")
ITALIC_FONT = (BASE_FONT,16,"italic")

TOP = "top"
BOTTOM = "bottom"
LEFT = "left"
RIGHT = "right"
X = "x"
Y = "y"
BOTH = "both"
DISABLED = "disabled"
ENABLED = "normal"
END = "end"

RED = "#ff0000"
DARK_BLUE = "#004080"
DARKER_BLUE = "#003070"
INVERTED_DARK_BLUE = "#FFBF7F"
WHITE = "#ffffff"
LIGHT_GRAY = "#dddddd"
GRAY = "#888888"
DARK_GRAY = "#222222"
BLACK = "#000000"
PALE_YELLOW = "#e0e090"


#------------------------------------------------------------------------------------
#                                      FONCTIONS
#------------------------------------------------------------------------------------


def update():
    """ Créé un bouton renvoyant vers le lien de mise à jour si disponible"""
    update_label.config(text="Vérification des mises à jour...")
    win.update()
    try: 
        version_request = requests.get(RAW_README_PATH)
    except:
        update_label.config(text="Impossible de vérifier les mises à jour")

    LAST_VERSION = version_request.content.decode("utf-8").split(NEW_LINE_CHAR)[0]

    if  LAST_VERSION != VERSION:
        update_label.destroy()
        update_button = tkinter.Button(win,text="Installer la dernière version\n(reccomandé)",padx=10,pady=10,bg=DARK_BLUE,fg=WHITE,font=DEFAULT_FONT,command=lambda: webbrowser.open_new_tab(WEBSITE_PATH))
        update_button.pack(fill=BOTH)
    else:
        update_label.config(text="Application à jour")


def copy_to_clipboard(text: str) -> str:
    """ Copie du texte dans le presse-papier """
    if system() == "Darwin": cmd='echo '+text.strip()+'|pbcopy'
    elif system() == "Windows":cmd='echo '+text.strip()+'|clip'
    return check_call(cmd, shell=True)


def resource_path(relative_path: str) -> str:
    """ Récupère le chemin absolu d'un chemin relatif d'une ressource """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def start_server():
    """ Démarre une instance de la classe SERVER """
    win.destroy()
    SERVER()


def start_client():
    """ Démarre une instance de la classe CLIENT """
    win.destroy()
    CLIENT()


ICON_PATH = resource_path(IMAGES_PATH + "icon_256.ico")
LOGO_PATH = resource_path(IMAGES_PATH + "logo_192_64.png")


#------------------------------------------------------------------------------------
#                                       SERVEUR
#------------------------------------------------------------------------------------


class SERVER:
    def __init__(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.host = s.getsockname()[0]
        s.close()
        self.port = 9090
        self.gui_done = False
        self.running = True

        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('',self.port))
        except: # Si serveur déjà existant : fermer l'application
            self.stop(force=True)

        gui_thread = threading.Thread(target=self.gui_loop)
        gui_thread.start()

        self.server.listen()
        self.blacklist = [] 
        self.clients = {} # dictionnaire socket : surnom 

        while not self.gui_done:
            pass
        if self.gui_done:
            self.log(f"Le serveur {self.host}:{self.port} est en ligne\n")
            self.log(HELP_MESSAGE,"command_result")
            self.receive()


    def gui_loop(self):
        """ Construit l'interface """
        self.win = tkinter.Tk()
        self.win.configure(bg=DARK_BLUE)
        self.win.title(VERSION + " - Hôte")
        self.win.wm_iconbitmap(ICON_PATH)
        self.logo = tkinter.PhotoImage(file=LOGO_PATH)
        self.win.bind("<Control_L><Return>", self.execute) # Ctrl+Entrée envoie le message

        # Importance relative des lignes et colonnes
        self.win.grid_rowconfigure(1,weight=1)
        self.win.grid_columnconfigure(0,weight=1)
        self.win.grid_columnconfigure(1,weight=0)

        # Widgets
        self.text_area = scrolledtext.ScrolledText(self.win,font = MONO_FONT)
        self.input_area = tkinter.Text(self.win,height=3)
        self.send_button = tkinter.Button(self.win,height=3,text="Envoyer",command=self.execute,width=15)
        
        # Affichage des widgets
        tkinter.Label(self.win,image=self.logo,bg=DARK_BLUE).grid(column=0,row=0,columnspan=2)
        self.text_area.grid(column=0,row=1,columnspan=2,sticky="nesw")    
        self.input_area.grid(column=0,row=2,sticky="nesw")                
        self.send_button.grid(column=1,row=2,sticky="nesw")               

        self.text_area.config(state="disabled")
        self.win.protocol('WM_DELETE_WINDOW',self.stop)

        self.gui_done = True
        self.win.mainloop()


    # Commandes
    

    def execute(self,event = None):
        """ Détecte et execute les commandes """
        message = self.input_area.get('1.0','end')

        # Si une commande
        if message.startswith("/"):
            self.log(message,"command")
            command = message.split()[0][1:]
            parameter = message[(len(command)+2):]
            
            if command in ["help"]:
                try: self.log(HELP_MESSAGE,"command_result")
                except Exception as e: self.log(f"ERREUR : {e}\n","error")

            elif command in ["help2"]:
                try: self.log(SYNTAX_HELP_MESSAGE,"command_result")
                except Exception as e: self.log(f"ERREUR : {e}\n","error")

            elif command in ["kick"]:
                try: self.kick(parameter.replace(NEW_LINE_CHAR,''))
                except Exception as e: self.log(f"ERREUR : {e}\n","error")
                    
            elif command in ["broadcast","br"]:
                try: self.broadcast(parameter)
                except Exception as e: self.log(e,"error")
                
            elif command in ["stop"]:
                try: self.stop()
                except Exception as e: self.log(e,"error")

            elif command in ["list"]:
                try: self.log_online_members()
                except Exception as e: self.log(e,"error")

            elif command in ["ban"]:
                try: self.ban(parameter.split()[0])
                except Exception as e: self.log(e,"error")

            elif command in ["msg"]:
                try: self.msg(parameter.split()[0],parameter[len(parameter.split()[0])+1:])
                except Exception as e: self.log(e,"error")

            elif command in ["ip"]:
                try: self.log(f"{self.host}:{self.port}\n","command_result")
                except Exception as e: self.log(e,"error")

            elif command in ["blacklist"]:
                try: self.log_banned_clients()
                except Exception as e: self.log(e,"error")

            elif command in ["invite"]:
                try: 
                    self.log("L'invitation a été copiée dans le presse-papier\n","command_result")
                    copy_to_clipboard(INVITE_MESSAGE)
                except Exception as e: self.log(e,"error")

            else: # Commande inexistante
                self.log("Cette commande n'existe pas.\nAfficher la liste des commandes : /help\n","command_result")
        else:
            self.broadcast("&[ADMIN]\n" + message)


    def get_socket_from_name(self,name: str) -> socket.socket:
        """ Renvoie un socket a partir du nom du client associé """
        sockets_list = list(self.clients.keys())
        nicknames_list = list(self.clients.values())
        socket = sockets_list[nicknames_list.index(name)]
        return socket  


    def log(self,message: str,message_type: str = None):
        """ Affiche un message dans la zone de texte """
        self.text_area.config(state="normal")

        if message_type == None:
            self.text_area.insert('end', (message))

        else:
            self.text_area.insert('end', message,message_type)

            if message_type == "user_msg":
                self.text_area.tag_config("user_msg",background="#ddd")

            if message_type == "command":
                self.text_area.tag_config("command",foreground="#0a0")

            if message_type == "command_result":
                self.text_area.tag_config("command_result",background = "#eee", foreground="#0a0")
          
            if message_type == "error":
                self.text_area.tag_config("error",foreground="#f00")

        self.text_area.config(state="disabled")
        self.input_area.delete('1.0','end')
        self.text_area.yview("end")
    

    def msg(self,name: str,message: str):
        try:
            self.get_socket_from_name(name).send(message.encode("utf-8"))
            self.log(f"Message envoyé\n","command_result")

        except ValueError:
            self.log(f"ERREUR : {name} n'est pas connecté\n","error")

        except IndexError:
            self.log(f"ERREUR : Syntaxe : /msg | /w <nom>\n","error")


    def get_online_members(self,names_only: bool = False):
        online_members = ""
        if self.clients == {}: 
            online_members = "Aucun client connecté\n"

        for client in self.clients:
            client_name = self.clients[client]
            member_address = client.getpeername()
            if names_only:
                online_members += f"{client_name}"
            else:
                online_members += f"{client_name} : {member_address[0]}:{member_address[1]}\n"
        return online_members


    def log_online_members(self,names_only:bool = False):
        """Affiche la liste des membres connectés"""
        self.log(self.get_online_members(names_only),"command_result")


    def log_banned_clients(self):
        if self.blacklist == []:
            self.log("La liste noire est vide\n","command_result")
        else: 
            self.log(str(self.blacklist) + '\n',"command_result")


    def ban(self,name: str):
        """Kick et refuse les tentatives de connection d'un client donné"""
        client = self.get_socket_from_name(name)
        banned_ip = client.getpeername()[0]

        self.broadcast(f"[{name} a été banni]\n")
        
        self.blacklist.append(banned_ip)
        client.close()
        
        # Ban des doubles comptes
        if self.clients != {}:
            for c in self.clients:
                if c.getpeername()[0] == banned_ip:
                    c.close()


    def kick(self,name: str):
        """Arrête le thread handle d'un client en particulier"""
        socket = self.get_socket_from_name(name)
        socket.send('[Vous avez été exclu]'.encode("utf-8"))
        self.log(f"{name} a été exclu\n","command_result")
        socket.close()


    def stop(self,force: bool = False):
        """Eteint le serveur en demandant confirmation"""
        if force:
            stop = True
        else:
            stop = messagebox.askokcancel("Quitter", "Voulez vous éteindre le serveur ?")

        if stop:
            try: self.broadcast("[Le serveur est fermé]\n")
            except: pass

            try: self.win.destroy()
            except: pass

            self.running = False
            self.server.close()
            sys.exit(1)


    # Communication


    def broadcast(self,message: str):
        """Envoie un message donné à tous les clients"""
        self.log(message,"user_msg")
        for client in self.clients:
            try:
                client.send(message.encode("utf-8"))
            except:
                self.log(f"ERREUR : Le message n’a pas pu être envoyé\n","error")


    def handle(self,client):
        """Reçoit et broadcast les messages que chaque client envoie"""
        while self.running:
            nom_client = self.clients[client]
            try:
                raw_message = client.recv(1024).decode('utf-8')
                message = f"{nom_client}\n{raw_message}"
                self.broadcast(message)

            except: # client deconnecté
                self.clients.pop(client)
                self.log(f"DEPART : {nom_client} est parti\n","error")
                self.broadcast(f"[{nom_client} est parti]\n")
                client.close()
                break


    def receive(self):
        """Accepte les tentatives de connection des clients"""
        while self.running:
            try:
                client, address = self.server.accept()
            except:
                self.stop(force=True)

            self.log(f"le client {address[0]}:{address[1]} a tenté de se connecter au serveur\n")

            client.send(("[asking_nickname]").encode("utf-8"))
            nickname = client.recv(1024).decode("utf-8")
            if address[0] not in self.blacklist:
                if nickname not in self.clients.values(): # Si ce nom n'est pas déjà pris
                    self.clients[client] = nickname

                    self.log(f"{address[0]}:{address[1]} a pour surnom : <{nickname}>\n")
                    self.broadcast(f"[{nickname} s’est connecté au serveur]\n")
                
                    thread = threading.Thread(target=self.handle, args=(client,))
                    thread.start()
                else:
                    client.send(("[nickname_already_taken]").encode("utf-8"))
            else:
                client.send(("[address_banned]").encode("utf-8"))


#------------------------------------------------------------------------------------
#                                      CLIENT
#------------------------------------------------------------------------------------


class CLIENT:
    def __init__(self):
        self.gui_done = False
        self.connected = False
        self.running =  True
        self.sock = None
        self.host = None
        self.port = 9090
        self.gui_loop()


    # Gestion de la fenêtre


    def gui_loop(self):
        # Paramètres de la fenêtre
        self.win = tkinter.Tk()
        self.win.configure(bg=DARK_BLUE)
        self.win.title(VERSION)
        self.win.wm_iconbitmap(ICON_PATH)
        self.win.resizable(False,False)
        self.create_nickname_choice_gui()

        self.win.protocol("WM_DELETE_WINDOW",self.stop)
        self.win.mainloop()


    def nickname_choice(self,event = None):
        self.nickname = ""
        self.nickname = self.nickname_entry.get()
        if self.is_nickname_valid(self.nickname):
            self.create_server_choice_gui()
        else:
            self.error_label.config(text="Le nom doit faire entre 3 et 16 caractères et ne\ncomporter que des caractères alphanumériques")


    def server_choice(self,event = None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = self.server_entry.get()

        start = timeit.default_timer()

        self.connect_thread = threading.Thread(target=self.connect)
        self.connect_thread.start()

        while timeit.default_timer()-start < 10 and not self.connected:
            pass
        if timeit.default_timer()-start >= 10 and not self.connected:
            self.error_label.config(text=f"{self.host}:{self.port} a mis trop de temps pour répondre")

        # Ouverture de la fenêtre principale
        if self.connected:
            self.create_texting_gui()
            self.gui_done = True 
            threading.Thread(target=self.receive).start()


    # Création des interfaces


    def create_nickname_choice_gui(self):
        self.logo = tkinter.PhotoImage(file=LOGO_PATH)
        self.nickname_frame = tkinter.Frame(self.win,bg=DARK_BLUE)
        self.nickname_label = tkinter.Label(self.nickname_frame,text = "Choisissez un nom",bg=DARK_BLUE,fg=WHITE,font=DEFAULT_FONT)
        self.nickname_entry = tkinter.Entry(self.nickname_frame,font=DEFAULT_FONT)
        self.confirm_button = tkinter.Button(self.nickname_frame,text="Continuer",bg=DARKER_BLUE,fg=WHITE,font=DEFAULT_FONT,command=self.nickname_choice)
        self.error_label = tkinter.Label(self.nickname_frame,bg=LIGHT_GRAY,fg=RED,font=DEFAULT_FONT)
        self.nickname_entry.bind("<Return>", self.nickname_choice)

        tkinter.Label(self.nickname_frame,image=self.logo,bg=DARK_BLUE).pack()
        self.nickname_frame.pack(expand=True,fill=BOTH)
        self.nickname_label.pack(fill=BOTH,padx=10,pady=10)
        self.nickname_entry.pack(fill=BOTH,padx=10,pady=10)
        self.error_label.pack(fill=BOTH,padx=10,pady=10)
        self.confirm_button.pack(fill=BOTH,padx=10,pady=10)


    def create_server_choice_gui(self): # TODO créer liste des serveurs favoris quand server un bouton a coté de server entry est cliqué
        self.nickname_frame.destroy()
        self.server_frame = tkinter.Frame(self.win,bg=DARK_BLUE)
        self.servers_list_frame = tkinter.Frame(self.server_frame)

        self.server_label = tkinter.Label(self.server_frame,text = "IP du serveur :",bg=DARK_BLUE,fg=WHITE,font=DEFAULT_FONT)
        self.server_entry = tkinter.Entry(self.server_frame,font=DEFAULT_FONT)
        self.servers_list_button = tkinter.Button(self.server_frame,text="▼",command=self.drop_servers_list)
        self.confirm_button = tkinter.Button(self.server_frame,text="Se connecter",bg=DARKER_BLUE,fg=WHITE,font=DEFAULT_FONT,command=self.server_choice)
        self.error_label = tkinter.Label(self.server_frame,bg=LIGHT_GRAY,fg=RED,font=DEFAULT_FONT)
        self.server_entry.bind("<Return>", self.server_choice)

    
        self.server_frame.pack(expand=True,fill=BOTH)
        self.server_label.pack(fill=BOTH,padx=10,pady=10)
        self.server_entry.pack(fill=Y,padx=10,pady=10)
        self.servers_list_button.pack(fill=Y,padx=10,pady=10)
        self.servers_list_frame.pack(expand=True,fill=BOTH)
        self.error_label.pack(fill=BOTH,padx=10,pady=10)
        self.confirm_button.pack(fill=BOTH,padx=10,pady=10)

    def create_texting_gui(self):
        self.server_frame.destroy() # Effacement du contenu de la fenêtre
        self.win.state('zoomed') # Plein écran
        self.win.resizable(True,True)
        self.win.bind("<Control_L><Return>", self.write) # Ctrl+Entrée envoie le message

        # Importance relative des lignes et colonnes
        self.win.grid_rowconfigure(1,weight=1)
        self.win.grid_columnconfigure(0,weight=1)
        self.win.grid_columnconfigure(1,weight=0)

        # Widgets
        self.text_area = scrolledtext.ScrolledText(self.win,font = DEFAULT_FONT)
        self.input_area = tkinter.Text(self.win,height=3)
        self.send_button = tkinter.Button(self.win,height=3,text="Envoyer",command=self.write)
        self.menu = tkinter.Menu(self.win)
        self.menu.add_command(label="Mode d'emploi", command=lambda: webbrowser.open(WEBSITE_PATH))
        if self.host not in self.get_servers(ip_only=True):
            self.menu.add_command(label= "Ajouter aux favoris ☆", command=self.register_server)
        else:
            self.menu.add_command(label= "Supprimer des favoris ★", command=self.unregister_server)

        self.win.config(menu=menu)
        
        # Affichage des widgets
        tkinter.Label(self.win,image=self.logo,bg=DARK_BLUE).grid(column=0,row=0,columnspan=2)
        self.text_area.grid(column=0,row=1,columnspan=2,sticky="nesw")    
        self.input_area.grid(column=0,row=2,sticky="nesw")                
        self.send_button.grid(column=1,row=2,sticky="nesw")               

        self.text_area.config(state="disabled")


    # Communication


    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            self.connected = True
        except Exception as e:
            self.error_label.config(text=f"Impossible de se connecter au serveur\n{self.host}:{self.port}")
            

    def write(self, event = None):
        input = self.input_area.get("1.0","end")
        if len(input.replace(" ","").replace(NEW_LINE_CHAR,"")) != 0:
            message = self.input_area.get("1.0","end")
            self.sock.send(message.encode("utf-8"))
            self.input_area.delete("1.0","end")
    

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode("utf-8")

                if message == "[asking_nickname]":
                    self.sock.send(self.nickname.encode("utf-8"))
                
                elif message == "[nickname_already_taken]": #FIXME Redemander nom si invalide
                    self.log("[Nom déjà pris.\nVeuillez redémarrer l'application]")

                elif message == "[address_banned]":
                    self.log("[Vous avez été banni]")

                elif self.gui_done:
                    self.text_area.config(state="normal")
                    self.log(message)

                    # Ajoute photo de profil 
                    #self.text_area.image_create("end",image=self.profile_pic)
                    # FIXME: La photo de profil du client est affiché sur tous les messages (envoyés ET reçus)
                    # FIXME: La photo de profil doit faire 32x32 peu importe sa taille originale

                    # Surligne mentions et messages informatifs
                    

            except Exception:
                self.sock.close()
                break


    # Fonctions utiles
    def drop_servers_list(self):
        self.servers_list_button.config(text="▲",command=self.hide_servers_list)
        for server in self.get_servers():
            tkinter.Button(self.servers_list_frame,text=server[1],command= lambda: self.insert_in_server_entry(server[0])).pack()

    def hide_servers_list(self):
        for widget in self.servers_list_frame.winfo_children():
            widget.destroy()
        self.servers_list_button.config(text="▼",command=self.drop_servers_list)


    def insert_in_server_entry(self, ip: str):
        self.server_entry.delete(0, END)
        self.server_entry.insert(0, ip)

    def get_servers(self,ip_only: bool = False) -> list:
        """ Récupère un serveur parmis les favoris """
        with open("servers.txt","r") as f:
            if ip_only:
                ips = []
                for server in f.readlines():
                    ips.append(server.split(";")[0])
                return ips
            else:
                servers = []
                for server in f.readlines():
                    server_tuple = tuple(server.split(";"))
                    servers.append(server_tuple)
                return servers


    def register_server(self):
        """ Enregistre un serveur aux favoris """
        with open("servers.txt","a") as f:
            if self.host not in self.get_servers(ip_only=True):
                f.write(f"{self.host};{simpledialog.askstring('Ajouter aux favoris','Choisissez un nom pour le serveur')}\n")
                self.log("[Serveur ajouté aux favoris]")
                self.menu.delete(2,2)
                self.menu.add_command(label="Supprimer des favoris ★", command=self.unregister_server)
    
    def unregister_server(self):
        """ Supprimer un serveur des favoris"""
        with open("servers.txt","r") as f:
            lines = f.readlines()
        
        # Récupère la ligne à supprimer
        for number, line in enumerate(lines):
            if line.split(";")[0] == self.host:
                line_to_remove = number

        # Réécrit tout le fichier sauf la ligne à supprimer
        with open("servers.txt","w") as f:
            for number, line in enumerate(lines):
                if number != line_to_remove:
                    f.write(line)

        self.menu.delete(2,2)
        self.menu.add_command(label="Ajouter aux favoris ☆", command=self.register_server)

    def log(self,message):
        if "@" + self.nickname in message: self.text_area.insert("end", message,"mention")
        elif message.startswith(self.nickname): self.text_area.insert("end", message,"own_msg")
        elif message.startswith("["): self.text_area.insert("end", message,"msg_info")
        elif message.startswith("*"): self.text_area.insert("end",message[1:],"bold")
        elif message.startswith("!"): self.text_area.insert("end",message[1:],"big")
        elif message.startswith("_"): self.text_area.insert("end",message[1:],"underlined")
        elif message.startswith("-"): self.text_area.insert("end",message[1:],"italic")
        elif message.startswith("/!\\"): self.text_area.insert("end",message[3:],"warning")
        elif message.startswith("&"): self.text_area.insert("end",message[1:],"red")
        else: self.text_area.insert("end",message)

        self.text_area.tag_config("mention",background=PALE_YELLOW)
        self.text_area.tag_config("msg_info",foreground=DARK_BLUE,font=BOLD_FONT) 
        self.text_area.tag_config("own_msg",background=LIGHT_GRAY)
        self.text_area.tag_config("bold",font=BOLD_FONT)
        self.text_area.tag_config("big",font=BIG_FONT)
        self.text_area.tag_config("underlined",font=UNDERLINED_FONT)
        self.text_area.tag_config("italic",font=ITALIC_FONT)
        self.text_area.tag_config("warning",foreground=RED,font=BIG_FONT)
        self.text_area.tag_config("red",foreground=RED)

        self.text_area.yview("end")
        self.text_area.config(state="disabled")


    def is_nickname_valid(self,nickname):
        if len(nickname) < 17 and len(nickname) > 2 and nickname.isalnum(): # alphanumérique et entre 3 et 16 caractères
            return True
        else:
            return False


    def stop(self):
        if messagebox.askokcancel("Quitter", "Voulez vous vraiment quitter ?"):
            self.force_stop()


    def force_stop(self):
        self.win.destroy()
        if self.sock != None:
            self.sock.close()
        self.running = False
        sys.exit(1)


#------------------------------------------------------------------------------------
#                                       MAIN
#------------------------------------------------------------------------------------


def main():
    global win, server_button, client_button, update_label, menu

    # Création de la fenêtre
    win = tkinter.Tk()
    win.configure(bg=DARK_BLUE)                         # Fond bleu foncé
    win.geometry("400x280")                             # Dimensions fenêtre = 400*280
    win.title(VERSION)                                  # Nom de la fenêtre
    win.eval("tk::PlaceWindow . center")                # Fenêtre centrée sur l'écran
    win.resizable(False,False)                          # Impossible de redimensionner la fenêtre
    win.wm_iconbitmap(ICON_PATH)                        # Icône de la fenêtre
    logo = tkinter.PhotoImage(file=LOGO_PATH)           # Import du logo

    tkinter.Label(win,image=logo,bg=DARK_BLUE).pack()   # Affichage du logo

    server_button = tkinter.Button(win,text="Créer un serveur",padx=10,pady=10,bg=DARK_BLUE,fg=WHITE,font=DEFAULT_FONT,command=start_server)
    client_button = tkinter.Button(win,text="Rejoindre un serveur",padx=10,pady=10,bg=DARK_BLUE,fg=WHITE,font=DEFAULT_FONT,command=start_client)
    update_label = tkinter.Label(win,bg=DARK_BLUE,fg=WHITE,font=DEFAULT_FONT)

    # Menu
    menu = tkinter.Menu(win)
    menu.add_command(label="Mode d'emploi", command=lambda: webbrowser.open(WEBSITE_PATH))
    win.config(menu=menu)

    # Affichage des widgets
    server_button.pack(expand=True,fill=BOTH)
    client_button.pack(expand=True,fill=BOTH)
    update_label.pack()
    
    # Mise à jour
    update()

    win.mainloop()


if __name__ == "__main__":
    main()
    
