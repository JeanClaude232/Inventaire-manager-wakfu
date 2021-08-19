
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
import json
import requests
import os


#########
adresse_mail = "Jeanclaude.python3@gmail.com"
background_color = "Grey"


class creation_json():
    """Gestion de la recuperation des api de wakfu pour avoir les recettes et les objets du jeu.
    Ecriture de fichiers locaux pour pouvoir fonctionné ensuite sans internet.
    Verification de la version du jeu et mise a jour si necessaire des fichiers locaux.
    Recuperation des information des fichiers locaux"""

    # gestion des api wakfu
    @classmethod
    def version_find(self) -> str:
        """Methode recupérent la dernière version de wakfu sur le repositorie de l'api wakfu"""
        # on test de se connecté au serveur pour recupérer les infos de la version
        try:
            version_dic = requests.get("https://wakfu.cdn.ankama.com/gamedata/config.json")
        except requests.ConnectionError as e:  # si l'accés au serveur est impossible on retourne une erreur
            return e

        # recuperation de la version sous forme de str
        version_dic = version_dic.text
        version = json.loads(version_dic)["version"]

        # ecriture de la version dans un fichier local
        with open("version.json", "w") as f:
            json.dump(version, f, indent=2)

        # retour de la version sous forme str
        return version

    @classmethod
    def version_local(cls) -> str:
        """Recupere la version locale de wakfu"""
        if os.path.exists("version.json"):
            with open("version.json", "r")as f:  # ouverture du fichier local
                version = json.load(f)
            return version
        else:
            return False

    @classmethod
    def recup_resultat_recette(self) -> dict:
        """Recuperation du dictionnaire des resultats de recette de l'api et ecriture du fichier local"""
        # recherche des api
        # on recupere la version
        version = self.version_local()

        # test de la connexion au serveur et stockage du resultas si la connexion ce fait
        try:
            resultats_recette = requests.get(f"https://wakfu.cdn.ankama.com/gamedata/{version}/recipeResults.json")

        # retour de l'exception si le serveur ne repond pas
        except requests.ConnectionError as e:
            return e
        # recuperation du dictionnaire des recette
        resultats_recette = resultats_recette.text
        resultats_recette = json.loads(resultats_recette)
        return resultats_recette

    @classmethod
    def recup_ingred_recette(cls) -> dict:
        """Recuperation du dictionnaire des ingredients de l'api et ecriture du fichier local"""
        # recherche des api
        version = cls.version_local()

        # test de la connexion au serveur et stockage du resultas si la connexion ce fait
        try:
            ingredients_recette = requests.get(f"https://wakfu.cdn.ankama.com/gamedata/{version}/recipeIngredients.json")

        # retour de l'exception si le serveur ne repond pas
        except requests.ConnectionError as e:
            return e
        # recuperation du dictionnaire des ingredients
        ingredients_recette = ingredients_recette.text
        ingredients_recette = json.loads(ingredients_recette)
        return ingredients_recette

    @classmethod
    def recup_item(cls) -> dict:
        """Recuperation du dictionnaire des caracteristique des items de l'api et ecriture du fichier local"""
        # recherche des items
        version = cls.version_local()

        # test de la connexion au serveur et stockage du resultas si la connexion ce fait
        try:
            items = requests.get(f"https://wakfu.cdn.ankama.com/gamedata/{version}/jobsItems.json")

        # retour de l'exception si le serveur ne repond pas
        except requests.ConnectionError as e:
            return e
        # recuperation du dictionnaire des items
        items = items.text
        items = json.loads(items)
        # extraction des infos utiles du dictionnaire
        items_simp = {}
        rarete = ["Commun", "Inhabituel", "Rare", "Mythique", "Légendaire", "Relique", "Epique", "Souvenir"]
        for it in items:
            if 'title' in it.keys():
                items_simp[it["definition"]["id"]] = f"{it['title']['fr']:<5} {rarete[it['definition']['rarity']]:>10}"
        # ecriture du fichier local des items
        with open("items.json", "w") as f:
            json.dump(items_simp, f, indent=2)
        # retour du dict simplifier
        return items_simp

    @classmethod
    def json_dump(self) -> None:
        """Formatage et ecriture des fichier des recettes :
            -dictionnaire des recettes et leur ingredient
            -dictionnaire des recettes lier a leur identifiant"""
        dict_recette_json = {}  # dictionnaire contenant les ingredients des recettes
        id_recette = {}  # dictionnaire liant le nom de la recette a son id
        # recuperation des resultats
        try:
            self.version_find()
        except requests.ConnectionError as e:
            return e
        resultats_recette = self.recup_resultat_recette()
        if isinstance(resultats_recette, requests.exceptions.ConnectionError):  # check si la connexion au serveur est ok
            return requests.ConnectionError
        items_simp = self.recup_item()
        if isinstance(items_simp, requests.exceptions.ConnectionError):  # check si la connexion au serveur est ok
            return requests.ConnectionError
        ingredients_recette = self.recup_ingred_recette()
        if isinstance(ingredients_recette, requests.exceptions.ConnectionError):  # check si la connexion au serveur est ok
            return requests.ConnectionError

        # recuperation des resultats de chaque recette
        for it in resultats_recette:
            # on check les erreurs dans l'api: items qui ont une recette mais pas existants
            if it["productedItemId"] in items_simp.keys():
                # clé = id recette
                dict_recette_json[it["recipeId"]] = {"resultat": {
                                                          "item": items_simp[it["productedItemId"]],
                                                          "quantite": it["productedItemQuantity"]},
                                                     "ingredient": {}
                                                     }
                # dict nom produit = id item produit
                id_recette[items_simp[it["productedItemId"]]] = it["recipeId"]

        # on recupere les ingrédient des recettes
        for it in ingredients_recette:
            if it["itemId"] in items_simp.keys() and it["recipeId"] in dict_recette_json.keys():  #check item valide
                # liaison de chaque item, quantite a sa recette
                dict_recette_json[it["recipeId"]]["ingredient"][items_simp[it["itemId"]]] = it["quantity"]
        self.dic_itemtorect = {}
        # dictionnaire permettant de lier l'objet a toutes ses recettes
        for it in ingredients_recette:
            if it["itemId"] in items_simp.keys() and it["recipeId"] in dict_recette_json.keys():
                if it["itemId"] in self.dic_itemtorect.keys():
                    self.dic_itemtorect[it["itemId"]] += [it["recipeId"]]
                else:
                    self.dic_itemtorect[it["itemId"]] = [it["recipeId"]]


        # ecriture des fichier locaux
        with open("recette.json", "w") as f:
            json.dump(dict_recette_json, f, indent=2)

        with open("recette_id.json", "w") as f:
            json.dump(id_recette, f, indent=2)

        with open("item_to_rect.json", "w") as f:
            json.dump(self.dic_itemtorect, f, indent=2)

    @classmethod
    def check_fichier(cls) -> bool:
        """ check la presence des fichiers locaux et retourne True si ils sont la"""
        chck_version = os.path.exists("version.json")
        chk_items = os.path.exists("items.json")
        chck_recette = os.path.exists("recette.json")
        chck_recette_id = os.path.exists("recette_id.json")
        if chck_version and chk_items and chck_recette and chck_recette_id:
            return True
        else:
            return False

    @classmethod
    def check_version(cls) -> bool:
        """ Compare la version locale et du serveur pour savoir si les fichiers locaux sont a jour"""

        # test de la connexion au serveur et stockage du resultas si la connexion ce fait
        try:
            version_dic = requests.get("https://wakfu.cdn.ankama.com/gamedata/config.json")

        # retour de l'exception si le serveur ne repond pas
        except requests.ConnectionError as e:
            return e
        version_dic = version_dic.text
        version_web = json.loads(version_dic)["version"]
        version_locale = cls.version_local()

        # check de la version
        if version_locale == version_web:
            return True
        else:
            return False

    @classmethod
    def recuperation_recette_local(cls) -> dict:
        """recupere les recettes des fichiers locaux"""
        with open("recette.json", "r") as f:
            recette = json.load(f)

        return recette

    @classmethod
    def recuperation_recette_id_local(cls) -> dict:
        """recupere les id recettes des fichiers locaux"""
        with open("recette_id.json", "r") as f:
            recette_id = json.load(f)

        return recette_id


