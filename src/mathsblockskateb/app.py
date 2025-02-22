import os
import random
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from os.path import dirname, join
import asyncio

# Importer les modules Android
from android.media import AudioManager, SoundPool

class MathsBlocksKateb(toga.App):
    def get_sound_path(self, filename):
        """Récupère le chemin complet d'un fichier sonore."""
        return join(dirname(__file__), "resources", filename)

    def play_sound(self, sound_id):
        """Joue un son à partir de son ID dans SoundPool."""
        if sound_id is not None:
            self.sound_pool.play(sound_id, 1.0, 1.0, 1, 0, 1.0)

    def generate_grid(self):
        """Génère une grille de 6x5 avec des nombres entre 0 et 20."""
        return [[random.randint(0, 20) for _ in range(5)] for _ in range(6)]

    def generate_target(self):
        """Génère un nombre cible entre 10 et 100."""
        return random.randint(10, 100)

    def generate_operations(self):
        """Génère une ligne d'opérations (+, -, ×, ÷, =)."""
        return ["+", "-", "×", "÷", "="]

    def reset_game(self):
        """Réinitialise le jeu avec une nouvelle grille, un nouveau nombre cible et de nouvelles opérations."""
        self.grid = self.generate_grid()
        self.target = self.generate_target()
        self.operations = self.generate_operations()
        self.current_calculation = []
        self.score = 0
        self.used_numbers = set()
        self.calculations_done = 0
        self.time_remaining = 120  # Temps initial : 120 secondes
        self.update_display()
        self.update_grid_buttons()
        self.start_timer()  # Démarrer le timer

    def update_grid_buttons(self):
        """Met à jour les boutons de la grille avec les nouveaux nombres."""
        if hasattr(self, 'number_buttons'):
            for btn, num in zip(self.number_buttons, [num for row in self.grid for num in row]):
                btn.text = str(num)
                btn.enabled = True

    async def run_timer(self):
        """Gère le timer de manière asynchrone."""
        while self.time_remaining > 0:
            await asyncio.sleep(1)  # Attendre 1 seconde
            self.time_remaining -= 1
            self.time_label.text = f"Temps restant : {self.time_remaining} secondes"
        self.end_game()

    def start_timer(self):
        """Démarre le timer en utilisant asyncio."""
        self.timer_task = asyncio.create_task(self.run_timer())

    def end_game(self):
        """Termine la partie lorsque le temps est écoulé."""
        self.question_label.text = "Temps écoulé ! Partie terminée."
        self.play_sound(self.time_up_sound)
        self.disable_all_buttons()

    def disable_all_buttons(self):
        """Désactive tous les boutons de la grille et des opérations."""
        for btn in self.number_buttons:
            btn.enabled = False
        for btn in self.operation_box.children:
            btn.enabled = False

    def update_display(self):
        """Met à jour l'affichage de la grille, du nombre cible, du calcul en cours et du score."""
        self.target_label.text = f"Nombre cible: {self.target}"
        self.calculation_label.text = "Calcul en cours: " + " ".join(self.current_calculation)
        self.score_label.text = f"Score: {self.score} | Calculs: {self.calculations_done}/10"
        self.time_label.text = f"Temps restant : {self.time_remaining} secondes"

    def on_number_click(self, widget):
        """Gère le clic sur un nombre dans la grille."""
        if len(self.current_calculation) % 2 == 0 and widget.text not in self.used_numbers:
            self.current_calculation.append(widget.text)
            self.used_numbers.add(widget.text)
            widget.enabled = False
            self.update_display()

    def on_operation_click(self, widget):
        """Gère le clic sur une opération."""
        if widget.text == "=":
            self.validate_calculation(widget)
        elif len(self.current_calculation) % 2 == 1:
            self.current_calculation.append(widget.text)
            self.update_display()

    def validate_calculation(self, widget):
        """Valide le calcul en cours et vérifie s'il correspond au nombre cible."""
        try:
            expression = " ".join(self.current_calculation)
            result = eval(expression.replace("×", "*").replace("÷", "/"))
            if result == self.target:
                self.score += 1
                self.calculations_done += 1
                self.question_label.text = "Correct !"
                self.play_sound(self.correct_sound)
            else:
                self.question_label.text = "Incorrect. Essayez encore !"
                self.play_sound(self.wrong_sound)
        except:
            self.question_label.text = "Calcul invalide."

        if self.calculations_done >= 10:
            self.question_label.text = "Félicitations ! Vous avez terminé 10 calculs."
            self.disable_all_buttons()
            return

        # Générer un nouveau nombre cible et une nouvelle grille après chaque essai
        self.target = self.generate_target()
        self.grid = self.generate_grid()
        self.current_calculation = []
        self.used_numbers = set()
        self.update_grid_buttons()
        self.update_display()

    def startup(self):
        """Initialisation de l'application."""
        # Initialiser SoundPool pour les sons
        self.sound_pool = SoundPool(5, AudioManager.STREAM_MUSIC, 0)
        self.correct_sound = self.sound_pool.load(join(dirname(__file__), "resources/correct.mp3"), 1)
        self.wrong_sound = self.sound_pool.load(join(dirname(__file__), "resources/wrong.mp3"), 1)
        self.time_up_sound = self.sound_pool.load(join(dirname(__file__), "resources/time_up.mp3"), 1)

        # Labels pour afficher les informations du jeu
        self.target_label = toga.Label("", style=Pack(padding=5))
        self.calculation_label = toga.Label("", style=Pack(padding=5))
        self.score_label = toga.Label("", style=Pack(padding=5))
        self.time_label = toga.Label("Temps restant : 120 secondes", style=Pack(padding=5))
        self.question_label = toga.Label("", style=Pack(padding=5))

        # Conteneur principal
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=10, alignment="center"))
        self.main_box.add(self.target_label)
        self.main_box.add(self.calculation_label)
        self.main_box.add(self.score_label)
        self.main_box.add(self.time_label)

        # Bouton Start
        self.start_button = toga.Button(
            "Start",
            on_press=lambda widget: self.reset_game(),
            style=Pack(padding=10)
        )
        self.main_box.add(self.start_button)

        # Conteneur pour centrer la grille
        self.grid_container = toga.Box(style=Pack(direction=COLUMN, alignment="center"))

        # Création de la grille de nombres (6 lignes et 5 colonnes)
        self.grid_box = toga.Box(style=Pack(direction=COLUMN, alignment="center"))
        self.number_buttons = []
        for row in self.generate_grid():
            row_box = toga.Box(style=Pack(direction=ROW, alignment="center"))
            for num in row:
                btn = toga.Button(
                    str(num),
                    on_press=self.on_number_click,
                    style=Pack(width=50, height=50, padding=2, flex=1)
                )
                row_box.add(btn)
                self.number_buttons.append(btn)
            self.grid_box.add(row_box)
        self.grid_container.add(self.grid_box)
        self.main_box.add(self.grid_container)

        # Création de la ligne des opérations (+, -, ×, ÷, =)
        self.operation_box = toga.Box(style=Pack(direction=ROW, padding=5, alignment="center"))
        for op in self.generate_operations():
            btn = toga.Button(
                op,
                on_press=self.on_operation_click,
                style=Pack(width=60, height=40, padding=2, flex=1)
            )
            self.operation_box.add(btn)
        self.main_box.add(self.operation_box)

        self.main_box.add(self.question_label)

        self.main_window = toga.MainWindow(title="Maths Blocks Kateb!")
        self.main_window.content = self.main_box
        self.main_window.show()

def main():
    return MathsBlocksKateb()
