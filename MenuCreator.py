import tkinter as tk
from tkinter import ttk, messagebox
from telegram import Bot
import pandas as pd
import asyncio

# Se configura el bot de Telegram
TOKEN = ''
CHAT_ID = None  # Inicialmente vacío, luego ya se obtendrá al inicio

# Límite diario de nutrientes
LIMITE_NUTRIENTES = {
    'Carbohidratos': 5,
    'Grasas': 2
}

# Ruta del archivo CSV, lista de comidas modificable
ruta_csv = 'comidas.csv'

# Se obtiene el Chat ID de un grupo de Telegram
async def obtener_chat_id_async():
    global CHAT_ID
    bot = Bot(token=TOKEN)
    updates = await bot.get_updates()
    
    for update in updates:
        # Verifica si el mensaje proviene de un grupo o supergrupo de Telegram
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            CHAT_ID = update.message.chat.id
            print("Chat ID del grupo:", CHAT_ID)
            #messagebox.showinfo("Chat ID Obtenido", f"Chat ID del grupo: {CHAT_ID}")
            return
    
    messagebox.showerror("Error", "No se encontro la ID del chat")

# Función para ejecutar la función asincrónica de obtener Chat ID al inicio
def obtener_chat_id():
    asyncio.run(obtener_chat_id_async())

# Leer comidas desde un archivo CSV
def leer_comidas_csv():
    return pd.read_csv(ruta_csv)