class interface(Tk):
    """Application permettant d'afficher les recettes rechercher et l'inventaire du joueurs
    Permet a l'utilisateur de voir les recettes sélectionné disponible a la confection selon son inventaire"""
    WIDTH, LENGTH = "1000", "700"

    def __init__(self):
        Tk.__init__(self)

        self.geometry(f"{self.WIDTH}x{self.LENGTH}")
        self.title("Comparateur de recette")
        self.resizable(False, False)
        self.config(background=background_color)
        dir = os.path.dirname(os.path.abspath(__file__))  # recuperation de l'emplacement de l'application
        # ajout d'une icone
        self.iconphoto(False, PhotoImage(file=f"{dir}\\icone_wakfu.png"))

        #########
        # Check de la version des fichiers et de leur presence et si besoin mise à jour
        # des fichiers ou création de ces derniers
        e = None  # recupere s'il y a une erreur
        if not creation_json.check_fichier():  # check la presence des fichiers nécessaire
            e = creation_json.version_find()  # si la connexion internet fail: renvoie une erreure

            # si une erreur de co est retourner, affichage d'un message
            if e == requests.exceptions.ConnectionError:
                messagebox.showerror("Erreur de connexion", "Pas de fichier locaux: fermeture de l'appli")

            else:
                e = creation_json.json_dump()
        e = creation_json.check_version()

        if not e:

            if creation_json.version_find() == requests.exceptions.ConnectionError:
                print(3)
                messagebox.showerror("Erreur de connexion", "Impossible de mettre a jour les données de l'appli")
                print("aie")
            else:
                e = creation_json.json_dump()

        if e == requests.exceptions.ConnectionError:
            messagebox.showerror("Erreur de connexion", "Impossible de se connecter au serveur")

        ######################
        # fix des probleme de couleur du Treeview

        style = Style()

        def fixed_map(option):
            # Fix for setting text colour for Tkinter 8.6.9
            # From: https://core.tcl.tk/tk/info/509cafafae
            #
            # Returns the style map for 'option' with any styles starting with
            # ('!disabled', '!selected', ...) filtered out.

            # style.map() returns an empty list for missing options, so this
            # should be future-safe.
            return [elm for elm in style.map('Treeview', query_opt=option) if
                    elm[:2] != ('!disabled', '!selected')]

        style.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))

        Style().configure("Treeview.Heading",  activebackground="Red", foreground="Black")
        Style().configure("Treeview", activebackground="Red", foreground="Black", fieldbackground="red")

        ########################

        self.dict_data = {"recette": {}, "inventaire": {}}

        # canvas pour les boutons d'entré de l'inventiare
        self.base_entry_inv = Canvas(self, background="#ded2de")
        self.base_entry_inv.grid(row=2, column=2, pady=5)

        # canvas pour les boutons des recetttes
        self.base_entry_rect = Canvas(self, background="#ded2de")

        self.base_entry_rect.grid(row=2, column=1, pady=5)

        # init des données pour les deroulant de recherche
        self.list_item_init()
        self.list_recette_init()
        self.dict_recette_tot = creation_json.recuperation_recette_local()

        self.menu()
        self.menu_deroulant_recette()
        self.tableau_recette()
        self.quantite_recette()
        self.tableau_inventaire()
        self.deroulant_inventaire()
        self.quantite_inventaire()

        self.text_recherche()
        self.boutton_ajout_inv()
        self.text_recherche_recette()

        self.boutton_suppr_recette()
        self.boutton_retrait_inv()
        #self.boutton_test()
        self.boutton_recette_possible()

        self.boutton_ajout_recette()
        self.licence_wakfu()


        if os.path.exists("save.json"):
            self.load()

    def licence_wakfu(self):
        label = Label(self, text="WAKFU MMORPG: © 2012 - 2021 Ankama Studio.Tous droits réservés", background=background_color)
        label.grid(row=6, columnspan=3, ipady=10)

    def menu(self):
        """bare de menu en haut"""

        self.menu_base = Menu(self)  # base de la barre de menu
        # commande pour sauvegarder l'etat de l'application
        self.menu_base.add_command(label="sauvegarder", command=self.save)
        # commande qui permet de supprimer la sauvegarde actuelle
        self.menu_base.add_command(label="supprimmer sauvegarde", command=self.del_save)
        # commande qui affiche l'addresse mail pour contacter le dev
        self.menu_base.add_command(label="Contact", command=self.contact)

        self.config(menu=self.menu_base)  # liaison de la barre de menu a l'application

    @staticmethod
    def contact():
        """ Method qui permet d'ouvrir une fenetre d'information affichant l'adresse mail du dev"""
        messagebox.showinfo("Contact", f"Pour me contacter \nAdresse mail : {adresse_mail}")

    def save(self):
        """fonction qui sauvegarde l'inventaire et les recettes de l'utilisateur """

        with open("save.json", "w") as f:
            json.dump(self.dict_data, f, indent=2)

    def load(self):
        """Methode qui charge le fichier de sauvegarde et permet de mettre l'application au même manière que lors de
        la sauvegarde
        Cette methode est appellé à l'ouverture de l'application"""

        # Recuperation de la sauvegarde via le fichier json
        with open("save.json", "r") as f:
            self.dict_data = json.load(f)

        # Affichage des données sauvegarder

        # recuperation des recette
        for key in self.dict_data["recette"]:
            # ajout de l'objet produit par la recette
            self.tableau.insert("", "end", iid=key,
                                values=(key,  # nom de l'objet
                                        "",
                                        self.dict_data["recette"][key]["quantite"],  # quantite produite par la recette
                                        self.dict_data["recette"][key]["quantite voulue"]  # quantité voulue par l'utilisateur
                                        )
                                )
            # ajout des ingrédient
            for it in self.dict_data["recette"][key]["ingredient"]:

                self.tableau.insert("", "end", iid=f"{it}/{key}",
                                    values=("",
                                            it,  # nom de l'ingredient
                                            self.dict_data["recette"][key]["ingredient"][it], # quantite pour une utilisation
                                            self.dict_data["recette"][key]["ingredient"][it] *  # quantite pour le
                                            self.dict_data["recette"][key]["quantite voulue"]  # volume voulu
                                            )
                                    )
            self.tableau.insert("", "end")  # ajout d'une ligne vide

        # ajout des objets de l'inventaire sauvegarder
        for key in self.dict_data["inventaire"]:
            self.inventaire.insert("", "end", iid=key,
                                   values=(key,
                                           self.dict_data["inventaire"][key])
                                   )

        self.comparaison_recette_inventaire()

    def del_save(self):
        if os.path.exists("save.json"):
            os.remove("save.json")

    def tableau_recette(self):
        """Tableau des recettes selectionné par l'utilisateur"""

        caneva = Canvas(self)


        self.titre_recet = Label(self, text="Recette", font=("Helvetica", "12", "underline"))
        self.titre_recet.config(background=background_color, foreground="white")
        self.titre_recet.grid(row=1, column=1)
        self.tableau = Treeview(caneva, columns=("recette", "ingredient", "quantite", "quantite voulue"),
                                height=20, selectmode="extended")
        self.tableau.heading("recette", text="recette")
        self.tableau.heading("ingredient", text="ingredient")
        self.tableau.heading("quantite", text="quantite")
        self.tableau.heading("quantite voulue", text="qte voulue")
        self.tableau.column("quantite", width=55, minwidth=50, stretch=False)
        self.tableau.column("quantite voulue", width=55, minwidth=50, stretch=False)

        scrollbar = Scrollbar(caneva, orient="vertical", command=self.tableau.yview)
        self.tableau.config(yscrollcommand=scrollbar.set)

        scrollbar.grid(row=1, column=2, sticky="ns")

        caneva.grid(row=3, column=1, padx=40, pady=20)


        # tag qui colore les lignes en fonction de la dispo du joueur de l'item dans son inventaire

        self.tableau.tag_configure("qte_ok", background="lightgreen")
        self.tableau.tag_configure("qte_nok", background="#ff0146", foreground="white")

        #####

        self.tableau['show'] = 'headings'
        self.tableau.grid(row=1, column=1)

    def list_recette_init(self):
        with open("recette_id.json", "r") as f:
            self.dict_recette = json.load(f)

        self.list_recette = list(self.dict_recette.keys())
        self.list_recette.sort()
        self.list_recette_orig = self.list_recette.copy()

    def menu_deroulant_recette(self):
        # faire un menu deroulant pour les recettes
        self.item_recette = StringVar(self)
        self.item_recette.set(self.list_recette[0])

        self.deroulant = Combobox(self.base_entry_rect, textvariable=self.item_recette, values=self.list_recette)

        self.deroulant.config(width=35)
        self.deroulant.grid(row=2, column=1, pady=5)

    def quantite_recette(self):
        base = Canvas(self.base_entry_rect)
        base.grid(row=3, column=1, pady=5)


        label_quantite = Label(base, text="Quantité : ")
        label_quantite.grid(row=1, column=1)
        self.quantite_rect = Entry(base)
        self.quantite_rect.grid(row=1, column=2)

    def text_recherche_recette(self):
        base = Canvas(self.base_entry_rect)
        base.grid(row=1, column=1, pady=5)
        label = Label(base, text="recherche :")
        label.grid(row=1, column=1)

        self.sv_recette = StringVar()
        self.sv_recette.trace("w", self.recherche_recette)
        self.text_rech_recette = Entry(base, textvariable=self.sv_recette)
        self.text_rech_recette.grid(row=1, column=2)

    def recherche_recette(self, *args):
        self.list_recette = []
        text = self.text_rech_recette.get()
        count =1
        for it in self.list_recette_orig:
            if text.lower() in it.lower():
                self.list_recette.append(it)
                count += 1
        if self.list_recette == []:
            self.list_recette = ["Pas d'objet trouvée"]


        self.deroulant.destroy()
        self.menu_deroulant_recette()

    def boutton_ajout_recette(self):
        self.boutton_ajout_rect = Button(self.base_entry_rect, text="Ajouter", command=self.ajout_recette)
        self.boutton_ajout_rect.grid(row=4, column=1)

    def ajout_recette(self):
        if self.deroulant.get() != "Pas d'objet trouvée":
            item = self.deroulant.get()
        else:
            return None

        id = str(self.dict_recette[item])
        recette = self.dict_recette_tot[id]
        quantite = self.quantite_rect.get()
        if quantite == "":
            quantite = 1
        else:
            quantite = int(quantite)

        self.tableau.insert("", "end", iid=item,
                            values=(recette["resultat"]["item"],
                                    "",
                                    recette["resultat"]["quantite"],
                                    quantite)
                            )
        self.dict_data["recette"][recette["resultat"]["item"]] = {"quantite": recette["resultat"]["quantite"],
                                                                        "quantite voulue": quantite, "ingredient": {}}

        count = 1
        for key in recette["ingredient"]:
            self.dict_data["recette"][recette["resultat"]["item"]]["ingredient"][key] = recette["ingredient"][key]
            self.tableau.insert("", "end", iid=f"{key}/{item}",
                                values=("",
                                        key,
                                        recette["ingredient"][key],
                                        recette["ingredient"][key] * quantite
                                        )
                                )
            count += 1
        self.tableau.insert("", "end")

        self.comparaison_recette_inventaire()

    def boutton_suppr_recette(self):
        self.suppr_recette_bt = Button(self, text="supprimer", command=self.suppr_recette)
        self.suppr_recette_bt.grid(row=4, column=1)

    def suppr_recette(self):
        list_del = []
        selec = self.tableau.selection()[0]
        selec_sp = selec.split("/")
        if len(selec_sp) == 1:
            for ligne in self.tableau.get_children():
                if selec in ligne:
                    list_del.append(ligne)
            for it in list_del:
                self.tableau.delete(it)
            self.dict_data["recette"].pop(selec)

        else:
            for ligne in self.tableau.get_children():
                if selec_sp[1] in ligne:
                    list_del.append(ligne)
            for it in list_del:
                self.tableau.delete(it)

            self.dict_data["recette"].pop(selec_sp[1])

    def tableau_inventaire(self):
        ##############
        # affichage de l'inventaire
        caneva = Canvas(self)

        self.titre_inv = Label(self, text="Inventaire", font=("Helvetica", "12", "underline"))
        self.titre_inv.config(background=background_color, foreground="white")
        self.titre_inv.grid(row=1, column=2)
        self.inventaire = Treeview(caneva, columns=("Item", "quantité"), height=20)
        self.inventaire.heading("Item", text='item')
        self.inventaire.heading("quantité", text="quantité")
        self.inventaire['show'] = 'headings'
        self.inventaire.column("quantité", width=55, minwidth=50, stretch=False)
        self.inventaire.grid(row=1, column=1)

        scrollbar = Scrollbar(caneva, orient="vertical", command=self.inventaire.yview)
        self.inventaire.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=2, sticky="ns")
        caneva.grid(row=3, column=2)

    def list_item_init(self):
        with open("items.json", "r") as f:
            dict_item = json.load(f)
        self.list_item = list(dict_item.values())
        self.list_item.sort()
        self.list_item_orig = self.list_item.copy()

    def deroulant_inventaire(self):

        self.item_inv = StringVar(self)
        self.item_inv.set(self.list_item[0])
        self.select_item_inv = Combobox(self.base_entry_inv, textvariable=self.item_inv, values=self.list_item, width=35)
        self.select_item_inv.grid(row=2, column=1, pady=5)

    def quantite_inventaire(self):
        base = Canvas(self.base_entry_inv)
        base.grid(row=3, column=1, pady=5)


        label_quantite = Label(base, text="Quantité : ")
        label_quantite.grid(row=1, column=1)
        self.quantite_inv = Entry(base)
        self.quantite_inv.grid(row=1, column=2)

    def text_recherche(self):
        base_i = Canvas(self.base_entry_inv)
        base_i.grid(row=1, column=1, pady=5)
        label = Label(base_i, text="recherche :")
        label.grid(row=1, column=1)

        self.sv_inv = StringVar()
        self.sv_inv.trace("w", self.recherche_inv)
        self.text_rech = Entry(base_i, textvariable=self.sv_inv)
        self.text_rech.grid(row=1, column=2)

    def recherche_inv(self, *args):
        self.list_item = []
        text = self.text_rech.get()
        count =1
        for it in self.list_item_orig:
            if text.lower() in it.lower():
                self.list_item.append(it)
                count += 1
        if self.list_item == []:
            self.list_item = ["Pas d'objet trouvée"]
        print(count)

        self.select_item_inv.destroy()
        self.deroulant_inventaire()

    def boutton_ajout_inv(self):
        self.boutton_ajout = Button(self.base_entry_inv, text="Ajouter", command=self.ajout_inventaire)
        self.boutton_ajout.grid(row=4, column=1)

    def ajout_inventaire(self):
        if self.select_item_inv.get() != "Pas d'objet trouvée":
            item = self.select_item_inv.get()
        else:
            return None
        qte = self.quantite_inv.get()
        if qte == "":
            qte = 1
        self.quantite_inv.destroy()
        self.quantite_inventaire()
        if item in self.dict_data["inventaire"].keys():
            value = int(self.dict_data["inventaire"][item])
            self.dict_data["inventaire"][item] = int(qte) + value
        else:
            self.dict_data["inventaire"][item] = qte

        if item not in self.inventaire.get_children():

            self.inventaire.insert("", "end", iid=item,
                                   values=(item, qte)
                                   )
        else:
            for ligne in self.inventaire.get_children():
                if item == ligne:
                    qte = self.inventaire.item(ligne)["values"][1] + int(qte)
            self.inventaire.delete(item)
            self.inventaire.insert("", "end", iid=item,
                                   values=(item, qte)
                                   )
        self.comparaison_recette_inventaire()

    def comparaison_recette_inventaire(self):

        for recette in self.dict_data["recette"]:
            ko = False
            for key in self.dict_data["recette"][recette]["ingredient"]:
                if key in self.dict_data["inventaire"].keys():
                    if int(self.dict_data["inventaire"][key]) >= int(self.dict_data["recette"][recette]["ingredient"][key] *
                                                                     self.dict_data["recette"][recette]["quantite voulue"]):
                        self.tableau.item(f"{key}/{recette}", tags=("qte_ok",))
                else:
                    self.tableau.item(f"{key}/{recette}", tags=("qte_nok",))
                    ko = True
            if ko:
                self.tableau.item(f"{recette}", tags=("qte_nok",))
            else:
                self.tableau.item(f"{recette}", tags=("qte_ok",))

    def comparaison_recette_inventaire_v2(self, recette):

        ko = False
        for key in self.dict_data["recette"][recette]["ingredient"]:
            if key in self.dict_data["inventaire"].keys():
                if int(self.dict_data["inventaire"][key]) >= int(
                        self.dict_data["recette"][recette]["ingredient"][key] *
                        self.dict_data["recette"][recette]["quantite voulue"]):
                    self.tableau.item(f"{key}/{recette}", tags=("qte_ok",))
            else:
                self.tableau.item(f"{key}/{recette}", tags=("qte_nok",))
                ko = True
        if ko:
            self.tableau.item(f"{recette}", tags=("qte_nok",))
        else:
            self.tableau.item(f"{recette}", tags=("qte_ok",))

    def boutton_test(self):
        self.test = Button(self, text="test", command=self.check_recette_possible)
        self.test.grid(row=5, column=1)

    def boutton_recette_possible(self):
        canevas = Canvas(self, background=background_color)

        label = Label(canevas, text="Recherche des recettes possible:", background="lightblue", borderwidth=-1)
        label.grid(row=1, column=1)

        self.btn_possible = Button(canevas, text="Rechercher", command=self.check_recette_possible)
        self.btn_possible.grid(row=1, column=2)
        canevas.grid(row=4, column=2)

    def check_recette_possible(self):
        with open("items.json", "r") as f:
            dict_item = json.load(f)  # nom = ###id

        with open("item_to_rect.json", "r") as f:
            dic_id_item_to_rect = json.load(f)
        item_id = {value:key for key, value in dict_item.items()}
        recette_potentielle = []

        for item in self.dict_data["inventaire"]:
            if item != "Poudre Légendaire":
                Id = item_id[item]
                if Id in dic_id_item_to_rect.keys():
                    recette_potentielle += dic_id_item_to_rect[Id]
        liste_recette_possible = []
        for id in recette_potentielle:
            test = self.recette_possible(id)
            if test != None:
                liste_recette_possible.append(test)
        self.recette_possible_set = set(liste_recette_possible)
        text = ""
        for it in self.recette_possible_set:

            text += it+"\n"
        messagebox.showinfo(title="Recette possible", message=text)

    def recette_possible(self, id_recette):

        recette = self.dict_recette_tot[str(id_recette)]

        ko = False
        for key in recette["ingredient"]:
            if key in self.dict_data["inventaire"].keys():

                if int(self.dict_data["inventaire"][key]) < int(recette["ingredient"][key]):
                    ko = True

            else:
                ko = True

        if ko == False:
            return self.dict_recette_tot[str(id_recette)]["resultat"]["item"]

    def boutton_retrait_inv(self):

        self.boutton_suppr_inv = Button(self, text="supprimer", command=self.retrait_inventaire)
        self.boutton_suppr_inv.grid(row=4, column=2)

    def retrait_inventaire(self):
        selec = self.inventaire.selection()[0]
        self.inventaire.delete(selec)



interface = interface()
interface.mainloop()

