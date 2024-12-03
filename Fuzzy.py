import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import skfuzzy as fuzz
import skfuzzy.control as ctrl
import numpy as np
import paho.mqtt.client as mqtt

class DroneFuzzyControl:
    def __init__(self, max_speed, FA, Umax):
        self.altitude = 100.0  # Altitude inicial
        self.origin = 100.0  # Altitude inicial de origem
        self.history = [self.altitude]
        self.FA = FA  # Fator de ajuste
        self.Umax = Umax  # Velocidade máxima
        self.max_speed = max_speed
        self.battery = 100.0  # Nível de bateria (em %)
        self.emergency_active = False  # Indica se o modo de emergência está ativo
        self.create_fuzzy_system()
        self.connect_mqtt()

    def create_fuzzy_system(self):
        # Definindo variáveis de entrada e saída
        self.error = ctrl.Antecedent(np.arange(-50, 51, 1), 'error')
        self.delta_error = ctrl.Antecedent(np.arange(-10, 11, 1), 'delta_error')
        self.motor_power = ctrl.Consequent(np.arange(0, 101, 1), 'motor_power')

        # Funções de pertinência
        self.error['negative'] = fuzz.trimf(self.error.universe, [-50, -25, 0])
        self.error['zero'] = fuzz.trimf(self.error.universe, [-5, 0, 5])
        self.error['positive'] = fuzz.trimf(self.error.universe, [0, 25, 50])

        self.delta_error['negative'] = fuzz.trimf(self.delta_error.universe, [-10, -5, 0])
        self.delta_error['zero'] = fuzz.trimf(self.delta_error.universe, [-1, 0, 1])
        self.delta_error['positive'] = fuzz.trimf(self.delta_error.universe, [0, 5, 10])

        self.motor_power['low'] = fuzz.trimf(self.motor_power.universe, [0, 25, 50])
        self.motor_power['medium'] = fuzz.trimf(self.motor_power.universe, [25, 50, 75])
        self.motor_power['high'] = fuzz.trimf(self.motor_power.universe, [50, 75, 100])

        # Base de regras
        rule1 = ctrl.Rule(self.error['negative'] & self.delta_error['negative'], self.motor_power['high'])
        rule2 = ctrl.Rule(self.error['negative'] & self.delta_error['zero'], self.motor_power['medium'])
        rule3 = ctrl.Rule(self.error['negative'] & self.delta_error['positive'], self.motor_power['low'])
        rule4 = ctrl.Rule(self.error['zero'], self.motor_power['medium'])
        rule5 = ctrl.Rule(self.error['positive'] & self.delta_error['negative'], self.motor_power['low'])
        rule6 = ctrl.Rule(self.error['positive'] & self.delta_error['zero'], self.motor_power['medium'])
        rule7 = ctrl.Rule(self.error['positive'] & self.delta_error['positive'], self.motor_power['high'])

        # Sistema de controle
        self.control_system = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7])
        self.control_simulation = ctrl.ControlSystemSimulation(self.control_system)

    def connect_mqtt(self):
        self.mqtt_client = mqtt.Client("DroneController")
        self.mqtt_client.connect("localhost", 1883, 60)  # Conecte-se ao broker MQTT

    def publish_status(self):
        self.mqtt_client.publish("drone/altitude", self.altitude)
        self.mqtt_client.publish("drone/battery", self.battery)

    def fuzzy_control(self):
        error_value = self.altitude - self.origin
        delta_error_value = (self.history[-1] - self.history[-2]) if len(self.history) > 1 else 0

        # Configurando as entradas do sistema fuzzy
        self.control_simulation.input['error'] = error_value
        self.control_simulation.input['delta_error'] = delta_error_value

        # Computando a saída
        self.control_simulation.compute()
        motor_power = self.control_simulation.output['motor_power']

        # Atualizando a altitude
        d_t = motor_power * 0.05  # Ajuste proporcional à potência do motor
        return max(0, self.altitude - d_t)

    def move_to_setpoint(self, setpoint):
        if self.battery <= 0:
            raise Exception("Bateria esgotada! Ative o modo de emergência.")
        if setpoint < 0:
            raise ValueError("Valor negativo! Entre com um valor acima de 0.")

        while self.altitude > setpoint and not self.emergency_active:
            self.altitude = self.fuzzy_control()
            self.altitude = max(self.altitude, setpoint)
            self.history.append(self.altitude)

            # Consome 0.5% de bateria por metro descido
            self.battery -= 0.5 * (self.history[-2] - self.altitude)
            if self.battery <= 0:
                self.battery = 0
                raise Exception("Bateria esgotada durante a descida!")
            self.publish_status()

    def return_to_home(self):
        if self.battery <= 0:
            raise Exception("Bateria esgotada! Ative o modo de emergência.")
        
        while self.altitude < self.origin and not self.emergency_active:
            prev_altitude = self.altitude
            self.altitude += 0.1 * self.Umax * self.FA
            self.altitude = min(self.altitude, self.origin)
            self.history.append(self.altitude)

            # Consome 1% de bateria por metro subido
            self.battery -= (self.altitude - prev_altitude)
            if self.battery <= 0:
                self.battery = 0
                raise Exception("Bateria esgotada durante o retorno!")
            self.publish_status()

    def emergency_landing(self):
        self.emergency_active = True
        while self.altitude > 0:
            self.altitude -= 2.0
            self.altitude = max(self.altitude, 0)
            self.history.append(self.altitude)
            self.publish_status()

class DroneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Fuzzy do Drone")
        self.drone = DroneFuzzyControl(max_speed=3.0, FA=1.0, Umax=3.0)
        self.create_widgets()

    def create_widgets(self):
        title_frame = tk.Frame(self.root)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="Controle Fuzzy do Drone", font=("Arial", 18, "bold")).pack()

        controls_frame = tk.Frame(self.root, relief=tk.GROOVE, borderwidth=2)
        controls_frame.pack(pady=10, padx=10, fill=tk.X)
        tk.Label(controls_frame, text="Defina o SetPoint (m):").pack()
        self.setpoint_entry = tk.Entry(controls_frame)
        self.setpoint_entry.pack(pady=5)

        self.move_button = tk.Button(
            controls_frame, text="Mover para SetPoint",
            command=self.move_to_setpoint, bg="#4CAF50", fg="white", font=("Arial", 12, "bold")
        )
        self.move_button.pack(pady=10)

        self.rth_button = tk.Button(
            controls_frame, text="Return to Home (RtH)",
            command=self.return_to_home, bg="#008CBA", fg="white", font=("Arial", 12, "bold")
        )
        self.rth_button.pack(pady=10)

        self.emergency_button = tk.Button(
            controls_frame, text="Ativar Emergência",
            command=self.activate_emergency, bg="#f44336", fg="white", font=("Arial", 12, "bold")
        )
        self.emergency_button.pack(pady=10)

        status_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        status_frame.pack(pady=10, padx=10, fill=tk.X)
        self.altitude_label = tk.Label(
            status_frame, text=f"Altura Atual: {self.drone.altitude:.2f} m", font=("Arial", 14)
        )
        self.altitude_label.pack(pady=5)

        self.battery_label = tk.Label(
            status_frame, text=f"Bateria: {self.drone.battery:.2f}%", font=("Arial", 14)
        )
        self.battery_label.pack(pady=5)

        self.graph_button = tk.Button(
            self.root, text="Exibir Trajetória", command=self.plot_trajectory, bg="#555555", fg="white",
            font=("Arial", 12, "bold")
        )
        self.graph_button.pack(pady=10)

    def move_to_setpoint(self):
        try:
            setpoint = float(self.setpoint_entry.get())
            if setpoint < 0:
                messagebox.showerror("Erro", "Valor negativo! Entre com um valor acima de 0.")
                return

            self.drone.move_to_setpoint(setpoint)
            self.update_labels()
            messagebox.showinfo("Sucesso", f"SetPoint {setpoint} m alcançado!")
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor numérico válido.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def return_to_home(self):
        try:
            self.drone.return_to_home()
            self.update_labels()
            messagebox.showinfo("Retorno", "Drone retornou à altitude de origem.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def activate_emergency(self):
        self.drone.emergency_landing()
        self.update_labels()
        messagebox.showwarning("Emergência", "Modo de emergência ativado! Recarregue o drone.")
    
    def update_labels(self):
        self.altitude_label.config(text=f"Altura Atual: {self.drone.altitude:.2f} m")
        self.battery_label.config(text=f"Bateria: {self.drone.battery:.2f}%")

    def plot_trajectory(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.drone.history, label="Altura do Drone", marker="o")
        plt.axhline(y=0, color="red", linestyle="--", label="Chão (0 m)")
        plt.axhline(y=self.drone.origin, color="blue", linestyle="--", label="Origem (100 m)")
        plt.xlabel("Iterações")
        plt.ylabel("Altura (m)")
        plt.title("Trajetória do Drone - Controle Fuzzy")
        plt.legend()
        plt.grid()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = DroneApp(root)
    root.mainloop()