# Función para agregar un nuevo alimento al archivo CSV
def agregar_alimento():
    # Crear una nueva ventana
    ventana_agregar = tk.Toplevel(root)
    ventana_agregar.title("Agregar Alimento")

    # Tamaño de la ventana de agregar alimento
    ventana_agregar.geometry("400x300")
    ventana_agregar.resizable(False, False)

    # Campos de entrada para el nombre y valores nutricionales
    tk.Label(ventana_agregar, text="Nombre:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    nombre_var = tk.StringVar()
    tk.Entry(ventana_agregar, textvariable=nombre_var, font=("Arial", 12), width=25).grid(row=0, column=1, padx=10, pady=10)

    tk.Label(ventana_agregar, text="Carbohidratos:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    carb_var = tk.DoubleVar()
    tk.Entry(ventana_agregar, textvariable=carb_var, font=("Arial", 12), width=25).grid(row=1, column=1, padx=10, pady=10)

    tk.Label(ventana_agregar, text="Proteínas:", font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=10, sticky="e")
    prot_var = tk.DoubleVar()
    tk.Entry(ventana_agregar, textvariable=prot_var, font=("Arial", 12), width=25).grid(row=2, column=1, padx=10, pady=10)

    tk.Label(ventana_agregar, text="Grasas:", font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=10, sticky="e")
    grasa_var = tk.DoubleVar()
    tk.Entry(ventana_agregar, textvariable=grasa_var, font=("Arial", 12), width=25).grid(row=3, column=1, padx=10, pady=10)

    # ComboBox para seleccionar el grupo
    tk.Label(ventana_agregar, text="Grupo:", font=("Arial", 12)).grid(row=4, column=0, padx=10, pady=10, sticky="e")
    grupo_var = tk.StringVar()
    combo_grupo = ttk.Combobox(ventana_agregar, textvariable=grupo_var, values=["Desayuno", "Comida", "Cena"], state="readonly", font=("Arial", 12), width=22)
    combo_grupo.grid(row=4, column=1, padx=10, pady=10)
    combo_grupo.set("Comida")  # Valor predeterminado

    # Función para guardar el alimento en el CSV
    def guardar_alimento():
        nuevo_alimento = {
            'Comida': nombre_var.get(),
            'Grupo': grupo_var.get(),  # Obtener el grupo seleccionado
            'Carbohidratos': carb_var.get(),
            'Proteínas': prot_var.get(),
            'Grasas': grasa_var.get()
        }
        
        # Cargar el archivo CSV y agregar la nueva fila usando pd.concat
        df = pd.read_csv(ruta_csv)
        nuevo_df = pd.DataFrame([nuevo_alimento])
        df = pd.concat([df, nuevo_df], ignore_index=True)
        
        # Guardar el DataFrame actualizado de nuevo en el CSV
        df.to_csv(ruta_csv, index=False)
        
        messagebox.showinfo("Alimento Agregado", f"El alimento '{nuevo_alimento['Comida']}' ha sido agregado.")
        ventana_agregar.destroy()

        # Actualizar opciones del combo box con el nuevo alimento
        actualizar_opciones_comidas()

    # Botón para guardar
    tk.Button(ventana_agregar, text="Guardar", command=guardar_alimento, font=("Arial", 12)).grid(row=5, columnspan=2, pady=20)

# Función para actualizar las opciones del ComboBox cuando se agrega un nuevo alimento
def actualizar_opciones_comidas():
    global comidas_opciones, comidas_df
    comidas_df = leer_comidas_csv()
    
    # Actualizar las opciones en cada ComboBox de la interfaz según el grupo
    for dia in dias_semana:
        for tipo_comida in ['Desayuno', 'Comida', 'Cena']:
            # Filtrar las comidas que pertenecen al grupo adecuado
            opciones_filtradas = comidas_df[comidas_df['Grupo'] == tipo_comida]['Comida'].tolist()
            
            combo = root.nametowidget(combo_var[dia][tipo_comida].widget)  # Accede al ComboBox por nombre
            combo['values'] = opciones_filtradas  # Actualiza las opciones del ComboBox con los alimentos del grupo


# Función para calcular los nutrientes totales de un día
def calcular_nutrientes_totales(comidas_dia):
    nutrientes_totales = {'Carbohidratos': 0, 'Grasas': 0}
    for comida, alimentos in comidas_dia.items():
        for alimento in alimentos:
            # Busca el alimento en el DataFrame de comidas
            alimento_info = comidas_df[comidas_df['Comida'] == alimento].iloc[0]
            nutrientes_totales['Carbohidratos'] += alimento_info['Carbohidratos']
            nutrientes_totales['Grasas'] += alimento_info['Grasas']
    return nutrientes_totales

# Función asincrónica para enviar el menú semanal al bot de Telegram con verificación de nutrientes
async def enviar_menu_telegram(token, chat_id, menu):
    bot = Bot(token=token)
    
    mensaje_menu = "Menú semanal:\n\n"
    for dia, comidas in menu.items():
        mensaje_menu += f"{dia}:\n"
        for comida, alimentos in comidas.items():
            mensaje_menu += f"{comida}: {', '.join(alimentos)}\n"
        
        # Calcula nutrientes y verifica si exceden los límites
        nutrientes_totales = calcular_nutrientes_totales(comidas)
        advertencias = []
        
        if nutrientes_totales['Carbohidratos'] > LIMITE_NUTRIENTES['Carbohidratos']:
            advertencias.append("⚠️ Exceso de carbohidratos")
        if nutrientes_totales['Grasas'] > LIMITE_NUTRIENTES['Grasas']:
            advertencias.append("⚠️ Exceso de grasas")
        
        # Agrega advertencias al mensaje del día
        if advertencias:
            mensaje_menu += "\n".join(advertencias) + "\n"
        
        mensaje_menu += "\n"  # Separador de días

    await bot.send_message(chat_id=chat_id, text=mensaje_menu)

# Función para asignar las comidas seleccionadas en la interfaz y enviar el menú
def asignar_comidas_y_enviar():
    if CHAT_ID is None:
        messagebox.showerror("Error", "Primero obtén el Chat ID del grupo.")
        return
    
    menu = {dia: {'Desayuno': [], 'Comida': [], 'Cena': []} for dia in dias_semana}
    
    for dia in dias_semana:
        menu[dia]['Desayuno'] = [combo_var[dia]['Desayuno'].get()]
        menu[dia]['Comida'] = [combo_var[dia]['Comida'].get()]
        menu[dia]['Cena'] = [combo_var[dia]['Cena'].get()]
    
    # Ejecutar la función asincrónica para enviar el menú
    asyncio.run(enviar_menu_telegram(TOKEN, CHAT_ID, menu))
    messagebox.showinfo("Menú Enviado", "El menú semanal ha sido enviado exitosamente al bot de Telegram.")

# Inicializar Tkinter y otros elementos (como los ComboBox y sus opciones)
root = tk.Tk()
root.title("Asignar Comidas Semanales")

# Configuración de la ventana principal
root.geometry("1200x800")
root.resizable(False, False)
root.iconphoto(True, tk.PhotoImage(file="GourmetIA.png")) 
# Centrar la ventana en la pantalla
window_width = 1200
window_height = 800
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

# Obtener el Chat ID al iniciar la aplicación
obtener_chat_id()

# Leer el archivo de comidas y obtener nombres para la selección
comidas_df = leer_comidas_csv()
comidas_opciones = comidas_df['Comida'].tolist()

# Días de la semana
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Variables para almacenar las selecciones de cada combobox y referencia al widget
combo_var = {dia: {'Desayuno': tk.StringVar(), 'Comida': tk.StringVar(), 'Cena': tk.StringVar()} for dia in dias_semana}

# Crear la interfaz gráfica
for idx, dia in enumerate(dias_semana):
    tk.Label(root, text=dia, font=("Arial", 12, "bold")).grid(row=idx, column=0, padx=20, pady=10, sticky="w")
    
    # Crear ComboBox para cada tipo de comida
    for i, tipo_comida in enumerate(['Desayuno', 'Comida', 'Cena']):
        ttk.Label(root, text=tipo_comida, font=("Arial", 12)).grid(row=idx, column=i * 2 + 1, padx=10, pady=10)
        
        # Filtrar las opciones para el grupo de comida adecuado (Desayuno, Comida o Cena)
        opciones_filtradas = comidas_df[comidas_df['Grupo'] == tipo_comida]['Comida'].tolist()
        combo = ttk.Combobox(root, textvariable=combo_var[dia][tipo_comida], values=opciones_filtradas, state="readonly", font=("Arial", 10), width=20)
        combo.grid(row=idx, column=i * 2 + 2, padx=10, pady=10)
        
        # Asignar un nombre único al ComboBox para acceder a él posteriormente
        combo_var[dia][tipo_comida].widget = combo  # Guardar referencia al widget en la variable

# Botón para agregar un nuevo alimento
btn_agregar_alimento = tk.Button(root, text="Agregar Alimento", command=agregar_alimento, font=("Arial", 12), width=20)
btn_agregar_alimento.grid(row=len(dias_semana), column=0, columnspan=2, pady=20)

# Botón para asignar y enviar el menú
btn_enviar = tk.Button(root, text="Asignar y Enviar Menú", command=asignar_comidas_y_enviar, font=("Arial", 12), width=20)
btn_enviar.grid(row=len(dias_semana), column=2, columnspan=5, pady=20)

root.mainloop()