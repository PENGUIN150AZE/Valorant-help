import customtkinter as ctk
import json
import os
import io
from tkinter import filedialog # Pour la sélection de fichiers
from PIL import Image # Nécessaire pour CTkImage
import tempfile # Importation de tempfile pour les fichiers temporaires

# Définition des couleurs pour chaque rôle d'agent (Non utilisé pour les icônes, mais gardé pour référence si besoin futur)
ROLE_COLORS = {
    "Duelliste": "#E74C3C",  # Rouge
    "Contrôleur": "#3498DB", # Bleu
    "Initiateur": "#F39C12", # Orange
    "Sentinelle": "#2ECC71", # Vert
    "Inconnu": "#7F8C8D"     # Gris pour les rôles inconnus ou par défaut
}

# Définitions de thèmes de couleurs personnalisés
# Ces thèmes sont définis directement dans le code pour une meilleure gestion
# Ils peuvent être chargés par leur nom via les add-ons
CUSTOM_THEMES = {
    "red_theme": {
        "CTkFrame": {"fg_color": "#4A0000"},
        "CTkButton": {"fg_color": "#CC0000", "hover_color": "#FF3333"},
        "CTkLabel": {"text_color": "#FFCCCC"},
        "CTkEntry": {"fg_color": "#660000", "border_color": "#CC0000"},
        "CTkComboBox": {"fg_color": "#660000", "border_color": "#CC0000"},
        "CTkScrollableFrame": {"fg_color": "#4A0000"},
        "CTkCheckBox": {"fg_color": "#CC0000", "hover_color": "#FF3333"},
        # Ajoutez d'autres widgets CustomTkinter si nécessaire
    },
    "orange_theme": {
        "CTkFrame": {"fg_color": "#4A2200"},
        "CTkButton": {"fg_color": "#CC6600", "hover_color": "#FF8800"},
        "CTkLabel": {"text_color": "#FFDDCC"},
        "CTkEntry": {"fg_color": "#663300", "border_color": "#CC6600"},
        "CTkComboBox": {"fg_color": "#663300", "border_color": "#CC6600"},
        "CTkScrollableFrame": {"fg_color": "#4A2200"},
        "CTkCheckBox": {"fg_color": "#CC6600", "hover_color": "#FF8800"},
    },
    "yellow_theme": {
        "CTkFrame": {"fg_color": "#4A4A00"},
        "CTkButton": {"fg_color": "#CCCC00", "hover_color": "#FFFF33"},
        "CTkLabel": {"text_color": "#FFFFCC"},
        "CTkEntry": {"fg_color": "#666600", "border_color": "#CCCC00"},
        "CTkComboBox": {"fg_color": "#666600", "border_color": "#CCCC00"},
        "CTkScrollableFrame": {"fg_color": "#4A4A00"},
        "CTkCheckBox": {"fg_color": "#CCCC00", "hover_color": "#FFFF33"},
    },
    "violet_theme": {
        "CTkFrame": {"fg_color": "#330033"},
        "CTkButton": {"fg_color": "#660066", "hover_color": "#993399"},
        "CTkLabel": {"text_color": "#CC99CC"},
        "CTkEntry": {"fg_color": "#440044", "border_color": "#660066"},
        "CTkComboBox": {"fg_color": "#440044", "border_color": "#660066"},
        "CTkScrollableFrame": {"fg_color": "#330033"},
        "CTkCheckBox": {"fg_color": "#660066", "hover_color": "#993399"},
    }
}


class ValorantAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Valorant Agent Recommender")
        # self.geometry("1000x700") # La géométrie initiale n'est plus aussi pertinente avec 'zoomed'
        # self.attributes('-fullscreen', True) # Ancien mode plein écran
        self.state('zoomed') # Nouveau: maximise la fenêtre tout en laissant la barre des tâches visible

        # Configurer la grille pour qu'elle soit redimensionnable
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Définition des rôles des agents (données de base)
        self.agent_roles = {
            "Astra": "Contrôleur", "Breach": "Initiateur", "Brimstone": "Contrôleur",
            "Clove": "Contrôleur", "Cypher": "Sentinelle", "Deadlock": "Sentinelle",
            "Fade": "Initiateur", "Gekko": "Initiateur", "Harbor": "Contrôleur",
            "Jett": "Duelliste", "Kay/O": "Initiateur", "Killjoy": "Sentinelle",
            "Neon": "Duelliste", "Omen": "Contrôleur", "Phoenix": "Duelliste",
            "Raze": "Duelliste", "Reyna": "Duelliste", "Sage": "Sentinelle",
            "Skye": "Initiateur", "Sova": "Initiateur", "Viper": "Contrôleur",
            "Yoru": "Duelliste", "Iso": "Duelliste"
        }

        # Liste de tous les agents Valorant (données de base), triée par nom
        self.all_agents = sorted(self.agent_roles.keys())

        # Liste de toutes les cartes Valorant (données de base)
        self.all_maps = [
            "Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox",
            "Lotus", "Pearl", "Split", "Sunset"
        ]
        self.all_maps.sort() # Tri alphabétique

        # Recommandations d'agents par carte (données de base)
        self.map_recommendations = {
            "Ascent": {
                "unlocked_best": {"agent": "Omen", "reason": "Omen est excellent sur Ascent pour ses smokes précises qui coupent les lignes de vue importantes et sa téléportation qui permet des rotations rapides ou des pushes agressifs."},
                "locked_best": {"agent": "Killjoy", "reason": "Killjoy est très forte sur Ascent grâce à sa capacité à verrouiller les sites avec sa tourelle et ses molotovs, rendant les retakes difficiles pour les ennemis."},
                "general_good_agents": ["Jett", "Sova", "KAY/O", "Brimstone", "Sage"]
            },
            "Bind": {
                "unlocked_best": {"agent": "Raze", "reason": "Raze brille sur Bind avec ses grenades et son ulti qui peuvent nettoyer les coins serrés et forcer les ennemis à sortir de leurs positions."},
                "locked_best": {"agent": "Skye", "reason": "Skye est polyvalente sur Bind, ses flashs peuvent aveugler les ennemis à travers les téléporteurs et son chien peut obtenir des informations cruciales."},
                "general_good_agents": ["Brimstone", "Viper", "Cypher", "Phoenix", "Reyna"]
            },
            "Breeze": {
                "unlocked_best": {"agent": "Viper", "reason": "Viper est essentielle sur Breeze pour contrôler les longues lignes de vue avec son mur de fumée et son ulti qui sécurise de vastes zones."},
                "locked_best": {"agent": "Cypher", "reason": "Cypher peut verrouiller des zones clés sur Breeze avec ses cages et sa caméra espionne, offrant une excellente information et des flank guards."},
                "general_good_agents": ["Jett", "Sova", "KAY/O", "Skye", "Yoru"]
            },
            "Fracture": {
                "unlocked_best": {"agent": "Brimstone", "reason": "Brimstone est idéal pour Fracture avec ses smokes longues durées pour bloquer les entrées et son ulti qui peut nettoyer les sites ou empêcher les désamorçages."},
                "locked_best": {"agent": "Fade", "reason": "Fade excelle sur Fracture en obtenant des informations sur les positions ennemies avec ses Prowlers et Haunt, et en initiant des pushes avec Nightfall."},
                "general_good_agents": ["Raze", "Breach", "Chamber", "Killjoy", "Neon"]
            },
            "Haven": {
                "unlocked_best": {"agent": "Sova", "reason": "Sova est très fort sur Haven pour ses flèches de reconnaissance qui couvrent les trois sites et son ulti qui peut traverser les murs."},
                "locked_best": {"agent": "Kay/O", "reason": "Kay/O est excellent pour désactiver les capacités ennemies sur Haven, ce qui est crucial pour prendre les sites ou défendre contre les rushes."},
                "general_good_agents": ["Omen", "Jett", "Killjoy", "Cypher", "Breach"]
            },
            "Icebox": {
                "unlocked_best": {"agent": "Sage", "reason": "Sage est précieuse sur Icebox pour ralentir les pushes ennemis avec ses orbes de ralentissement et bloquer les goulots d'étranglement avec son mur."},
                "locked_best": {"agent": "Viper", "reason": "Viper est dominante sur Icebox, utilisant son mur et sa boule de poison pour bloquer des chemins entiers et rendre les sites très difficiles à prendre."},
                "general_good_agents": ["Jett", "Sova", "Killjoy", "Cypher", "Reyna"]
            },
            "Lotus": {
                "unlocked_best": {"agent": "Omen", "reason": "Omen est polyvalent sur Lotus avec ses smokes pour bloquer les rotations et son ulti pour les téléportations rapides entre les sites."},
                "locked_best": {"agent": "Gekko", "reason": "Gekko est excellent pour les entrées sur Lotus, ses créatures peuvent nettoyer les corners et planter/désamorcer le spike en toute sécurité."},
                "general_good_agents": ["Skye", "Breach", "Killjoy", "Raze", "Astra"]
            },
            "Pearl": {
                "unlocked_best": {"agent": "Astra", "reason": "Astra contrôle bien Pearl avec ses étoiles qui peuvent bloquer des entrées multiples et son ulti qui divise la carte."},
                "locked_best": {"agent": "Harbor", "reason": "Harbor est très efficace sur Pearl pour créer des couvertures avec ses murs d'eau et son ulti qui ralentit les ennemis sur de grandes surfaces."},
                "general_good_agents": ["Viper", "KAY/O", "Fade", "Killjoy", "Jett"]
            },
            "Split": {
                "unlocked_best": {"agent": "Raze", "reason": "Raze est agressive sur Split, utilisant ses grenades pour déloger les ennemis des positions défensives et son ulti pour les éliminations rapides."},
                "locked_best": {"agent": "Cypher", "reason": "Cypher est un excellent défenseur sur Split, ses fils de détection et sa caméra espionne peuvent surveiller les goulots d'étranglement étroits et prévenir les pushes."},
                "general_good_agents": ["Jett", "Omen", "Sage", "Killjoy", "Breach"]
            },
            "Sunset": {
                "unlocked_best": {"agent": "Reyna", "reason": "Reyna est une duelliste forte sur Sunset avec ses capacités d'auto-guérison et de désengagement après des éliminations, idéale pour les combats rapprochés."},
                "locked_best": {"agent": "Iso", "reason": "Iso est un duelliste puissant pour Sunset, capable de prendre des duels en un contre un avec son bouclier et son ulti qui isole un ennemi."},
                "general_good_agents": ["Omen", "Killjoy", "Fade", "Raze", "Cypher"]
            },
        }

        self.unlocked_agents = self.load_unlocked_agents()
        self.selected_role_filter = "Tous" # Filtre de rôle par défaut
        self.selected_map = None # Variable pour stocker la carte actuellement sélectionnée

        # Variable pour stocker l'information de l'agent "meilleur débloqué" s'il n'est pas possédé
        # et l'agent alternatif débloqué si trouvé
        self.unlocked_but_not_owned_agent_info = None
        self.alternative_owned_agent_for_display = None # Nouveau: pour l'agent alternatif débloqué

        self.current_text_font_size = 14 # Taille de police par défaut pour les zones de texte
        self.available_font_sizes = [12, 14, 16, 18, 20] # Tailles de police disponibles

        # Dictionnaire pour stocker les objets CTkImage des agents (maintenant vide, car les icônes sont supprimées)
        self.agent_icons = {} 
        
        # Liste pour stocker les images chargées via les add-ons
        self.addon_images = []
        # Chemin du dossier pour les images d'add-ons
        self.addon_images_folder = "addon_images" 
        if not os.path.exists(self.addon_images_folder):
            os.makedirs(self.addon_images_folder)

        # Initialize UI elements to None so they can be checked before creation
        self.main_content_frame = None
        self.addon_images_frame = None 
        self.status_label = None 
        self.initial_tutorial_frame = None 
        self.initial_tutorial_textbox = None # Initialiser les textboxes
        self.info_text_box = None 
        self.other_agents_text_box = None 
        self.addons_tutorial_text_box = None 
        self.font_size_combobox = None # Initialiser la combobox

        # Nouveau: Cadre pour les boutons d'addons
        self.addon_buttons_frame = None
        # Nouveau: Variable pour suivre la visibilité du cadre des boutons d'addons
        self.addon_buttons_visible = False

        # Données des addons
        self.addons_data = self.load_addons_data()
        
        # Fichier pour suivre si le tutoriel initial a été vu
        self.tutorial_seen_file = "tutorial_seen.txt"

        # Création des cadres de l'interface utilisateur
        # Cela appellera create_widgets ou show_initial_tutorial_view
        self.check_and_show_initial_tutorial()

        # Maintenant que les widgets sont créés (ou le seront après la fermeture du tutoriel),
        # appliquer les paramètres d'interface utilisateur des add-ons.
        self._apply_addon_ui_settings(self.addons_data)

        # Nouveau: Lier la touche '!' pour afficher/masquer les boutons d'addons
        self.bind("!", self.toggle_addon_buttons_visibility)


    def check_and_show_initial_tutorial(self):
        """Vérifie si le tutoriel initial a été vu et l'affiche si ce n'est pas le cas."""
        if not os.path.exists(self.tutorial_seen_file):
            self.show_initial_tutorial_view()
            # Marquer le tutoriel comme vu après l'avoir affiché
            with open(self.tutorial_seen_file, "w") as f:
                f.write("seen")
        else:
            self.create_widgets() # Créer l'interface principale si le tutoriel a déjà été vu

    def show_initial_tutorial_view(self):
        """Affiche la vue du tutoriel initial."""
        self.initial_tutorial_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.initial_tutorial_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        self.initial_tutorial_frame.grid_columnconfigure(0, weight=1)
        self.initial_tutorial_frame.grid_rowconfigure(2, weight=1) # Pour que le texte s'étende

        ctk.CTkLabel(self.initial_tutorial_frame, text="Bienvenue dans le Recommandeur d'Agents Valorant !",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(0, 20))

        tutorial_text = """
        Cette application vous aide à choisir le meilleur agent pour votre partie de Valorant !

        Voici comment l'utiliser :

        1.  **Agents Débloqués :** Cochez les agents que vous possédez dans la section "Agents Débloqués".
            Vous pouvez filtrer par rôle ou rechercher un agent par son nom.
            N'oubliez pas de cliquer sur "Sauvegarder Agents Débloqués" pour enregistrer vos choix.

        2.  **Sélectionner une Carte :** Choisissez la carte sur laquelle vous allez jouer.
            Vous pouvez rechercher la carte ou la sélectionner dans la liste.

        3.  **Recommandations d'Agents :** L'application vous proposera alors :
            * Le "Meilleur Agent Débloqué" (parmi ceux que vous possédez et avez cochés).
            * Le "Meilleur Agent Non Débloqué" (l'agent le plus fort pour la carte, même si vous ne le possédez pas encore).

            Utilisez les boutons "Plus d'informations" et "Autres agents" pour des détails supplémentaires.

        **Système d'Add-ons :**
        Vous pouvez étendre les données de l'application en ajoutant des "Add-ons" !
        Appuyez sur la touche "!" de votre clavier pour faire apparaître les boutons d'Add-ons et les options de l'application en bas à droite de l'écran.
        Cliquez sur "Tutoriels Add-ons" pour savoir comment en ajouter ou en créer.

        Amusez-vous bien et bonne chance dans vos parties !
        """
        self.initial_tutorial_textbox = ctk.CTkTextbox(self.initial_tutorial_frame, wrap="word",
                                                       font=ctk.CTkFont(size=self.current_text_font_size),
                                                       height=400)
        self.initial_tutorial_textbox.insert("1.0", tutorial_text)
        self.initial_tutorial_textbox.configure(state="disabled")
        self.initial_tutorial_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.got_it_button = ctk.CTkButton(self.initial_tutorial_frame, text="Compris !", command=self.return_to_main_view)
        self.got_it_button.grid(row=2, column=0, pady=20)


    def load_addons_data(self):
        """Charge les données des addons depuis un fichier JSON."""
        if os.path.exists("addons_data.json"):
            try:
                with open("addons_data.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des données d'addons: {e}")
                return {}
        return {}

    def save_addons_data(self):
        """Sauvegarde les données des addons dans un fichier JSON."""
        try:
            # Assurez-vous que self.status_label existe avant de l'utiliser
            if hasattr(self, 'status_label') and self.status_label is not None:
                with open("addons_data.json", "w") as f:
                    json.dump(self.addons_data, f, indent=4)
                self.status_label.configure(text="Add-on chargé avec succès ! Redémarrez l'application.", text_color="green")
            else:
                # Si status_label n'est pas encore créé (ex: au premier chargement)
                with open("addons_data.json", "w") as f:
                    json.dump(self.addons_data, f, indent=4)
                print("Addon data saved (status label not yet available).")
        except Exception as e:
            if hasattr(self, 'status_label') and self.status_label is not None:
                self.status_label.configure(text=f"Erreur lors du chargement de l'addon: {e}", text_color="red")
            else:
                print(f"Error saving addon data: {e}")
        if hasattr(self, 'status_label') and self.status_label is not None:
            self.after(3000, lambda: self.status_label.configure(text=""))

    def _apply_addon_ui_settings(self, data):
        """Applique les paramètres d'interface utilisateur des données d'addon après que les widgets soient créés."""
        if "ui_settings" in data:
            ui_settings = data["ui_settings"]
            
            if "app_appearance_mode" in ui_settings:
                ctk.set_appearance_mode(ui_settings["app_appearance_mode"])
            
            if "app_color_theme" in ui_settings:
                theme_name = ui_settings["app_color_theme"]
                if theme_name in CUSTOM_THEMES:
                    # Créer un fichier JSON temporaire pour le thème personnalisé
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_theme_file:
                        json.dump(CUSTOM_THEMES[theme_name], temp_theme_file, indent=4)
                        temp_file_path = temp_theme_file.name
                    try:
                        ctk.set_default_color_theme(temp_file_path)
                    except Exception as e:
                        print(f"Erreur lors de l'application du thème personnalisé '{theme_name}': {e}")
                    finally:
                        # Supprimer le fichier temporaire
                        os.remove(temp_file_path)
                else:
                    # Utiliser les thèmes CustomTkinter intégrés
                    ctk.set_default_color_theme(theme_name)
            
            if "text_font_size" in ui_settings:
                self.current_text_font_size = ui_settings["text_font_size"]
                # Réappliquer la taille de police aux zones de texte existantes si elles existent
                if self.initial_tutorial_textbox is not None:
                    self.initial_tutorial_textbox.configure(font=ctk.CTkFont(size=self.current_text_font_size))
                if self.info_text_box is not None:
                    self.info_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
                if self.other_agents_text_box is not None:
                    self.other_agents_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
                if self.addons_tutorial_text_box is not None:
                    self.addons_tutorial_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
                # La combobox est maintenant dans le cadre des addons, elle sera mise à jour lors de sa création.
                # Si elle existe déjà (par exemple, lors d'une recréation de widgets), on la met à jour ici.
                if self.font_size_combobox is not None:
                    self.font_size_combobox.set(str(self.current_text_font_size))


    def apply_addon_data(self, data):
        """Applique les données d'addon chargées aux données de l'application.
        Cette méthode gère les données non-UI (agents, maps, images).
        Les paramètres UI sont gérés par _apply_addon_ui_settings.
        """
        # Ajouter de nouveaux agents
        if "new_agents" in data:
            for agent, role in data["new_agents"].items():
                if agent not in self.agent_roles:
                    self.agent_roles[agent] = role
                    self.all_agents.append(agent)
            self.all_agents.sort() # Re-trier la liste des agents

        # Ajouter de nouvelles cartes
        if "new_maps" in data:
            for map_name in data["new_maps"]:
                if map_name not in self.all_maps:
                    self.all_maps.append(map_name)
            self.all_maps.sort() # Re-trier la liste des cartes

        # Mettre à jour les recommandations de cartes
        if "map_recommendations_updates" in data:
            for map_name, updates in data["map_recommendations_updates"].items():
                if map_name not in self.map_recommendations:
                    self.map_recommendations[map_name] = {}
                self.map_recommendations[map_name].update(updates)
        
        # Mettre à jour les données d'addons persistantes
        self.addons_data.update(data)

        # Charger les images des add-ons
        if "new_images" in data:
            self.addon_images.clear() # Effacer les images précédentes pour éviter les doublons
            for img_info in data["new_images"]:
                img_name = img_info.get("name")
                img_path = os.path.join(self.addon_images_folder, img_info.get("path"))
                img_size = img_info.get("display_size", (100, 100)) # Taille par défaut
                img_position = img_info.get("position", "bottom_right") # Position par défaut

                if os.path.exists(img_path):
                    try:
                        pil_image = Image.open(img_path)
                        pil_image = pil_image.resize(img_size)
                        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=img_size)
                        self.addon_images.append({"name": img_name, "image": ctk_image, "position": img_position})
                        print(f"Image '{img_name}' chargée depuis '{img_path}'")
                    except Exception as e:
                        print(f"Erreur lors du chargement de l'image '{img_name}' depuis '{img_path}': {e}")
                else:
                    print(f"Avertissement: Image '{img_path}' non trouvée pour l'add-on.")
            if self.addon_images_frame is not None:
                self.populate_addon_images() # Mettre à jour l'affichage des images après le chargement des add-ons


    def create_widgets(self):
        # Vérifier si les widgets principaux ont déjà été créés
        if self.main_content_frame is not None:
            return # Ne rien faire si déjà créé

        # Cadre de navigation (pourrait être utilisé pour d'autres sections)
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(10, weight=1) # Pour le label de signature en bas

        self.navigation_frame_label = ctk.CTkLabel(self.navigation_frame, text="Valorant Agent Recommender",
                                                    font=ctk.CTkFont(size=20, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        # Signature en bas à gauche
        self.signature_label = ctk.CTkLabel(self.navigation_frame, text="Fait par la big 92i que t'aime",
                                            font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        self.signature_label.grid(row=10, column=0, padx=10, pady=10, sticky="sw")


        # Cadre principal pour le contenu
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1) # Permet au contenu de s'étendre

        # --- Contenu principal (Agents, Maps, Recommandations) ---
        self.main_content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        # Permet aux cadres défilants de s'étendre verticalement
        self.main_content_frame.grid_rowconfigure(4, weight=1) # agent_checkbox_frame
        self.main_content_frame.grid_rowconfigure(8, weight=1) # map_button_frame
        self.main_content_frame.grid_rowconfigure(15, weight=1) # Pour les images d'add-ons
        self.main_content_frame.grid_rowconfigure(16, weight=0) # Message de statut

        # --- Section 1: Sélection des agents débloqués ---
        self.agent_selection_label = ctk.CTkLabel(self.main_content_frame, text="1. Agents Débloqués",
                                                  font=ctk.CTkFont(size=18, weight="bold"))
        self.agent_selection_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Filtre par catégorie d'agents
        self.role_filter_label = ctk.CTkLabel(self.main_content_frame, text="Filtrer par rôle:")
        self.role_filter_label.grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.role_filter_combobox = ctk.CTkComboBox(self.main_content_frame,
                                                    values=["Tous"] + sorted(list(set(self.agent_roles.values()))),
                                                    command=self.set_role_filter)
        self.role_filter_combobox.set("Tous")
        self.role_filter_combobox.grid(row=2, column=0, sticky="ew", pady=(0, 10))


        self.agent_search_entry = ctk.CTkEntry(self.main_content_frame, placeholder_text="Rechercher un agent...")
        self.agent_search_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.agent_search_entry.bind("<KeyRelease>", self.filter_agents)

        self.agent_checkbox_frame = ctk.CTkScrollableFrame(self.main_content_frame, width=300, height=200)
        self.agent_checkbox_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))

        self.agent_checkboxes = {}
        self.populate_agent_checkboxes()

        self.save_agents_button = ctk.CTkButton(self.main_content_frame, text="Sauvegarder Agents Débloqués", command=self.save_unlocked_agents)
        self.save_agents_button.grid(row=5, column=0, sticky="ew", pady=(0, 20))

        # --- Section 2: Sélection de la carte ---
        self.map_selection_label = ctk.CTkLabel(self.main_content_frame, text="2. Sélectionner une Carte",
                                                font=ctk.CTkFont(size=18, weight="bold"))
        self.map_selection_label.grid(row=6, column=0, sticky="w", pady=(0, 10))

        # Barre de recherche pour les cartes
        self.map_search_entry = ctk.CTkEntry(self.main_content_frame, placeholder_text="Rechercher une carte...")
        self.map_search_entry.grid(row=7, column=0, sticky="ew", pady=(0, 10))
        self.map_search_entry.bind("<KeyRelease>", self.filter_maps)

        # Cadre défilant pour les boutons de carte
        self.map_button_frame = ctk.CTkScrollableFrame(self.main_content_frame, width=300, height=150)
        self.map_button_frame.grid(row=8, column=0, sticky="nsew", pady=(0, 10))

        self.map_buttons = {} # Dictionnaire pour stocker les références aux boutons de carte
        self.populate_map_buttons()

        # Label pour afficher la carte sélectionnée
        self.selected_map_display_label = ctk.CTkLabel(self.main_content_frame, text=f"Carte sélectionnée: Aucune",
                                                       font=ctk.CTkFont(size=15, weight="bold"),
                                                       fg_color="gray20", corner_radius=5, padx=10, pady=5)
        self.selected_map_display_label.grid(row=9, column=0, sticky="w", pady=(0, 20))


        # --- Section 3: Recommandations ---
        self.recommendation_label = ctk.CTkLabel(self.main_content_frame, text="3. Recommandations d'Agents",
                                                 font=ctk.CTkFont(size=18, weight="bold"))
        self.recommendation_label.grid(row=10, column=0, sticky="w", pady=(0, 10))

        # Labels de recommandation avec visibilité améliorée
        self.unlocked_reco_label = ctk.CTkLabel(self.main_content_frame, text=f"Meilleur Agent Débloqué: N/A",
                                                font=ctk.CTkFont(size=16), fg_color="gray20", corner_radius=5,
                                                width=400, wraplength=380, justify="left", padx=10, pady=5)
        self.unlocked_reco_label.grid(row=11, column=0, sticky="w", pady=(0, 5))

        self.locked_reco_label = ctk.CTkLabel(self.main_content_frame, text=f"Meilleur Agent Non Débloqué: N/A",
                                              font=ctk.CTkFont(size=16), fg_color="gray20", corner_radius=5,
                                              width=400, wraplength=380, justify="left", padx=10, pady=5)
        self.locked_reco_label.grid(row=12, column=0, sticky="w", pady=(0, 5))

        # Nouveau bouton pour les "Autres agents"
        self.other_agents_button = ctk.CTkButton(self.main_content_frame, text="Autres agents", command=self.show_other_agents_info, state="disabled")
        self.other_agents_button.grid(row=13, column=0, sticky="ew", pady=(10, 5))

        self.more_info_button = ctk.CTkButton(self.main_content_frame, text="Plus d'informations", command=self.show_more_info, state="disabled")
        self.more_info_button.grid(row=14, column=0, sticky="ew", pady=(0, 20))

        # Cadre pour les images d'add-ons
        self.addon_images_frame = ctk.CTkScrollableFrame(self.main_content_frame, width=300, height=100)
        self.addon_images_frame.grid_columnconfigure(0, weight=1)
        # La visibilité est gérée dans populate_addon_images
        self.populate_addon_images() # Afficher les images chargées

        # Message de statut
        self.status_label = ctk.CTkLabel(self.main_content_frame, text="", text_color="green")
        self.status_label.grid(row=16, column=0, sticky="w")

        # --- Cadre pour "Plus d'informations" ---
        self.info_display_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_display_frame.grid_columnconfigure(0, weight=1)
        self.info_display_frame.grid_rowconfigure(1, weight=1) # Permet au texte de s'étendre

        ctk.CTkLabel(self.info_display_frame, text="Informations détaillées", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10, sticky="w")
        self.info_text_box = ctk.CTkTextbox(self.info_display_frame, wrap="word", width=450, height=200, font=ctk.CTkFont(size=self.current_text_font_size))
        self.info_text_box.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.close_info_button = ctk.CTkButton(self.info_display_frame, text="X Fermer", command=self.return_to_main_view, fg_color="red")
        self.close_info_button.grid(row=2, column=0, pady=10, sticky="ew")
        self.info_display_frame.grid_forget() # Masquer par défaut

        # --- Cadre pour "Autres agents" ---
        self.other_agents_display_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.other_agents_display_frame.grid_columnconfigure(0, weight=1)
        self.other_agents_display_frame.grid_rowconfigure(1, weight=1) # Permet au texte de s'étendre

        ctk.CTkLabel(self.other_agents_display_frame, text="Autres options d'agents", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10, sticky="w")
        self.other_agents_text_box = ctk.CTkTextbox(self.other_agents_display_frame, wrap="word", width=450, height=200, font=ctk.CTkFont(size=self.current_text_font_size))
        self.other_agents_text_box.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.close_other_agents_button = ctk.CTkButton(self.other_agents_display_frame, text="X Fermer", command=self.return_to_main_view, fg_color="red")
        self.close_other_agents_button.grid(row=2, column=0, pady=10, sticky="ew")
        self.other_agents_display_frame.grid_forget() # Masquer par défaut

        # --- Cadre pour les tutoriels Add-ons ---
        self.addons_tutorial_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.addons_tutorial_frame.grid_columnconfigure(0, weight=1)
        self.addons_tutorial_frame.grid_rowconfigure(3, weight=1) # Pour le texte du tuto

        ctk.CTkLabel(self.addons_tutorial_frame, text="Tutoriels Add-ons", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=(0, 20))
        
        self.how_to_add_addon_button = ctk.CTkButton(self.addons_tutorial_frame, text="Comment ajouter un Add-on ?", command=self.show_how_to_add_addon)
        self.how_to_add_addon_button.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        self.how_to_create_addon_button = ctk.CTkButton(self.addons_tutorial_frame, text="Comment créer un Add-on ?", command=self.show_how_to_create_addon)
        self.how_to_create_addon_button.grid(row=2, column=0, pady=(0, 20), sticky="ew")

        self.addons_tutorial_text_box = ctk.CTkTextbox(self.addons_tutorial_frame, wrap="word", height=300, font=ctk.CTkFont(size=self.current_text_font_size))
        self.addons_tutorial_text_box.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.addons_tutorial_text_box.configure(state="disabled") # Rendre non modifiable par défaut

        self.close_addons_tutorial_button = ctk.CTkButton(self.addons_tutorial_frame, text="X Fermer", fg_color="red", command=self.return_to_main_view)
        self.close_addons_tutorial_button.grid(row=4, column=0, pady=10, sticky="ew")
        self.addons_tutorial_frame.grid_forget() # Masquer par défaut

        # Assurez-vous que le contenu principal est visible au démarrage (si pas de tutoriel initial)
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")

        # Nouveau: Créer le cadre des boutons d'addons et le masquer initialement
        self.create_addon_buttons_frame()


    def create_addon_buttons_frame(self):
        """Crée le cadre contenant les boutons d'addons et le positionne en bas à droite."""
        self.addon_buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        # Positionner en bas à droite avec un léger padding
        # relx=1.0, rely=1.0 signifie le coin inférieur droit du parent
        # x=-20, y=-20 ajoute un décalage de 20px vers l'intérieur
        # anchor="se" signifie que le point d'ancrage du cadre est son propre coin inférieur droit
        self.addon_buttons_frame.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")
        self.addon_buttons_frame.grid_columnconfigure(0, weight=1) # Pour que les boutons s'étirent en largeur

        # Sélecteur de taille de texte (maintenant dans ce cadre)
        self.font_size_label = ctk.CTkLabel(self.addon_buttons_frame, text="Taille du texte:")
        self.font_size_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        self.font_size_combobox = ctk.CTkComboBox(self.addon_buttons_frame,
                                                  values=[str(s) for s in self.available_font_sizes],
                                                  command=self.change_text_size)
        self.font_size_combobox.set(str(self.current_text_font_size)) # Définir la valeur par défaut
        self.font_size_combobox.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="ew")


        # Bouton Ajouter un Add-on
        self.add_addon_button = ctk.CTkButton(self.addon_buttons_frame, text="Ajouter un Add-on", command=self.add_addon)
        self.add_addon_button.grid(row=2, column=0, padx=5, pady=(5, 2), sticky="ew")

        # Bouton Redémarrer l'application
        self.restart_app_button = ctk.CTkButton(self.addon_buttons_frame, text="Redémarrer l'application", command=self.restart_application)
        self.restart_app_button.grid(row=3, column=0, padx=5, pady=2, sticky="ew")

        # Nouveau bouton pour les tutoriels Add-ons
        self.addons_tutorial_button = ctk.CTkButton(self.addon_buttons_frame, text="Tutoriels Add-ons", command=self.show_addons_tutorial_view)
        self.addons_tutorial_button.grid(row=4, column=0, padx=5, pady=2, sticky="ew")

        # Nouveau bouton pour supprimer tous les addons
        self.delete_addons_button = ctk.CTkButton(self.addon_buttons_frame, text="Supprimer tous les Add-ons", command=self.delete_all_addons, fg_color="red", hover_color="#CC0000")
        self.delete_addons_button.grid(row=5, column=0, padx=5, pady=(2, 5), sticky="ew")

        # Masquer le cadre par défaut
        self.addon_buttons_frame.place_forget()
        self.addon_buttons_visible = False

    def toggle_addon_buttons_visibility(self, event=None):
        """Bascule la visibilité du cadre des boutons d'addons."""
        if self.addon_buttons_visible:
            self.addon_buttons_frame.place_forget()
            self.addon_buttons_visible = False
        else:
            self.addon_buttons_frame.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")
            self.addon_buttons_visible = True


    def populate_addon_images(self):
        """Affiche les images chargées via les add-ons dans le cadre dédié.
        Le cadre est masqué s'il n'y a pas d'images.
        """
        # Ensure addon_images_frame is created before trying to access its children
        if self.addon_images_frame is None:
            return

        # Supprimer les images existantes
        for widget in self.addon_images_frame.winfo_children():
            widget.destroy()

        if not self.addon_images:
            # Si aucune image, masquer le cadre entier
            self.addon_images_frame.grid_forget()
            return
        else:
            # S'il y a des images, s'assurer que le cadre est visible
            self.addon_images_frame.grid(row=15, column=0, sticky="nsew", pady=(10, 0))


        row = 0
        for img_data in self.addon_images:
            img_name = img_data["name"]
            ctk_image = img_data["image"]
            # img_position = img_data["position"] # Pour l'instant, toutes les images sont au même endroit

            # Créer un label pour chaque image
            img_label = ctk.CTkLabel(self.addon_images_frame, text=img_name, image=ctk_image, compound="top")
            img_label.grid(row=row, column=0, padx=5, pady=5, sticky="w")
            row += 1


    def recreate_all_widgets(self):
        """Détruit et recrée tous les widgets pour appliquer les changements d'UI."""
        # Détruire tous les widgets existants
        for widget in self.winfo_children():
            widget.destroy()
        
        # Réinitialiser main_content_frame et autres éléments d'interface utilisateur pour la recréation
        self.main_content_frame = None 
        self.addon_images_frame = None
        self.status_label = None
        self.initial_tutorial_frame = None
        self.initial_tutorial_textbox = None
        self.info_text_box = None
        self.other_agents_text_box = None
        self.addons_tutorial_text_box = None
        self.font_size_combobox = None
        self.addon_buttons_frame = None # Réinitialiser le cadre des boutons d'addons aussi

        self.create_widgets() # Recréer tous les widgets

        # Réappliquer les paramètres d'interface utilisateur des données d'addons chargées
        self._apply_addon_ui_settings(self.addons_data)

        # Rafraîchir les cases à cocher des agents et les boutons de carte
        self.populate_agent_checkboxes(self.agent_search_entry.get())
        self.populate_map_buttons(self.map_search_entry.get())
        if self.selected_map:
            self.display_recommendations(self.selected_map)
        else:
            self.selected_map_display_label.configure(text=f"Carte sélectionnée: Aucune")
        
        # Rafraîchir les images d'add-ons
        self.populate_addon_images()


    def set_role_filter(self, selected_role):
        self.selected_role_filter = selected_role
        self.populate_agent_checkboxes(self.agent_search_entry.get())

    def populate_agent_checkboxes(self, filter_text=""):
        # Supprimer les anciennes cases à cocher
        for widget in self.agent_checkbox_frame.winfo_children():
            widget.destroy()
        self.agent_checkboxes.clear()

        # Ajouter de nouvelles cases à cocher filtrées
        row = 0
        for agent in self.all_agents:
            # Filtrer par texte de recherche ET par rôle sélectionné
            matches_search = filter_text.lower() in agent.lower()
            matches_role = (self.selected_role_filter == "Tous" or
                            self.agent_roles.get(agent) == self.selected_role_filter)

            if matches_search and matches_role:
                var = ctk.StringVar(value="on" if agent in self.unlocked_agents else "off")
                # Les arguments 'image' et 'compound' ont été supprimés car CTkCheckBox ne les supporte pas directement.
                checkbox = ctk.CTkCheckBox(self.agent_checkbox_frame,
                                           text=f"{agent} ({self.agent_roles.get(agent, 'Inconnu')})",
                                           variable=var, onvalue="on", offvalue="off")
                checkbox.grid(row=row, column=0, sticky="w", padx=5, pady=2)
                self.agent_checkboxes[agent] = var
                row += 1

    def filter_agents(self, event=None):
        filter_text = self.agent_search_entry.get()
        self.populate_agent_checkboxes(filter_text)

    def save_unlocked_agents(self):
        self.unlocked_agents = [agent for agent, var in self.agent_checkboxes.items() if var.get() == "on"]
        try:
            with open("unlocked_agents.json", "w") as f:
                json.dump(self.unlocked_agents, f)
            if self.status_label is not None: # Check if status_label is initialized
                self.status_label.configure(text="Agents débloqués sauvegardés avec succès !", text_color="green")
        except Exception as e:
            if self.status_label is not None: # Check if status_label is initialized
                self.status_label.configure(text=f"Erreur lors de la sauvegarde: {e}", text_color="red")
        if self.status_label is not None: # Check if status_label is initialized
            self.after(3000, lambda: self.status_label.configure(text="")) # Efface le message après 3 secondes

    def load_unlocked_agents(self):
        if os.path.exists("unlocked_agents.json"):
            try:
                with open("unlocked_agents.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des agents débloqués: {e}")
                return []
        return []

    def populate_map_buttons(self, filter_text=""):
        # Supprimer les anciens boutons de carte
        for widget in self.map_button_frame.winfo_children():
            widget.destroy()
        self.map_buttons.clear()

        row = 0
        for map_name in self.all_maps:
            if filter_text.lower() in map_name.lower():
                button = ctk.CTkButton(self.map_button_frame, text=map_name,
                                       command=lambda m=map_name: self.select_map(m))
                button.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
                self.map_buttons[map_name] = button
                row += 1
        # Mettre à jour la couleur du bouton si une carte est déjà sélectionnée
        if self.selected_map and self.selected_map in self.map_buttons:
            self.map_buttons[self.selected_map].configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])


    def filter_maps(self, event=None):
        filter_text = self.map_search_entry.get()
        self.populate_map_buttons(filter_text)

    def select_map(self, map_name):
        # Réinitialiser la couleur du bouton précédemment sélectionné
        if self.selected_map and self.selected_map in self.map_buttons:
            self.map_buttons[self.selected_map].configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        self.selected_map = map_name
        # Mettre à jour la couleur du bouton sélectionné
        self.map_buttons[self.selected_map].configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])

        self.display_recommendations(map_name)


    def display_recommendations(self, selected_map):
        # Mettre à jour le label de la carte sélectionnée
        self.selected_map_display_label.configure(text=f"Carte sélectionnée: {selected_map}")

        if selected_map == "Sélectionnez une carte":
            self.unlocked_reco_label.configure(text=f"Meilleur Agent Débloqué: N/A")
            self.locked_reco_label.configure(text=f"Meilleur Agent Non Débloqué: N/A")
            self.more_info_button.configure(state="disabled")
            self.other_agents_button.configure(state="disabled")
            self.current_recommendation_info = None
            self.unlocked_but_not_owned_agent_info = None
            self.alternative_owned_agent_for_display = None # Réinitialiser
            return

        recommendations = self.map_recommendations.get(selected_map, {})
        unlocked_reco_data = recommendations.get("unlocked_best", {"agent": "N/A", "reason": ""})
        locked_reco_data = recommendations.get("locked_best", {"agent": "N/A", "reason": ""})
        general_good_agents = recommendations.get("general_good_agents", [])

        best_unlocked_agent = unlocked_reco_data["agent"]
        best_locked_agent = locked_reco_data["agent"]

        # Stocker les informations de la recommandation actuelle pour le bouton "Plus d'informations"
        self.current_recommendation_info = {
            "map": selected_map,
            "unlocked": unlocked_reco_data,
            "locked": locked_reco_data
        }

        # --- NOUVELLE LOGIQUE POUR L'AFFICHAGE DES RECOMMANDATIONS ---
        # Priorité 1: Si le "meilleur global" est débloqué par l'utilisateur, l'afficher comme "Meilleur Agent Débloqué"
        if best_locked_agent != "N/A" and best_locked_agent in self.unlocked_agents:
            self.unlocked_reco_label.configure(text=f"Meilleur Agent Débloqué: {best_locked_agent} (Idéal pour cette carte)")
            
            # Pour le "Meilleur Agent Non Débloqué", trouver un autre agent non débloqué si possible
            alternative_locked_agent = "N/A"
            for agent in self.all_agents:
                if agent not in self.unlocked_agents and agent != best_locked_agent:
                    # On peut chercher une raison spécifique dans map_recommendations si elle existe pour cet agent
                    # Ou simplement indiquer qu'il est une option non débloquée
                    alternative_locked_agent = agent
                    break # On prend le premier trouvé pour l'exemple
            
            if alternative_locked_agent != "N/A":
                self.locked_reco_label.configure(text=f"Meilleur Agent Non Débloqué: {alternative_locked_agent}")
            else:
                self.locked_reco_label.configure(text=f"Meilleur Agent Non Débloqué: Aucun autre agent non débloqué suggéré.")

            self.unlocked_but_not_owned_agent_info = None # Pas besoin de cette info ici
            self.alternative_owned_agent_for_display = None # Pas besoin de cette info ici
            self.other_agents_button.configure(state="disabled") # Désactiver le bouton "Autres agents"
        
        # Priorité 2: Si le "meilleur global" n'est PAS débloqué, alors utiliser la logique précédente
        else:
            if best_unlocked_agent != "N/A" and best_unlocked_agent in self.unlocked_agents:
                self.unlocked_reco_label.configure(text=f"Meilleur Agent Débloqué: {best_unlocked_agent}")
                self.unlocked_but_not_owned_agent_info = None
                self.alternative_owned_agent_for_display = None
                self.other_agents_button.configure(state="disabled")
            else:
                self.unlocked_reco_label.configure(text="Aucun agent débloqué idéal trouvé. Voir 'Autres agents'.")
                if best_unlocked_agent != "N/A": # Si un agent "unlocked_best" existe mais n'est pas possédé
                    self.unlocked_but_not_owned_agent_info = {
                        "agent": best_unlocked_agent,
                        "reason": unlocked_reco_data["reason"],
                        "map": selected_map
                    }
                    # Chercher un agent alternatif que l'utilisateur possède
                    found_alternative = None
                    for agent in general_good_agents:
                        if agent in self.unlocked_agents and agent != best_unlocked_agent:
                            found_alternative = agent
                            break
                    self.alternative_owned_agent_for_display = found_alternative
                    self.other_agents_button.configure(state="normal")
                else: # Si aucun "unlocked_best" n'existe
                    self.unlocked_but_not_owned_agent_info = None
                    self.alternative_owned_agent_for_display = None
                    self.other_agents_button.configure(state="disabled")

            # Toujours afficher le meilleur agent non débloqué si la priorité 1 n'est pas appliquée
            self.locked_reco_label.configure(text=f"Meilleur Agent Non Débloqué: {best_locked_agent}")

        self.more_info_button.configure(state="normal")


    def show_more_info(self):
        if not self.current_recommendation_info:
            return

        map_name = self.current_recommendation_info["map"]
        unlocked_info = self.current_recommendation_info["unlocked"]
        locked_info = self.current_recommendation_info["locked"]

        # Masquer le contenu principal et les autres tutoriels
        if self.main_content_frame is not None:
            self.main_content_frame.grid_forget()
        if self.addons_tutorial_frame is not None:
            self.addons_tutorial_frame.grid_forget()
        if self.other_agents_display_frame is not None:
            self.other_agents_display_frame.grid_forget()
        if hasattr(self, 'initial_tutorial_frame') and self.initial_tutorial_frame is not None:
            self.initial_tutorial_frame.grid_forget()
        # Masquer le cadre des boutons d'addons s'il est visible
        if self.addon_buttons_visible:
            self.toggle_addon_buttons_visibility()

        # Afficher le cadre d'informations
        self.info_display_frame.grid(row=0, column=0, sticky="nsew")

        self.info_text_box.configure(state="normal") # Activer pour insérer du texte
        self.info_text_box.delete("1.0", "end") # Effacer le contenu précédent

        content = ""
        # Logique mise à jour pour le "Plus d'informations"
        # Si le meilleur global est débloqué par l'utilisateur, l'afficher ici comme "Meilleur Agent Débloqué"
        if locked_info["agent"] != "N/A" and locked_info["agent"] in self.unlocked_agents:
            content += f"Meilleur Agent Débloqué: {locked_info['agent']} ({self.agent_roles.get(locked_info['agent'], 'Inconnu')})\n"
            content += f"Raison (Idéal pour cette carte): {locked_info['reason']}\n\n"
            
            # Trouver un autre agent non débloqué pour la section "Meilleur Agent Non Débloqué"
            alternative_locked_agent_name = "N/A"
            # Chercher dans tous les agents, excluant ceux débloqués par l'utilisateur et l'agent idéal global
            for agent in self.all_agents:
                if agent not in self.unlocked_agents and agent != locked_info["agent"]:
                    alternative_locked_agent_name = agent
                    break
            
            if alternative_locked_agent_name != "N/A":
                content += f"Meilleur Agent Non Débloqué: {alternative_locked_agent_name} ({self.agent_roles.get(alternative_locked_agent_name, 'Inconnu')})\n"
                # On peut ajouter une raison générique ou chercher une raison spécifique si disponible
                content += f"Raison: Un agent non débloqué qui est également une bonne option.\n\n"
            else:
                content += f"Meilleur Agent Non Débloqué: Aucun autre agent non débloqué suggéré.\n\n"

        else: # Si le meilleur global n'est pas débloqué par l'utilisateur
            if unlocked_info["agent"] != "N/A":
                content += f"Meilleur Agent Débloqué: {unlocked_info['agent']} ({self.agent_roles.get(unlocked_info['agent'], 'Inconnu')})\n"
                if unlocked_info["agent"] not in self.unlocked_agents:
                    content += f"(Non débloqué par vous. Ce n'est peut-être pas la meilleure option pour VOUS.)\n"
                content += f"Raison: {unlocked_info['reason']}\n\n"

            if locked_info["agent"] != "N/A":
                content += f"Meilleur Agent Non Débloqué: {locked_info['agent']} ({self.agent_roles.get(locked_info['agent'], 'Inconnu')})\n"
                content += f"Raison: {locked_info['reason']}\n\n"

        self.info_text_box.insert("1.0", content)
        self.info_text_box.configure(state="disabled") # Rendre le texte non modifiable


    def show_other_agents_info(self):
        if not self.unlocked_but_not_owned_agent_info and not self.alternative_owned_agent_for_display:
            return

        map_name = self.unlocked_but_not_owned_agent_info["map"] if self.unlocked_but_not_owned_agent_info else self.selected_map
        
        # Masquer le contenu principal et les autres tutoriels
        if self.main_content_frame is not None:
            self.main_content_frame.grid_forget()
        if self.addons_tutorial_frame is not None:
            self.addons_tutorial_frame.grid_forget()
        if self.info_display_frame is not None:
            self.info_display_frame.grid_forget()
        if hasattr(self, 'initial_tutorial_frame') and self.initial_tutorial_frame is not None:
            self.initial_tutorial_frame.grid_forget()
        # Masquer le cadre des boutons d'addons s'il est visible
        if self.addon_buttons_visible:
            self.toggle_addon_buttons_visibility()

        # Afficher le cadre des autres agents
        self.other_agents_display_frame.grid(row=0, column=0, sticky="nsew")

        self.other_agents_text_box.configure(state="normal") # Activer pour insérer du texte
        self.other_agents_text_box.delete("1.0", "end") # Effacer le contenu précédent

        content = ""
        # Afficher l'agent idéal non débloqué (si applicable)
        if self.unlocked_but_not_owned_agent_info:
            agent_info = self.unlocked_but_not_owned_agent_info
            agent_name = agent_info["agent"]
            reason = agent_info["reason"]
            role = self.agent_roles.get(agent_name, 'Inconnu')
            content += f"Agent idéal (non débloqué par vous): {agent_name} ({role})\n"
            content += f"Raison: {reason}\n\n"

        # Afficher l'agent alternatif débloqué (si trouvé)
        if self.alternative_owned_agent_for_display:
            agent_name = self.alternative_owned_agent_for_display
            role = self.agent_roles.get(agent_name, 'Inconnu')
            content += f"Un agent débloqué que vous possédez et qui est une bonne option pour cette carte: {agent_name} ({role})\n"
            content += f"Raison: Cet agent est généralement efficace sur cette carte et fait partie de vos agents débloqués.\n\n"

        self.other_agents_text_box.insert("1.0", content)
        self.other_agents_text_box.configure(state="disabled") # Rendre le texte non modifiable

    def return_to_main_view(self):
        # Masquer tous les cadres d'informations et de tutoriels
        if hasattr(self, 'initial_tutorial_frame') and self.initial_tutorial_frame is not None:
            self.initial_tutorial_frame.grid_forget()
            # Si le tutoriel initial était affiché, créer les widgets principaux maintenant
            if self.main_content_frame is None: # Créer uniquement si pas déjà créé
                self.create_widgets()

        if self.info_display_frame is not None:
            self.info_display_frame.grid_forget()
        if self.other_agents_display_frame is not None:
            self.other_agents_display_frame.grid_forget()
        if self.addons_tutorial_frame is not None:
            self.addons_tutorial_frame.grid_forget()
        
        # Afficher le contenu principal
        if self.main_content_frame is not None:
            self.main_content_frame.grid(row=0, column=0, sticky="nsew")


    def change_text_size(self, new_size_str):
        new_size = int(new_size_str)
        self.current_text_font_size = new_size
        # Mettre à jour la taille de la police pour les zones de texte
        if hasattr(self, 'initial_tutorial_textbox') and self.initial_tutorial_textbox is not None:
            self.initial_tutorial_textbox.configure(font=ctk.CTkFont(size=self.current_text_font_size))
        if hasattr(self, 'info_text_box') and self.info_text_box is not None:
            self.info_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
        if hasattr(self, 'other_agents_text_box') and self.other_agents_text_box is not None:
            self.other_agents_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
        if hasattr(self, 'addons_tutorial_text_box') and self.addons_tutorial_text_box is not None:
            self.addons_tutorial_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
        
        # Si une des fenêtres est ouverte, rafraîchir son contenu pour appliquer le changement
        if hasattr(self, 'info_display_frame') and self.info_display_frame is not None and self.info_display_frame.winfo_ismapped():
            self.show_more_info()
        elif hasattr(self, 'other_agents_display_frame') and self.other_agents_display_frame is not None and self.other_agents_display_frame.winfo_ismapped():
            self.show_other_agents_info()
        elif hasattr(self, 'addons_tutorial_frame') and self.addons_tutorial_frame is not None and self.addons_tutorial_frame.winfo_ismapped():
            # Déterminer quel sous-tutoriel était affiché pour le rafraîchir
            # Ces chaînes sont maintenant hardcodées en français
            if "Comment ajouter un Add-on ?" in self.addons_tutorial_text_box.get("1.0", "1.end"):
                self.show_how_to_add_addon()
            elif "Comment créer un Add-on ?" in self.addons_tutorial_text_box.get("1.0", "1.end"):
                self.show_how_to_create_addon()
            else: # Si aucun sous-tutoriel spécifique n'était affiché, effacer le texte
                self.addons_tutorial_text_box.configure(state="normal")
                self.addons_tutorial_text_box.delete("1.0", "end")
                self.addons_tutorial_text_box.configure(state="disabled")


    def add_addon(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier d'addon JSON et le charge."""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier d'addon JSON",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    addon_content = json.load(f)
                
                # Appliquer les données non-UI en premier
                self.apply_addon_data(addon_content)
                # Puis appliquer les paramètres d'interface utilisateur
                self._apply_addon_ui_settings(addon_content)
                self.save_addons_data() # Sauvegarder les addons chargés
                if self.status_label is not None:
                    self.status_label.configure(text="Add-on chargé avec succès ! Redémarrez l'application.", text_color="green")
            except json.JSONDecodeError:
                if self.status_label is not None:
                    self.status_label.configure(text="Erreur: Le fichier n'est pas un JSON valide.", text_color="red")
            except Exception as e:
                if self.status_label is not None:
                    self.status_label.configure(text=f"Erreur lors du chargement de l'addon: {e}", text_color="red")
            if self.status_label is not None:
                self.after(5000, lambda: self.status_label.configure(text=""))

    def restart_application(self):
        """Simule un redémarrage de l'application."""
        self.destroy() # Détruit la fenêtre actuelle
        # Pour un vrai redémarrage, vous relanceriez le script.
        # Dans cet environnement, la manière la plus simple est de recréer l'instance.
        # Note: Dans un script Python autonome, vous pourriez utiliser os.execv(sys.executable, ['python'] + sys.argv)
        # Mais ici, nous simulerons en recréant l'application.
        global app # Déclarer app comme global pour pouvoir le recréer
        app = ValorantAgentApp()
        app.mainloop()

    def delete_all_addons(self):
        """Supprime le fichier addons_data.json, réinitialise les données des addons
        et les paramètres d'interface utilisateur à leurs valeurs par défaut.
        """
        if os.path.exists("addons_data.json"):
            try:
                os.remove("addons_data.json")
                self.addons_data = {} # Réinitialiser les données d'addons en mémoire
                self.addon_images.clear() # Effacer les images des addons
                if self.addon_images_frame is not None:
                    self.populate_addon_images() # Mettre à jour l'affichage des images (masquera le cadre)

                # Réinitialiser les paramètres d'interface utilisateur à leurs valeurs par défaut
                ctk.set_appearance_mode("System") # Mode système par défaut
                ctk.set_default_color_theme("blue") # Thème de couleur par défaut
                self.current_text_font_size = 14 # Taille de police par défaut
                
                # Mettre à jour la combobox de taille de texte
                if self.font_size_combobox is not None:
                    self.font_size_combobox.set(str(self.current_text_font_size))
                # Réappliquer la taille de police aux zones de texte existantes si elles existent
                if self.initial_tutorial_textbox is not None:
                    self.initial_tutorial_textbox.configure(font=ctk.CTkFont(size=self.current_text_font_size))
                if self.info_text_box is not None:
                    self.info_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
                if self.other_agents_text_box is not None:
                    self.other_agents_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))
                if self.addons_tutorial_text_box is not None:
                    self.addons_tutorial_text_box.configure(font=ctk.CTkFont(size=self.current_text_font_size))


                if self.status_label is not None:
                    self.status_label.configure(text="Tous les add-ons ont été supprimés. Redémarrez l'application.", text_color="green")
                print("addons_data.json supprimé et addons réinitialisés.")
            except Exception as e:
                if self.status_label is not None:
                    self.status_label.configure(text=f"Erreur lors de la suppression des add-ons: {e}", text_color="red")
                print(f"Erreur lors de la suppression des add-ons: {e}")
        else:
            if self.status_label is not None:
                self.status_label.configure(text="Aucun fichier d'add-on à supprimer.", text_color="orange")
            print("Aucun fichier d'add-on à supprimer.")
        
        if self.status_label is not None:
            self.after(5000, lambda: self.status_label.configure(text=""))


    def show_addons_tutorial_view(self):
        """Affiche la vue des tutoriels Add-ons."""
        # Masquer le contenu principal et les autres cadres d'information
        if hasattr(self, 'initial_tutorial_frame') and self.initial_tutorial_frame is not None:
            self.initial_tutorial_frame.grid_forget()
        if self.main_content_frame is not None:
            self.main_content_frame.grid_forget()
        if self.info_display_frame is not None:
            self.info_display_frame.grid_forget()
        if self.other_agents_display_frame is not None:
            self.other_agents_display_frame.grid_forget()
        # Masquer le cadre des boutons d'addons s'il est visible
        if self.addon_buttons_visible:
            self.toggle_addon_buttons_visibility()

        # Afficher le cadre des tutoriels Add-ons
        self.addons_tutorial_frame.grid(row=0, column=0, sticky="nsew")
        # Effacer le contenu précédent du textbox des tutoriels
        self.addons_tutorial_text_box.configure(state="normal")
        self.addons_tutorial_text_box.delete("1.0", "end")
        self.addons_tutorial_text_box.configure(state="disabled")

    def show_how_to_add_addon(self):
        """Affiche le tutoriel pour ajouter un Add-on."""
        tutorial_content = f"""
        **Comment ajouter un Add-on ?**

        Les Add-ons sont des fichiers JSON qui contiennent de nouvelles données pour l'application
        (nouveaux agents, nouvelles cartes, mises à jour de recommandations, etc.).

        Voici les étapes pour ajouter un Add-on :

        1.  **Obtenez le fichier Add-on :** Assurez-vous d'avoir un fichier Add-on au format JSON (.json)
            sur votre ordinateur. Ces fichiers peuvent être créés par vous-même ou partagés par d'autres.

        2.  **Cliquez sur "Ajouter un Add-on" :** Une fois les boutons d'Add-ons affichés (en appuyant sur "!")
            cliquez sur le bouton "Ajouter un Add-on".

        3.  **Sélectionnez le fichier :** Une fenêtre de sélection de fichier s'ouvrira. Naviguez jusqu'à
            l'emplacement de votre fichier .json et sélectionnez-le.

        4.  **Confirmation :** L'application vous indiquera si l'Add-on a été chargé avec succès.

        5.  **Redémarrez l'application :** Pour que les modifications apportées par l'Add-on soient
            entièrement prises en compte, vous devez redémarrer l'application. Cliquez sur le bouton
            "Redémarrer l'application" qui apparaît également avec les autres boutons d'Add-ons.

        Après le redémarrage, les nouvelles données de l'Add-on seront intégrées !
        """
        self.addons_tutorial_text_box.configure(state="normal")
        self.addons_tutorial_text_box.delete("1.0", "end")
        self.addons_tutorial_text_box.insert("1.0", tutorial_content)
        self.addons_tutorial_text_box.configure(state="disabled")

    def show_how_to_create_addon(self):
        """Affiche le tutoriel pour créer un Add-on."""
        json_example_content = """
        {
            "new_agents": {
                "NomAgent1": "RôleAgent1",
                "NomAgent2": "RôleAgent2"
                // ... ajoutez d'autres agents ici
            },
            "new_maps": [
                "NomCarte1",
                "NomCarte2"
                // ... ajoutez d'autres cartes ici
            ],
            "map_recommendations_updates": {
                "NomCarteExistanteOuNouvelle": {
                    "unlocked_best": {
                        "agent": "NomAgentIdealDebloque",
                        "reason": "Raison de la recommandation..."
                    },
                    "locked_best": {
                        "agent": "NomAgentIdealNonDebloque",
                        "reason": "Raison de la recommandation..."
                    },
                    "general_good_agents": [
                        "AgentBon1",
                        "AgentBon2"
                    ]
                },
                "AutreCarte": {
                    // ... autres recommandations pour une autre carte
                }
            },
            "ui_settings": {
                "app_appearance_mode": "Dark", // "System", "Dark", "Light"
                "app_color_theme": "red_theme",    // "blue", "green", "dark-blue", "red_theme", "orange_theme", "yellow_theme", "violet_theme"
                "text_font_size": 16           // Override default font size
            },
            "new_images": [
                {
                    "name": "MonImageCool",
                    "path": "image1.png", // Chemin relatif au dossier 'addon_images'
                    "display_size": [150, 150], // Taille d'affichage (largeur, hauteur)
                    "position": "bottom_right" // Indique où l'image doit être affichée (pour l'instant, toutes vont dans la section "Images d'Add-ons")
                },
                {
                    "name": "GIF Animé (1ère trame seulement)",
                    "path": "animated_gif.gif",
                    "display_size": [100, 100]
                }
            ]
        }
        """
        tutorial_content = f"""
        **Comment créer un Add-on ?**

        Un fichier Add-on est un simple fichier texte au format JSON.
        Vous pouvez le créer avec n'importe quel éditeur de texte (Bloc-notes, VS Code, etc.) et l'enregistrer
        avec l'extension .json (par exemple, `mon_super_addon.json`).

        Voici la structure que votre fichier JSON doit suivre :

        ```json
{json_example_content}
        ```

        **Explications des sections :**

        * `new_agents`: Un objet JSON où chaque clé est le nom d'un nouvel agent et sa valeur est son rôle.
            Exemple : `"Deadlock": "Sentinelle"`

        * `new_maps`: Une liste JSON de noms de nouvelles cartes.
            Exemple : `["District", "Kasbah"]`

        * `map_recommendations_updates`: Un objet JSON où chaque clé est le nom d'une carte
            (existante ou nouvelle) et sa valeur est un objet contenant les recommandations pour cette carte.
            * `unlocked_best`: L'agent idéal si débloqué.
            * `locked_best`: L'agent idéal même si non débloqué.
            * `general_good_agents`: Une liste d'autres agents qui sont de bonnes options pour cette carte.

        * `ui_settings`: Un objet JSON pour personnaliser l'apparence de l'interface.
            * `app_appearance_mode`: Définit le mode d'apparence ("Dark", "Light", "System").
            * `app_color_theme`: Définit le thème de couleur. Vous pouvez utiliser les thèmes intégrés de CustomTkinter ("blue", "green", "dark-blue") ou les nouveaux thèmes personnalisés que l'application supporte maintenant : "red_theme", "orange_theme", "yellow_theme", "violet_theme".
            * `text_font_size`: Définit la taille de police par défaut.

        * `new_images`: Une liste d'objets JSON, où chaque objet représente une image à ajouter.
            * `name`: Un nom unique pour l'image.
            * `path`: Le chemin du fichier image, **relatif au dossier `addon_images`** (qui doit se trouver au même niveau que votre script Python). Par exemple, si votre image est dans `votre_dossier_app/addon_images/mon_image.png`, le chemin sera `"mon_image.png"`.
            * `display_size`: (Optionnel) Un tableau `[largeur, hauteur]` pour spécifier la taille d'affichage de l'image. Par défaut, `[100, 100]`.
            * `position`: (Optionnel) Indique où l'image doit être affichée. Pour l'instant, toutes les images des add-ons seront affichées dans la nouvelle section "Images d'Add-ons" en bas de l'application.
            * **Note sur les GIFs :** Les fichiers GIF sont supportés, mais `CustomTkinter` n'affichera que la **première image (trame)** de l'animation. L'animation complète du GIF ne sera pas visible.

        **Conseils :**
        * Vous n'êtes pas obligé d'inclure toutes les sections dans votre fichier Add-on.
        * Assurez-vous que votre JSON est valide. Des outils en ligne comme "JSONLint" peuvent vous aider à vérifier.
        * Les noms d'agents et de cartes doivent correspondre exactement à ceux que l'application utilise si vous mettez à jour des entrées existantes.
        * **Pour les images :** Créez un dossier nommé `addon_images` à côté de votre fichier Python, et placez-y toutes les images que vous souhaitez charger via les add-ons.
        * **AVERTISSEMENT DE SÉCURITÉ :** N'utilisez des fichiers Add-on que de sources fiables. Un Add-on malveillant pourrait modifier le texte de l'interface pour afficher des informations trompeuses ou rendre l'application difficile à utiliser.


        Une fois votre fichier .json créé, vous pouvez l'ajouter via le bouton "Ajouter un Add-on" !
        """
        self.addons_tutorial_text_box.configure(state="normal")
        self.addons_tutorial_text_box.delete("1.0", "end")
        self.addons_tutorial_text_box.insert("1.0", tutorial_content)
        self.addons_tutorial_text_box.configure(state="disabled")


if __name__ == "__main__":
    app = ValorantAgentApp()
    app.mainloop()
